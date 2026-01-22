""" Helper functions for common operations required by signal chain math.
"""

import math

#
# Physical constants relevant to noise calculations
#

# Default system temperature
T0 = 290  # K

# Boltzmann constant
BOLTZMANN = 1.380649e-23

# Thermal NPSD (-174 dBm/Hz)
kT0 = BOLTZMANN*T0


def dB(x: float) -> float:
    """Turn x into decibels.

    Args:
        x (float): input

    Returns:
        float: 10*log10(x)
    """
    return 10 * math.log10(x)


def dBm(x: float) -> float:
    """Turn x into dBm.

    Assuming x is power in W, normalize to
    milliwatts and convert to decibels.

    Args:
        x (float): Power, in W

    Returns:
        float: 10*log10(x) + 30
    """
    return 10 * math.log10(x) + 30


def undB(x: float) -> float:
    """Undo decibel operation.

    Reverse the arithmetic for converting
    a ratio into decibels.

    Args:
        x (float): Input

    Returns:
        float: 10^(x/10)
    """
    return 10 ** (x / 10)


def undBm(x: float) -> float:
    """Undo decibel operation.

    Assuming x is power in dBm, convert
    back to Watts.

    Args:
        x (float): Power, in dBm

    Returns:
        float: 10^((x-30)/10)
    """
    return 10 ** ((x - 30) / 10)


#
# Initialization values for variables that get converted
# back into dB/dBm when printing. This prevents arithmetic
# errors if inputs haven't been specified while providing
# a clear indication in the report that the values are
# placeholders.
#
DB_INIT = undB(-999.99)
DBM_INIT = undBm(-999.99)


def Te(F: float) -> float:
    """Calculate effective noise temperature from noise factor.
    
    https://en.wikipedia.org/wiki/Noise_temperature

    Args:
        F (float): Noise Factor

    Returns:
        float: Effective noise temperature, in Kelvin
    """
    return T0 * (F - 1)


def mismatch_loss_dB(VSWR: float) -> float:
    """Calculate the insertion power loss due to VSWR.

    An interface with an impedance mismatch will result
    in standing waves due to reflections. This function
    calculates the extra insertion loss caused by the 
    reflections.

    Args:
        VSWR (float): Voltage Standing Wave Ratio

    Returns:
        float: mismatch loss, in dB
    """
    refl_coeff = (VSWR - 1) / (VSWR + 1)
    return dB(1 - refl_coeff**2)

def return_loss_to_VSWR(rl: float) -> float:
    """Calculate the VSWR from the return loss.
    
    Calculate the standing wave ratio from the
    return loss.

    Args:
        rl (float): return loss (S11), in dB

    Returns:
        float: VSWR
    """
    return (1 + 10**(-rl/20)) / (1 - 10**(-rl/20))
