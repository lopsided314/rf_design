"""Helper functions to format number printouts."""

import signal_chain.utils.signal_chain_math as sgc_math


def _f72(f: float) -> str:
    """Put float through predefined f-string.

    Args:
        f (float): Number to format.

    Returns:
        str: Formatted number with set precision and fixed width.
    """
    return f"{f:7.2f}"


def sdB(x: float) -> str:
    """Convert x to decibels and format into string.

    Args:
        x (float): Number to format.

    Returns:
        str: Formatted number with set precision and fixed width.
    """
    return _f72(sgc_math.dB(x))


def sdBm(x: float) -> str:
    """Convert x to dBm and format into string.

    Args:
        x (float): Number to format.

    Returns:
        str: Formatted number with set precision and fixed width.
    """
    return _f72(sgc_math.dBm(x))
