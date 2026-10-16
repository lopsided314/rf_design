"""Cascaded Noise figure computation.

Tools to make cascaded noise figure computation simpler.

Typical usage example: # TODO: Update
    stages = [
        NoiseFigureStage(10, 2),
        NoiseFigureStage(0.2, 2),
        NoiseFigureStage(.5, 4),
    ]
    G, F = cascade_G_F(stages)
"""

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass
class NoiseFigureStage:
    """Object used in noise figure calculations.

    Any construct that defines a gain and a noise figure
    can be used as a stage when calculating the gain and
    noise figure of a sequence of such stages.

    Attributes:
        G (float): power gain of represented object (not dB)
        F (float): noise factor of represented object (not dB)
        OIP3 (float): third-order-intercept power (Watts)
    """

    G: float
    F: float
    OIP3: float = math.nan

    def __post_init__(self) -> None:
        """Verify parameters are valid.

        Power gain cannot be negative, and Noise Factor cannot be less than one.

        Args:
            G (float): power gain (not dB).
            F (float): noise factor (not dB).
            OIP3 (float): third-order-intercept power (Watts)

        Raises:
            ValueError: One or more stages have invalid gain or noise factor parameters.
        """

        if self.G < 0 or self.F < 1 or self.OIP3 < 0:
            raise ValueError("Stage has invalid parameters")


def cascade_G_F(
    stages: Sequence[NoiseFigureStage],
) -> tuple[list[float], list[float], list[float]]:
    """Compute the cascaded Gain, Noise Factor, and Output Third Order
    Intercept of ordered stages.

    https://en.wikipedia.org/wiki/Noise_figure#Noise_factor_of_cascaded_devices

    Args:
        stages (Sequence[NoiseFigureStage]): ordered sequence of noise figure stages.

    Raises:
        ValueError: No stages were provided.

    Returns:
        A tuple of 3 lists: cascaded gain G, cascaded noise factor F, and
        cascated OIP3.

        G = [G1,
             G1*G2,
             G1*G2*G3,
             ...
             G1*G2*...*Gn],
        F = [F1,
             F1 + (F2 - 1)/G1,
             F1 + (F2 - 1)/G1 + (F3 - 1)/(G1*G2),
             ...
             F1 + (F2 - 1)/G1 + (F3 - 1)/(G1*G2) + ... + (Fn - 1)/(G1*G2*...*Gn-1)]
        OIP3 = [1 / ( 1 / OIP3_1),
                1 / ( 1 / (OIP3_1 * G2) + 1 / OIP3_2),
                1 / ( 1 / (OIP3_1 * G2 * G3) + 1 / (OIP3_2 * G4) + 1 / OIP3_3),
                ...
            ]
    """

    if len(stages) == 0:
        raise ValueError("Calculations require one or more stages")

    Gees: list[float] = [s.G for s in stages]

    G_accum: list[float] = [math.prod(Gees[: i + 1]) for i in range(len(Gees))]
    F_accum: list[float] = [stages[0].F]
    OIP3_accum: list[float] = [stages[0].OIP3]

    for g, s in zip(G_accum[:-1], stages[1:]):
        F_accum.append(F_accum[-1] + (s.F - 1) / g)
        OIP3_accum.append(1 / (1 / (OIP3_accum[-1] * s.G) + 1 / s.OIP3))

    return G_accum, F_accum, OIP3_accum
