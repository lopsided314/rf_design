import matplotlib.pyplot as plt
import numpy as np


def rect_pulse():
    # define waveform parameters
    T_adc = 1e-9
    tau_p = 10e-6
    tau_pri = 1e-3
    n_pulses = 128

    # How to I make an efficient simulation of a very long cpi?
    #
    # Need true time coherence
    # Need convolution to be limited to only the pulse itself

    # make a time vector
    t_pulse = np.arange(0, tau_p, T_adc)

    # allocate an array to store the start time of the return pulses
    ret_times = np.zeros(n_pulses)


rect_pulse()
try:
    plt.show()
except KeyboardInterrupt:
    plt.close("all")
