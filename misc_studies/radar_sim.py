import matplotlib.pyplot as plt
import numpy as np


class Target:
    def __init__(self) -> None:
        self.range = 1000


def rect_pulse():
    # define waveform parameters
    T_adc = 1e-9
    tau_p = 10e-6
    tau_pri = 1e-3
    n_pulses = 128

    tgt = Target()

    # How do I make an efficient simulation of a very long cpi with
    # very large time vectors?
    #
    # Needs:
    #   true phase coherence
    #


rect_pulse()
try:
    plt.show()
except KeyboardInterrupt:
    plt.close("all")
