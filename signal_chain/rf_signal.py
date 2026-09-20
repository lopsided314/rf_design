"""Dataclass for an RF signal, separating Signal and Noise."""

from dataclasses import dataclass

from signal_chain.utils import sgc_math


@dataclass(frozen=True)
class RFSignal:
    """Hold the Signal and Noise components of an RF signal."""

    S: float = sgc_math.default_dBm()  # Signal power (W)
    N: float = sgc_math.default_dBm()  # Noise Power Spectral Density (W/Hz)
    BW: float = 1  # Bandwidth (Hz)

    @property
    def SNR(self) -> float:
        """Signal to Noise Ratio."""
        return self.S / (self.N * self.BW)
