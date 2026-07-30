"""Cascaded Noise figure computation.

Tools to make cascaded noise figure computation simpler.

Typical usage example:
    stages = [
        NoiseFigureStage(10, 2),
        NoiseFigureStage(-2, 2),
        NoiseFigureStage(-3, 4),
    ]
    G, F = cascade_G_F(stages)
"""

import math
from typing import Sequence


class NoiseFigureStage:
    """Object used in noise figure calculations.

    Any construct that defines a gain and a noise figure
    can be used as a stage when calculating the gain and
    noise figure of a sequence of such stages.

    Attributes:
        G (float): power gain of represented object (not dB)
        F (float): noise factor of represented object (not dB)
    """

    def __init__(self, G: float = -1, F: float = -1) -> None:
        """Initialize stage properties.

        Args:
            G (float, optional): power gain (not dB). Defaults to uninitialized
            F (float, optional): noise factor (not dB). Defaults to uninitialized
        """
        self.G: float = G
        self.F: float = F

    def valid(self) -> bool:
        """Determine if the stage has valid parameters.

        Returns:
            bool: Power gain cannot be negative and Noise Factor
                  cannot be less than one.
        """
        return self.G > 0 and self.F >= 1


def cascade_G_F(stages: Sequence[NoiseFigureStage]) -> tuple[list[float], list[float]]:
    """Compute the cascaded Gain and Noise Factor of ordered stages.

    https://en.wikipedia.org/wiki/Noise_figure#Noise_factor_of_cascaded_devices

    Args:
        stages (Sequence[NoiseFigureStage]): ordered sequence of noise figure stages.

    Raises:
        ValueError: No stages were provided.
        ValueError: One or more stages have invalid gain or noise factor parameters.

    Returns:
        A tuple of 2 lists, the cascaded gain G and the cascaded noise factor F.
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
    """

    if len(stages) == 0:
        raise ValueError("Calculations require one or more stages")

    if not all(s.valid() for s in stages):
        raise ValueError("Stage has invalid or uninitialized parameters")

    Gees: list[float] = [s.G for s in stages]
    Effs: list[float] = [s.F for s in stages]

    G_accum: list[float] = [math.prod(Gees[: i + 1]) for i in range(len(Gees))]

    F_accum: list[float] = [Effs[0]]

    for g, f in zip(G_accum[:-1], Effs[1:]):
        F_accum.append(F_accum[-1] + (f - 1) / g)

    return G_accum, F_accum
