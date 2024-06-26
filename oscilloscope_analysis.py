import numpy as np
import matplotlib.pylab as plt
import glob
from scipy import signal
import scipy
import os
from scipy.optimize import curve_fit
import matplotlib.ticker as mtick
import sys
import matplotlib


matplotlib.use('TKAgg')

####
folder = r'test_osc'
print(folder)

dir = 'logging' + os.path.sep + folder
files = sorted(glob.glob(dir + '/[0-9]*.csv'))

calibration = np.loadtxt(
    dir + os.path.sep + 'calibration.csv', delimiter=',').T

#####


def lor(x, x0, g):
    return 1/np.pi/(1+((x-x0)/g)**2)


def gau(x, x0, s):
    return 1/np.sqrt(2/np.pi)*np.exp(-1/2*(x-x0)**2/s**2)


def model(x, aL, aG, x0, g, s, C):
    return (aG * gau(x, x0, s) + C + aL * lor(x, x0, g))


######
# plt.plot(*calibration, 'k.', ls='None', label='Calibration')
# plt.legend()
# plt.show()

#####

subfolders = [f.path.split('\\')[-1] for f in os.scandir(dir) if f.is_dir()]
pos_mm = np.array([float(sf.replace('_', '.')) for sf in subfolders])
sig = []

for sf in subfolders:
    subdir = dir + os.path.sep + sf
    files = sorted(glob.glob(subdir + '/[0-9]*.csv'))
    signal = []
    for f in files:
        t, v = np.loadtxt(f, delimiter=',').T
        # cond = v < 0      # If Saturation and ringing
        cond = np.full(len(v), True)
        signal.append(np.sum(np.abs(np.diff(t)[cond[1:]]*v[1:][cond[1:]])))  # "Integration"
    sig.append(np.mean(signal))

sig = np.array(sig) / np.max(sig)   # Normalize
pos_mm, sig = np.array(sorted(zip(pos_mm, sig))).T

left_found = False
right_found = False
normed = sig - np.min(sig)
normed /= np.max(normed)
for i, val in enumerate(normed - 0.5):
    if val > 0 and not left_found:
        left = i
        left_found = True
    if left_found and val < 0 and not right_found:
        right = i
        right_found = True

print(left, right)
print((pos_mm[right] - pos_mm[left])/1e3/2.998e8/1e-15*2)

# plt.plot(pos_mm, sig, 'k.')
# plt.show(block=True)

# # If already compiled into one file
# folder = 'double_peak_zoomed'
# file = 'logging/' + folder + '/summary.csv'
# pos_mm, sig, error = np.loadtxt(file, delimiter=',').T

# Fitting

p0 = [2.5, 11.136,0.04, 0.]

# plt.plot(pos_mm, model(pos_mm, *p0), 'r-')
# plt.plot(pos_mm, sig, 'k.', ls='None', ms=2)
# plt.text(0.1, 0.95, va='top', s=f'Amp. Lor. :{p0[0]}\nAmp. Gau. :{p0[1]}\nCenter:{p0[2]}\
#          \n$\gamma$:{p0[3]}\n$\sigma$:{p0[4]}\nConst.:{p0[5]}', transform=plt.gca().transAxes)
# plt.show()
model = lambda x,A,x0,s,C: A*gau(x,x0,s) + C
fit, err = curve_fit( model, pos_mm, normed, p0=p0,
                     bounds=([.001, p0[1] - .1,  .001, p0[-1] - 0.5],
                             [40, p0[1] + .1,  .07, p0[-1] + 1]))

A, x0, s, C = fit

t_fs = (pos_mm - fit[1])/1e3/2.998e8/1e-15*2

fwhm_factor = 2.355
width = fit[-2]/1e3/3e8 / 1e-15 * 2
e_width = np.sqrt(np.diag(err))[-2]/1e3/3e8 / 1e-15

width_gamma = fit[3]/1e3/3e8 / 1e-15 * 2
e_width_gamma = np.sqrt(np.diag(err))[3]/1e3/3e8 / 1e-15

print(f'{width:.2f} +/- {e_width:.2f}')

# Plotting
# fig = plt.figure()
# gs = fig.add_gridspec(2, 1,  height_ratios=(1, 4),
#                       left=0.1, right=0.9, bottom=0.1, top=0.9,
#                       wspace=0.05, hspace=0)


# ax = fig.add_subplot(gs[1, 0])
# res_ax = fig.add_subplot(gs[0, 0], sharex=ax)

# ax.plot(t_fs, normed, 'k.', ms=4, markevery=1, label='Data')
# ax.plot(t_fs, model(pos_mm, *fit), c='b', lw=1,  label='Fit')
# # ax.plot(t_fs, gau(pos_mm, x0, s)*aG + C, '-.',
# #         c='green', lw=1, alpha=.5,  label='Gaussian')
# # ax.plot(t_fs, lor(pos_mm, x0, g)*aL + C, '--',
# #         c='r', lw=1, alpha=.5,   label='Lorentzian')
# ax.set_xlabel('Delay (fs)')
# # ax.set_ylabel('Signal (arb. unit)')
# # ax.legend(loc='center left')

# # res_ax.plot(t_fs, (sig - model(pos_mm, *fit))/sig * 100, 'b-', lw=1)
# # res_ax.yaxis.set_major_formatter(mtick.PercentFormatter())
# # res_ax.minorticks_on()
# # res_ax.set_ylim(-15, 10)
# # res_ax.set_ylabel('Residuals')
# # # ax.set_xlim(-250, 250)

# ax.axvline(t_fs[left], c='r')
# ax.axvline(t_fs[right], c='r')
# ax.axhline(0.5, c='r')

# plt.setp(res_ax.get_xticklabels(), visible=False)
# fig.tight_layout()

# # text_out = "$\sigma_{\mathrm{auto.}}=$" + f"${width:.2f}\pm{e_width:.2f}$ fs\n" +\
# #     "$\gamma_{\mathrm{auto.}}=$" + \
# #     f"${width_gamma:.2f}\pm{e_width_gamma:.2f}$ fs\n"
# # # "$\mathrm{FWHM}_{\mathrm{source}}=$" + \
# # # f"${width/np.sqrt(2) * fwhm_factor:.0f}\pm{e_width/np.sqrt(2) *fwhm_factor:.0f}$ fs\n" +\

# # ax.text(.05, .95, s=text_out, transform=ax.transAxes, va='top')


# plt.show()

f, ax =  plt.subplots(1,1)
#ax.set_xlim(-200,200)
#ax.set_ylim(0.35,1)
ax.plot(t_fs, normed, 'k.',lw=.5, ms = 3, alpha = .7, zorder= -1, markevery=1, label='Data')
ax.plot(t_fs, model(pos_mm, *fit), c='b', lw=1,  label='Fit')
ax.plot([],[], lw=1, c="b", label=f"FWHM={width*fwhm_factor:.2f} fs")
ax.axvline(t_fs[left], c='r')
ax.axvline(t_fs[right], c='r')
ax.axhline(0.5, c='r', label=f"FWHM={(pos_mm[right] - pos_mm[left])/1e3/2.998e8/1e-15*2:.2f} fs")

np.savetxt("times.txt",t_fs)
np.savetxt("intensities.txt", normed)

ax.set_xlabel("Delay [fs]")
ax.legend()
f.tight_layout()

print('figsaved')
plt.show()

f.savefig("logging//"+folder+"//trace.png")

