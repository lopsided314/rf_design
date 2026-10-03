import matplotlib.pyplot as plt
import numpy as np

# setup the plots
fig, (time_ax, freq_ax) = plt.subplots(2, 1)
time_ax.set_title("Time Signal")
time_ax.set_xlabel("Time Sample #")

freq_ax.set_title("FFT Output")
freq_ax.set_xlabel("FFT Frequency [Hz]")

#
# The Fourier Transform looks at a signal and decomposes it into its frequency
# components - it looks at a specific frequency and sees if it can match the
# input to that frequency.
#
# A few miscellaneous points:
#
# 1. Derivation of the e**(1j*x) = cos(x) + 1j*sin(x)
#       - exp(x) = 1 + x + x**2/2! + x**3/3! + ...
#       - cos(x) = 1 - x**2/2! + x**4/4! - x**6/6! + ...
#       - sin(x) = x - x**3/3! + x**5/5! - x**7/7! + ...
#       - j**0 = 1, j**1 = j, j**2 = -1, j**3 = -j, j**4 = 1
#       - exp(1j*x) = 1 + j*x - x**2/2! - j*x**3/3! + x**4/4! + j*x**5/5! + ...
#                   = cos(x) + j*sin(x)
#       - conversly: cos(x) = (exp(j*x) + exp(-j*x))/2
#       -            sin(x) = (exp(j*x) - exp(-j*x))/(2*j)
#       - note that a single-frequency input requires two complex sinusoids,
#         which is what the fourier transform actually deals with
# 2. FFT X-axis - See fft_bins function bwlow
# 3. The 0th bin (a0) is 0 Hz - its just the DC offset of the signal - in other
#    words, the average value of the signal over the sample window
# 4. The output is complex
# 5. It is best practice to make the length of the FFT a power of 2. This is
#    because much greater computational efficiency can be achieved since the
#    FFT algorithm implementations can take advantage of this factorization.
#    It isn't strictly necessary for it to be length 2^n. Many of the examples
#    in this module don't have a power of 2 length since I think it is easier
#    to track where the generated result is from by using time constants to
#    derive the input samples.
# 6. Not specifically for the FFT, but DFTs in general: If the input signal
#    has frequency components greater than the Nyquist (1 / (2 * sample period)),
#    those frequency components will show up as images in the wrong
#    frequency bins. Look up 'Nyquist Frequency' for more informatino on this.
#
#    This does not mean that sampling at exactly 2*Nyquist is a good idea,
#    in fact its often a bad idea. 4*Nyquist is a better rule of thumb when
#    choosing a sample rate, although this can be a more complicated subject.
#


#
# Convenience function to generate the FFT output bins
#
def fft_bins(T_sample: float, Nfft: int) -> np.ndarray:
    f = np.zeros(Nfft)

    # The x-values for the FFT output are arranged as follows.
    #
    # [0, ..., Nfft/2 - 1, -Nfft/2, ..., -1] * 1/(T * Nfft)
    #
    # The reasoning behind this arrangement comes from the
    # periodic nature of the regular DFT (Discrete Fourier Transform).
    # Instead of going from -1/(2*T) to 1/(2*T), this is the 1/(2*T) from
    # the base DFT output and the -1/(2*T) from the adjacent mirrored DFT
    # output. Or, at least thats how I think of it, might not be strictly
    # true.
    #
    # These values have important ramifications.
    #
    # 1. More time domain samples = better frequency resolution.
    #    Stated differently, wide in time = narrow in frequency.
    #    The highest frequency bin will always be 1/(2*T) regardless of the
    #    length of the FFT but the number of steps takes to get there increases.
    # 2. Higher sample rate = lower frequency resolution, but higher sample rate
    #    means higher maximum frequency. The spacing of the bins scales directly
    #    with the sample frequency

    f[0 : Nfft // 2] = np.arange(0, Nfft // 2)
    f[Nfft // 2 :] = np.arange(-Nfft // 2, 0)

    # Set the bin spacing  = 1/(T*Nfft) = Fs/Nfft
    f = f * 1 / (T_sample * Nfft)

    return f


#
# Visualize the outputs of very simple signals to understand what the FFT
# is showing you
#
def manual():
    #
    # input signal length 4, let sample period be 1 second
    # What is the bin spacing? (1/4 Hz)
    #

    # 1. all zeros - not a trick question, should see all zeros
    # s = np.array([0, 0, 0, 0])

    # 2. 1 in the first sample - energy in every bin since there is no repetition
    # s = np.array([1, 0, 0, 0])

    # 3. -1 in third sample - should see 0, 2, 0, 2 - energy in the +-1/4 Hz bins (1, 3)
    #    This basically one period of a sinusoid.
    s = np.array([1, 0, -1, 0])

    #
    # input signal length 8, sample period 1 second
    # What is the bin spacing now? (1/8 Hz)
    #

    # 1. same pattern, repeated twice - see +-1/4 Hz bins
    # s = np.array([1, 0, -1, 0, 1, 0, -1, 0])

    # 2. same pattern but faster - see -1/2 Hz bin - this is aliasing! There is no
    #    +1/2 Hz bin, so it wraps to the netagive frequencies
    # s = np.array([1, -1, 1, -1, 1, -1, 1, -1])

    # 3. Some other pattern - it is periodic, period of 2 samples (or
    #    1/2 Hz) but also has a non-zero mean - should see 0 Hz and +-1/2 Hz bins
    # s = np.array([1, 0, 1, 0, 1, 0, 1, 0])

    freq_ax.set_xlabel("FFT Bin #")
    return np.arange(s.size), s


#
# Now generate a simple time sampled sine wave
#
def sine():
    # Sample period
    T_sample = 10e-3  # 100 Hz

    # signal bounds
    t_start = 0
    t_stop = 1

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # generate a recognizable signal - 15 Hz sine wave
    s = np.sin(2 * np.pi * 15 * t)

    # This plot should show 2 peaks - bins have spacing of 1 Hz,
    # so should see equal power in bins 15 and Nfft-15
    return fft_bins(T_sample, s.size), s


#
# Generate a simple sine wave, but not centered on one of the FFT bins
#
def half_bin_sine():

    T_sample = 10e-3  # 1000 Hz

    # signal bounds
    t_start = 0
    t_stop = 1

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # generate a signal with a frequency in between two of the output bins
    s = np.sin(2 * np.pi * 15.5 * t)

    # should see the signal with frequency in the middle of two bins. Notice how
    # tons of energy leaking into many surrounding bins, not just the 2
    # on either side of the 'true' frequency
    return fft_bins(T_sample, s.size), s


#
# Look at the the effects of zero padding the time domain signal
#
def zero_pad():

    T_sample = 10e-3  # 100 Hz

    # signal bounds
    t_start = 0
    t_stop = 1

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # make a signal with multiple frequencies
    s = np.sin(2 * np.pi * 15 * t) + np.sin(2 * np.pi * 17 * t)

    # make a much larger zero buffer and put the signal at the start
    z = np.zeros(2048)
    z[: s.size] = s
    s = z

    # Should see that the peaks are still in the same place, but there are
    # many more fft output samples that make the plot smoother. However, there
    # is not actually more information here - notice how the peaks at the
    # input signal base frequencies are not as sharp.
    return fft_bins(T_sample, s.size), s


#
# Do it with a complex sinusoid
#
def complex_sine():
    # Sample period
    T_sample = 10e-3  # 1000 Hz

    # signal bounds
    t_start = 0
    t_stop = 1

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # generate a complex sine wave
    s = np.exp(1j * 2 * np.pi * 15.5 * t)

    # Should see the same thing as the real signal except the negative image
    # is gone
    return fft_bins(T_sample, s.size), s


#
# Now generate a more complex signal - pulsed sine wave
#
def pulsed_carrier():
    # Sample period
    T_sample = 10e-3  # 100 Hz

    # signal bounds
    t_start = 0
    t_stop = 5

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # generate a sine wave
    s = np.sin(2 * np.pi * 20 * t)

    # zero different sections to simulate pulses
    s[(1 <= t) & (t < 2)] = 0
    s[(3 <= t) & (t < 4)] = 0

    # Should see 2 sinc functions, centered at +-20 Hz
    return fft_bins(T_sample, s.size), s


#
# Repeat last one again with higher sample rate
#
def pulsed_carrier_oversampled():
    # Sample period
    T_sample = 1e-3  # 1000 Hz

    # signal bounds
    t_start = 0
    t_stop = 5

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # generate a sine wave
    s = np.sin(2 * np.pi * 20 * t)

    # zero different sections to simulate pulses
    s[(1 <= t) & (t < 2)] = 0
    s[(3 <= t) & (t < 4)] = 0

    # Should see 2 sinc functions at +- 20 Hz, but with higher definition
    return fft_bins(T_sample, s.size), s


#
# Try to make an LFM signal
#
def LFM():
    # Sample period
    T_sample = 1e-3  # 1000 Hz

    # signal bounds
    t_start = 0
    t_stop = 5

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # generate an LFM signal
    lfm_slope = 10 / 1  # Hz/second
    s = np.exp(1j * 2 * np.pi * (20 * t + lfm_slope / 2 * t**2))

    # should see power between 20 and 70 Hz
    return fft_bins(T_sample, s.size), s


#
# Make the LFM pulsed
#
def pulsed_LFM():
    # Sample period
    T_sample = 1e-3  # 1000 Hz

    # signal bounds
    t_start = 0
    t_stop = 5

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # generate an LFM signal
    lfm_slope = 20 / 1  # Hz/second
    s = np.exp(1j * 2 * np.pi * (20 * t + lfm_slope / 2 * (t % 1) ** 2))

    # zero different sections to simulate pulses
    s[(1 <= t) & (t < 2)] = 0
    s[(3 <= t) & (t < 4)] = 0

    # should see power between 20 and 70 Hz
    return fft_bins(T_sample, s.size), s


#
# Make some white noise
#
def noise():

    # Sample period
    T_sample = 1e-3  # 1000 Hz

    # signal bounds
    t_start = 0
    t_stop = 1

    # time vector
    t = np.arange(t_start, t_stop, T_sample)

    # generate a zero-mean gaussian noise signal
    s = np.random.standard_normal(t.size)

    # Should see random output over the full output span width with, on average,
    # constant power. It is called 'white' noise since it has constant power
    # over all frequencies, similiar to how white light is a combination of all
    # other component wavelengths.
    return fft_bins(T_sample, s.size), s


f, s = noise()

# take the fft
S = np.fft.fft(s)

# update the plots
#
# Since the output of the FFT is complex, take the absolute value to plot
# the total energy in each bin
time_ax.stem(s)
freq_ax.stem(f, np.abs(S))

# open the plot windows
plt.tight_layout()
try:
    plt.show()
except KeyboardInterrupt:
    plt.close("all")
