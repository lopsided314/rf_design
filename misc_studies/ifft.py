import matplotlib.pyplot as plt
import numpy as np

# setup the plots
fig, (freq_ax, time_ax) = plt.subplots(2, 1)
freq_ax.set_title("FFT Spectrum")
freq_ax.set_xlabel("FFT Frequency [Hz]")

time_ax.set_title("IFFT Output")
time_ax.set_xlabel("IFFT Time [s]")

#
# Notes
#
# The Numpy ifft function expects the spectrum to be in the same format as the
# unshifted output of the FFT, i.e. [0, ..., Nfft/2 - 1, -Nfft/2, ..., -1]
#
#


def ifft_bins(f_bin, Nfft):
    #
    # To get back the time samples, all we need to do is figure out the sample
    # period based on the bin spacing and make a time vector of samples
    # starting from t = 0
    #
    # Reverse of: f_bin = 1/(T * Nfft)
    #
    T_sample = 1 / (f_bin * Nfft)

    return np.arange(0, Nfft) * T_sample


def manual():
    # frequencies for T_sample = 1, 4 samples
    f = np.array([0, 1, -2, -1]) / 4

    # Purely DC offset
    # S = np.array([1, 0, 0, 0])

    # .25 Hz sine wave - complex
    # S = np.array([0, 1, 0, 0])

    # .25 Hz sine wave - real
    # To get the real time signal out, need to include both the positive and
    # negative frequencies
    # S = np.array([0, 1, 0, 1])

    # frequencies for T_sample = .1, 32 samples
    f = np.fft.fftfreq(n=32, d=0.1)

    # make some spectrum to get a real time domain signal
    S = np.zeros(f.size)
    S[10] = 1
    S[13] = 1
    S[-13] = 1
    S[-10] = 1

    return f, S


f, S = manual()

# take the ifft
t = ifft_bins(f_bin=(f[1] - f[0]), Nfft=f.size)
s = np.fft.ifft(S)

# update the plots
#
# Since the output of the inverse FFT is complex, plot the real and imaginary
# components separately.
freq_ax.stem(f, np.abs(S))
time_ax.stem(t, s.real, linefmt="r", label="Real")
time_ax.stem(t, s.imag, linefmt="g", label="Imag")

# open the plot windows
plt.tight_layout()
plt.legend()

try:
    plt.show()
except KeyboardInterrupt:
    plt.close("all")
