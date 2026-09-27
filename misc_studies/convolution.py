import matplotlib.pyplot as plt
import numpy as np


def smooth(arr: np.ndarray, n: int) -> np.ndarray:
    """Apply a moving average, similar to network analyzer smoothing.

    Args:
        arr (np.ndarray): Input array
        n (int): Size of sliding window

    Returns:
        np.ndarray: Smoothed array
    """

    # this doesn't work with a window with an even number of samples
    if n % 2 == 0:
        n += 1

    # make a window to implement a moving average
    window = np.ones(n)

    # do the convolution
    output = np.convolve(arr, window, mode="same") / window.size

    # finish out the smoothing at values past the valid convolution
    output[[0, -1]] = arr[[0, -1]]
    for i in range(1, n // 2):
        span = i * 2 + 1
        output[i] = np.sum(arr[:span]) / (span)
        output[-(i + 1)] = np.sum(arr[-span:]) / (span)

    return output


def test():
    fig, (ax1, ax2) = plt.subplots(2, 1)

    x = np.linspace(0, 1)
    y = np.sin(2 * np.pi * 1 * x) + 3
    yn = y + 0.1 * np.random.standard_normal(x.size)

    ax1.plot(x, y, "-o", label="orig")
    ax2.plot(x, yn, "-o", label="noisy")

    o = smooth(y, 5)
    on = smooth(yn, 5)

    ax1.plot(x, o, "-o", label="out")
    ax2.plot(x, on, "-o", label="noisy out")

    for ax in fig.axes:
        ax.grid()
        ax.legend()

    try:
        plt.show()
    except KeyboardInterrupt:
        plt.close("all")


if __name__ == "__main__":
    test()
