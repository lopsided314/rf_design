import matplotlib.pyplot as plt
import numpy as np

# setup axes
fig, (ax1, ax2) = plt.subplots(2, 1)

for ax in fig.axes:  # type: ignore
    ax.grid()

# make a signal
x = np.linspace(0, 1)
y = np.sin(2 * np.pi * 3 * x) + 3
y = y + 0.2 * np.random.standard_normal(x.size)

ax1.stem(y)

# make a window to implement a moving average
window = np.ones(4)

# do the convolution
output = np.convolve(y, window, mode="full")
#            a a a a a a a a a a a a a a
#            1 1 1 1

# the only 'valid' output samples are the ones where the signals completely
# overlap - the primary array gets padded with zeros
print(f"{output.size = }")
ax2.stem(output)

try:
    plt.show()
except KeyboardInterrupt:
    plt.close("all")
