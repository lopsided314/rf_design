import matplotlib.pyplot as plt
import numpy as np

# setup the plots
# plt.ion()
fig, (time_ax, freq_ax) = plt.subplots(2, 1)
time_ax.set_title("Time Signal")
time_ax.set_xlabel("Time Sample #")

freq_ax.set_title("FFT Output")
# freq_ax.set_xlabel("FFT Bin #")
freq_ax.set_xlabel("FFT Frequency [Hz]")

#
# Explain ahead of time
#
# The Fourier Transform looks at a signal and decomposes it into its frequency
# components - it looks at a specific frequency and sees if it can match the
# input to that frequency.
#
# 1. Derivation of the e**(1j*x) = cos(x) + 1j*sin(x)
#       - exp(x) = 1 + x + x**2/2! + x**3/3! + ...
#       - cos(x) = 1 - x**2/2! + x**4/4! - x**6/6! + ...
#       - sin(x) = x - x**3/3! + x**5/5! - x**7/7! + ...
#       - j**0 = 1
#       - j**1 = j
#       - j**2 = -1
#       - j**3 = -j
#       - j**4 = 1
#       - exp(1j*x) = 1 + j*x - x**2/2! - j*x**3/3! + x**4/4! + j*x**5/5! + ...
#                   = cos(x) + j*sin(x)
#       - conversly: cos(x) = (exp(j*x) + exp(-j*x))/2
#       -            sin(x) = (exp(j*x) - exp(-j*x))/(2*j)
#       - note that a single-frequency input requires two complex sinusoids,
#         which is what the fourier transform actually deals with
# 2. FFT X-axis - only for even number of samples
#       - bin spacing  = 1/(T*Nfft) = Fs/Nfft
#       - negative frequencies cause fftshift - [0,...,Nfft/2-1,-Nfft/2,...,-1]/(T*Nfft)
# 3. The 0th bin (a0)
#       - 0 Hz is just DC
# 4. The output is complex
#       - this means it has both an amplitude and phase
#


#
# input signal - length 4, let sample period be 1 second
# What is the bin spacing? (1/4 Hz)
#

# 1. all zeros - should see all zeros
# s = np.array([0, 0, 0, 0])

# 2. 1 in the first sample - energy in every bin since there is no repetition
# s = np.array([1, 0, 0, 0])

# 3. -1 in third sample - should see 0, 2, 0, 2 - energy in the +-1/4 Hz bins (1, 3)
# s = np.array([1, 0, -1, 0])

#
# input signal - length 8, sample period 1 second
# What is the bin spacing now? (1/8 Hz)
#

# 1. same pattern, repeated twice - see +-1/4 Hz bins
# s = np.array([1, 0, -1, 0, 1, 0, -1, 0])

# 2. same pattern but faster - see -1/2 Hz bin - this is aliasing! There is no
#    +1/2 Hz bin, so it wraps to the netagive frequencies
# s = np.array([1, -1, 1, -1, 1, -1, 1, -1])

# 3. Some other pattern - it is periodic, period of 2 samples (or
#    1/2 Hz) but with a DC offset - should see 0 Hz and -1/2 Hz bins
s = np.array([1, 0, 1, 0, 1, 0, 1, 0])

#
# Now generate a simple time sampled sine wave
#

# Sample period
T_sample = 10e-3  # 100 Hz

# signal bounds
t_start = 0
t_stop = 1

# time vector
t = np.arange(t_start, t_stop, T_sample)

# generate a recognizable signal - 5.5 Hz sine wave
s = np.sin(2 * np.pi * 5.5 * t)

# generate a recognizable signal - 15 Hz sine wave
# s = np.sin(2 * np.pi * 15 * t)

# generate a proper x-axis
#
# Need to change the xlabel and add f to the plot args
f = np.zeros(s.size)
f[0 : s.size // 2] = np.arange(0, s.size // 2)
f[s.size // 2 :] = np.arange(-s.size // 2, 0)
f = f * 1 / (T_sample * s.size)

# This plot should show 2 peaks - bins have spacing of 1 Hz,
# so should see equal power in bins [5, 6] and [Nfft-6, Nfft-5]

#
# Now generate a more complex signal - pulsed sine wave
#

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

# generate a proper x-axis
f = np.zeros(s.size)
f[0 : s.size // 2] = np.arange(0, s.size // 2)
f[s.size // 2 :] = np.arange(-s.size // 2, 0)
f = f * 1 / (T_sample * s.size)

# Should see 2 sinc functions, centered at +-20 Hz

#
# Repeat last one again with higher sample rate
#

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

# generate a proper x-axis
f = np.zeros(s.size)
f[0 : s.size // 2] = np.arange(0, s.size // 2)
f[s.size // 2 :] = np.arange(-s.size // 2, 0)
f = f * 1 / (T_sample * s.size)

# Should see 2 sinc functions at +- 20 Hz, but with higher definition

#
# Do it with a complex sinusoid
#

# Sample period
T_sample = 1e-3  # 1000 Hz

# signal bounds
t_start = 0
t_stop = 5

# time vector
t = np.arange(t_start, t_stop, T_sample)

# generate a complex sine wave
s = np.exp(1j * 2 * np.pi * 20 * t)

# zero different sections to simulate pulses
s[(1 <= t) & (t < 2)] = 0
s[(3 <= t) & (t < 4)] = 0

# generate a proper x-axis
f = np.zeros(s.size)
f[0 : s.size // 2] = np.arange(0, s.size // 2)
f[s.size // 2 :] = np.arange(-s.size // 2, 0)
f = f * 1 / (T_sample * s.size)

# Should see 1 sinc function at +20 Hz

#
# Try to make an LFM signal
#

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
# generate a proper x-axis
f = np.zeros(s.size)
f[0 : s.size // 2] = np.arange(0, s.size // 2)
f[s.size // 2 :] = np.arange(-s.size // 2, 0)
f = f * 1 / (T_sample * s.size)

# should see power between 20 and 70 Hz

#
# Make the LFM pulsed
#

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

# generate a proper x-axis
f = np.zeros(s.size)
f[0 : s.size // 2] = np.arange(0, s.size // 2)
f[s.size // 2 :] = np.arange(-s.size // 2, 0)
f = f * 1 / (T_sample * s.size)

# should see power between 20 and 70 Hz
#
#
#

# take the fft
S = np.fft.fft(s)
# print(S)

# update the plots
time_ax.stem(s)
# freq_ax.stem(np.abs(S))
freq_ax.stem(f, np.abs(S))

# open the plot windows
plt.tight_layout()
try:
    plt.show()
except KeyboardInterrupt:
    plt.close("all")
