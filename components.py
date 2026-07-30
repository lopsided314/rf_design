"""Equivalent model of RF Components.

It is recommended to use the constructor functions when possible, as it
improves clarity and reduces unnecessary typing.

Typical usage example:
    # equivalent
    lna = Amp(10, 2, OP1dB_dBm=13, desc="lna")
    lna = RFComponent(
        gain_dB=10,
        NF_dB=2,
        Pin_warn_dBm=(13-10),
        desc="lna"
    )

    # equivalent
    div4 = Loss(7, desc="4-way power divider")
    div4 = RFComponent(
        gain_dB=-7,
        NF_dB=7,
        Pin_warn_dBm=999,
        desc="4-way power divider"
    )
"""

from dataclasses import dataclass

from signal_chain import noise_figure
from signal_chain.utils import signal_chain_math as sgc_math


@dataclass(frozen=True)
class RFSignal:
    """Hold the Signal and Noise components of an RF signal."""

    S: float = sgc_math.DBM_INIT  # Signal power (W)
    N: float = sgc_math.DBM_INIT  # Noise Power Spectral Density (W/Hz)


class RFComponent(noise_figure.NoiseFigureStage):
    """RFComponent base class.

    Attributes:
        G (float): Power gain (not dB)
        F (float): Noise Factor (not dB)
        rf_in (RFSignal): The input RF signal
        rf_out (RFSignal): The output RF signal
        warning (str): Warning string if something undesirable has happened
        desc (str): Description of component.
    """

    def __init__(
        self,
        *,
        gain_dB: float,
        NF_dB: float,
        Pin_warn_dBm: float,
        desc: str,
    ) -> None:
        """Create an RF Component model with common RF component parameters.

        Args:
            gain_dB (float): Power gain, in dB.
            NF_dB (float): Noise Figure, in dB.
            Pin_warn_dBm (float): Input power limit, in dBm.
            desc (str): Description of component.
        """
        super().__init__(
            G=sgc_math.undB(gain_dB),
            F=sgc_math.undB(NF_dB),
        )

        self.rf_in: RFSignal = RFSignal()
        self.rf_out: RFSignal = RFSignal()

        self.warning: str = ""
        self.desc: str = desc

        self._Si_warn: float = sgc_math.undBm(Pin_warn_dBm)  # Input power limit (W)

    def set_input(self, rf_in: RFSignal) -> RFSignal:
        """Calculate the output of the component given an input.

        Args:
            rf_in (RFSignal): Input signal

        Returns:
            RFSignal: The output of this component when rf_in is the input
        """

        # signal
        self.warning = ""
        if rf_in.S > self._Si_warn:
            # The limit is defined at the input, but for components with
            # positive gain (amps) the P1dB is implied to be the OP1dB,
            # so generate the more intuitive warning.
            if self.G > 1:
                output = f"{sgc_math.dBm(rf_in.S * self.G):.1f}"
                limit = f"{sgc_math.dBm(self._Si_warn * self.G):.1f}"
                self.warning = f"'{self.desc}' output too high: {output}, {limit}"
            else:
                s_input = f"{sgc_math.dBm(rf_in.S):.1f}"
                limit = f"{sgc_math.dBm(self._Si_warn):.1f}"
                self.warning = f"'{self.desc}' input too high: {s_input}, {limit}"

        # noise
        No = self.G * (rf_in.N + sgc_math.BOLTZMANN * sgc_math.Te(self.F))
        No = max(No, sgc_math.kT0)

        self.rf_in = rf_in
        self.rf_out = RFSignal(rf_in.S * self.G, No)

        return self.rf_out


def Amp(
    gain_dB: float,
    NF_dB: float,
    OP1dB_dBm: float = 999,
    desc: str = "_Amp",
) -> RFComponent:
    """Construct a component representing typical amplifier parameters.

    Args:
        gain_dB (float): amplifier gain, in dB
        NF_dB (float): amplifier noise figure, in dB
        OP1dB_dBm (float, optional): Output power at 1 dB compression point.
            Defaults to 999 (never goes into compression).
        desc (str, optional): brief description of component. Defaults to "_Amp".

    Returns:
        RFComponent: Generic component with the parameters of the described amplifier.
    """
    return RFComponent(
        gain_dB=gain_dB,
        NF_dB=NF_dB,
        Pin_warn_dBm=OP1dB_dBm - gain_dB,
        desc=desc,
    )


def Mixer(
    loss_dB: float,
    NF_dB: float,
    IP1dB_dBm: float = 999,
    desc: str = "_Mixer",
) -> RFComponent:
    """Construct a component representing typical mixer parameters.

    Args:
        loss_dB (float): conversion loss, in dB
        NF_dB (float): mixer noise figure, in dB
        IP1dB_dBm (float, optional): Input power at 1 dB compression point.
            Defaults to 999 dBm (never goes into compression).
        desc (str, optional): brief description of component. Defaults to "_Mixer".

    Returns:
        RFComponent: Generic component with the parameters of the described mixer.
    """
    return RFComponent(
        gain_dB=-loss_dB,
        NF_dB=NF_dB,
        Pin_warn_dBm=IP1dB_dBm,
        desc=desc,
    )


def Loss(
    loss_dB: float,
    Pin_warn_dBm: float = 999,
    desc: str = "_Loss",
) -> RFComponent:
    """Construct a component representing generic loss parameters.

    Catchall for combiners, isolators, attenuators, etc. Anything that has a
    noise figure equal to its loss.

    Args:
        loss_dB (float): component power loss, in dB
        Pin_warn_dBm (float, optional): Input power at which the analyzer will give a warning.
            Defaults to 999 (no power limit)
        desc (str, optional): brief description of component. Defaults to "_Loss".

    Returns:
        RFComponent: Generic component with the parameters of the described lossy component.
    """
    return RFComponent(
        gain_dB=-loss_dB,
        NF_dB=loss_dB,
        Pin_warn_dBm=Pin_warn_dBm,
        desc=desc,
    )
