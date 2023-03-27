import numpy as np
import matplotlib.pylab as plt
import glob
from scipy import signal
import scipy
import os
from scipy.optimize import curve_fit
import matplotlib.ticker as mtick
import sys


def lor(x, x0, g):
    return 1/np.pi/g/(1+((x-x0)/g)**2)


def gau(x, x0, s):
    return 1/np.sqrt(2/np.pi)/s*np.exp(-1/2*(x-x0)**2/s**2)


def model(x, aL, aG, x0, g, s, C):
    return aG/1000 * gau(x, x0, s) + C + aL/1000 * lor(x, x0, g)


# dir = 'logging' + os.path.sep + 'spitfire_osc_wide_window'
# files = sorted(glob.glob(dir + '/[0-9]*.csv'))

# calibration = np.loadtxt(
#     dir + os.path.sep + 'calibration.csv', delimiter=',').T

# plt.plot(*calibration, 'k.', ls='None', label='Calibration')
# plt.legend()
# plt.show()

# # Here, its whether the max V or average
# pos_mm = np.array([float(os.path.basename(f).replace(
#     '.csv', '').replace('_', '.')) for f in files])
# sig = []

# for f in files:
#     t, v = np.loadtxt(f, delimiter=',').T
#     sig.append(np.sum(v)/len(v))
#     # sig.append(np.max(v))
# sig = np.array(sig)


#### If already compiled into one file
file = ''
pos_mm, sig= np.loadtxt(file, delimiter=',').T

p0 = [1.5, .2, 11.655, .006, .008, .158]

plt.plot(pos_mm, model(pos_mm, *p0), 'r-')
plt.plot(pos_mm, sig, 'k.', ls='None', ms=2)
plt.text(0.1, 0.95, va='top', s=f'Amp. Lor. :{p0[0]}\nAmp. Gau. :{p0[1]}\nCenter:{p0[2]}\
         \n$\gamma$:{p0[3]}\n$\sigma$:{p0[4]}\nConst.:{p0[5]}', transform=plt.gca().transAxes)
plt.show()

if len(sys.argv) > 1:
    fit, err = curve_fit(model, pos_mm, sig, p0=p0,
                         bounds=([.01, 0.01, p0[2] - .1, .001, .001, p0[-1] - .4],
                                 [3, 10, p0[2] + .1, .01, .05, p0[-1] + .4]))

    aL, aG, x0, g, s, C = fit

    t_fs = (pos_mm - fit[2])/1e3/2.998e8/1e-15*2

    fwhm_factor = 2.355
    width = fit[-2]/1e3/3e8 / 1e-15 * 2
    e_width = np.sqrt(np.diag(err))[-2]/1e3/3e8 / 1e-15
    print(f'{width:.0f} +/- {e_width:.0f}')
    # Plotting
    fig = plt.figure()
    gs = fig.add_gridspec(2, 1,  height_ratios=(1, 4),
                          left=0.1, right=0.9, bottom=0.1, top=0.9,
                          wspace=0.05, hspace=0.05)

    res_ax = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[1, 0])

    ax.plot(t_fs, sig, 'k.', ms=1.5, markevery=1, label='Data')
    ax.plot(t_fs, model(pos_mm, *fit), c='b', lw=1,  label='Fit')
    ax.plot(t_fs, gau(pos_mm, x0, s)*aG/1000 + C, '-.',
            c='green', lw=1, alpha=.5,  label='Gaussian')
    ax.plot(t_fs, lor(pos_mm, x0, g)*aL/1000 + C, '--',
            c='r', lw=1, alpha=.5,   label='Lorentzian')
    ax.set_xlabel('Delay (fs)')
    ax.set_ylabel('Signal (arb. unit)')
    ax.legend(loc=0)

    res_ax.plot(t_fs, (sig - model(pos_mm, *fit))/sig * 100, 'b-', lw=1)
    res_ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    res_ax.minorticks_on()
    res_ax.set_ylim(-15, 10)
    res_ax.set_ylabel('Residuals')

    text_out = "$\sigma_{\mathrm{auto.}}=$" + f"${width:.0f}\pm{e_width:.0f}$ fs\n" +\
        "$\mathrm{FWHM}_{\mathrm{source}}=$" + \
        f"${width/np.sqrt(2) * fwhm_factor:.0f}\pm{e_width/np.sqrt(2) *fwhm_factor:.0f}$ fs\n"

    ax.text(.05, .95, s=text_out, transform=ax.transAxes, va='top')

    fig.savefig(r'./figures/autocorrelation_new.pdf',
                format='pdf', bbox_inches='tight')
    fig.show()