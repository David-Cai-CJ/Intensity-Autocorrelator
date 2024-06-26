from moku.instruments import Oscilloscope
from uedinst.delay_stage import XPSController
import os
import numpy as np
import socket
import tqdm
import matplotlib
import csv
import matplotlib.pylab as plt

matplotlib.use('TKAgg')

moku_address = '[fe80:0000:0000:0000:7269:79ff:feb9:1a40%9]'

# If it says API already connected, close it from fd in the WARNING message. (Probably better ways...)

# socket.socket().close(404)
# socket.socket().close(1192)


osc = Oscilloscope(moku_address, force_connect=True)
osc.set_source(2, source='Input2')
osc.set_acquisition_mode(mode='Precision')
osc.set_hysteresis("Absolute", 0.03)
osc.set_trigger(auto_sensitivity=False, hf_reject=False,
                noise_reject=False, mode='Single', level=0.09, source='Input2')
osc.set_timebase(-.6e-6, 1.e-6)
# https://apis.liquidinstruments.com/reference/oscilloscope/
xps = XPSController(reset=False)

stage = xps.autocorr_stage

# hardware limits
min_move = stage.min_limit
max_move = stage.max_limit


# signal limits for ~100fs pulse
PEAK_POS_MM = 11.6550

# RANGE_PS = .5
# RANGE_MM = abs(stage.delay_to_distance(RANGE_PS))

# First set -- try to resolve the fringes in the middle
# RANGE_MM = 0.025
# STEP_SIZE_MM = 1e-4  # 100 nm
# 0.03 mm per 100 fs


# # Second set -- long scan period
RANGE_MM = 0.04
STEP_SIZE_MM = 5e-4


MAX_POS_MM = round(PEAK_POS_MM + RANGE_MM, 4)
MIN_POS_MM = round(PEAK_POS_MM - RANGE_MM, 4)


###

stage.absolute_move(10)
print(f"Stage moved to {stage.current_position()}")

folder = r'post_oscillator_adjust'
n_samples = 1


try:
    os.makedirs(os.path.sep.join(['logging', folder]))
except FileExistsError:
    pass


########
measurement = osc.get_data()
calibration_data = np.array([measurement['time'], measurement['ch2']]).T

np.savetxt(r'./logging' + os.sep + folder + os.path.sep + 'calibration'
           '.csv', calibration_data, delimiter=',')

print("Start Scanning\n\n")

pos = np.round(np.arange(MIN_POS_MM, MAX_POS_MM +
               STEP_SIZE_MM, STEP_SIZE_MM), 4)


fig, (ax, ax2) = plt.subplots(2, 1)

v_data = []
e_v_data = []

for loc in tqdm.tqdm(pos):
    stage.absolute_move(loc)
    prefix = f"{stage.current_position():.4f}".replace(".", "_")

    Vmax = []
    step_folder = r'./logging'+os.path.sep + folder + \
        os.path.sep + rf'{loc}'.replace('.', '_')

    try:
        os.makedirs(step_folder)
    except FileExistsError:
        pass

    for n in np.arange(n_samples):
        # Current proportional to Voltage. Take max Vout
        measurement = osc.get_data()
        data = np.array([measurement['time'], measurement['ch2']]).T
        np.savetxt(step_folder+os.path.sep +
                   f'{n}' + '.csv', data, delimiter=',')
        Vmax.append(np.sum(measurement['ch2']))
        ax.plot(measurement['time'], measurement['ch2'])

    ax.clear()
    ax2.clear()

    v_data.append(np.mean(Vmax))
    e_v_data.append(np.std(Vmax))

    ax.errorbar(np.array(pos[:len(v_data)]), np.array(v_data), yerr=e_v_data)

    with open(r'./logging' + os.path.sep + folder + os.path.sep +
              'summary.csv', 'a+', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([loc, np.mean(Vmax), np.std(Vmax)])
    plt.pause(.1)

plt.show(block=True)


osc.relinquish_ownership()
