"""Equivalent model of RF Components.

It is recommended to use the constructor functions when possible, as it
improves clarity and reduces unnecessary typing.

Typical usage example:
    # equivalent
    lna = Amp(10, 2, OP1dB_dBm=13, desc="lna")
    lna = RFComponent(
        gain_dB=10,
        NF_dB=2,
        VSWR=1.5,
        Pin_warn_dBm=(13-10),
        desc="lna"
    )

    # equivalent
    div4 = Loss(7, desc="4-way power divider")
    div4 = RFComponent(
        gain_dB=-7,
        NF_dB=7,
        VSWR=1.6,
        Pin_warn_dBm=999,
        desc="4-way power divider"
    )
"""

from signal_chain import noise_figure
import signal_chain.utils.signal_chain_math as sgc_math


class RFComponent(noise_figure.NoiseFigureStage):
    """Model for an RF Component inside a signal chain.

    Create component with RF parameters and compute the components output
    for a given input.

    No values stored in dB.

    Attributes:
        G (float): Gain of component
        F (float): Noise Factor of component
        VSWR (float): VSWR of component
        desc (str): brief description of component

        Si (float): Input signal power (W)
        So (float): Output signal power (W)
        Si_warn (float): Input power limit (W)
        Ni (float): Input noise power spectral density (W/Hz)
        No (float): Output noise power spectral density (W/Hz)
        SNR_i (float): SNR at component input
        SNR_o (float): SNR at component output
    """

    def __init__(
        self, gain_dB: float, NF_dB: float, VSWR: float, Pin_warn_dBm: float, desc: str
    ) -> None:
        """Create component with RF parameters.

        Args:
            gain_dB (float): power gain, in dB
            NF_dB (float): Noise Figure, in dB
            VSWR (float): VSWR
            Pin_warn_dBm (float): Input power limit, in dBm. A warning message will
                be added to the report summary if this limit is crossed.
            desc (str): brief description of component
        """
        super().__init__()

        self.G: float = sgc_math.undB(gain_dB)
        self.F: float = sgc_math.undB(NF_dB)
        self.VSWR: float = VSWR
        self.desc: str = desc

        self.Si: float = sgc_math.DBM_INIT  # Input signal power (W)
        self.So: float = sgc_math.DBM_INIT  # Output signal power (W)
        self.Si_warn: float = sgc_math.undBm(Pin_warn_dBm)  # Input power limit (W)
        self.Ni: float = sgc_math.DBM_INIT  # Input noise power spectral density (W/Hz)
        self.No: float = sgc_math.DBM_INIT  # Output noise power spectral density (W/Hz)
        self.SNR_i: float = sgc_math.DB_INIT  # SNR at component input
        self.SNR_o: float = sgc_math.DB_INIT  # SNR at component output

        self.warning: str = ""

    def set_input(self, Si: float, Ni: float, BW: float) -> None:
        """Calculate the output of the component given an input.

        Args:
            Si (float): Input signal power (W)
            Ni (float): Input noise power spectral density (W/Hz)
            BW (float): Bandwidth to use for SNR calculation (Hz)
        """

        self.Si = Si
        self.Ni = Ni

        # signal
        self.So = self.Si * self.G

        self.warning = ""
        if self.Si > self.Si_warn:
            # The limit is defined at the input, but for components with
            # positive gain (amps) the P1dB is usually implied to be the OP1dB,
            # so generate the more intuitive warning.
            if self.G > 1:
                output = f"{sgc_math.dBm(self.So):.1f}"
                limit = f"{sgc_math.dBm(self.Si_warn * self.G):.1f}"
                self.warning = f"'{self.desc}' output too high: {output}, {limit}"
            else:
                s_input = f"{sgc_math.dBm(self.Si):.1f}"
                limit = f"{sgc_math.dBm(self.Si_warn):.1f}"
                self.warning = f"'{self.desc}' input too high: {s_input}, {limit}"

        # noise
        self.No = self.G * (self.Ni + sgc_math.BOLTZMANN * sgc_math.Te(self.F))
        self.No = max(self.No, sgc_math.kT0)

        # SNR
        self.SNR_i = Si / (BW * Ni)
        self.SNR_o = self.So / (BW * self.No)


def Amp(
    gain_dB: float,
    NF_dB: float,
    VSWR: float = 1,
    OP1dB_dBm: float = 999,
    desc: str = "",
) -> RFComponent:
    """Construct a component representing typical amplifier parameters.

    Args:
        gain_dB (float): amplifier gain, in dB
        NF_dB (float): amplifier noise figure, in dB
        VSWR (float, optional): VSWR. Defaults to 1.
        OP1dB_dBm (float, optional): Output power at 1 dB compression point.
            Defaults to 999 dBm (never goes into compression).
        desc (str, optional): brief description of component. Defaults to "".

    Returns:
        RFComponent: Generic component with the parameters of the described amplifier.
    """
    return RFComponent(gain_dB, NF_dB, VSWR, OP1dB_dBm - gain_dB, desc)


def Mixer(
    loss_dB: float,
    NF_dB: float,
    VSWR: float = 1,
    IP1dB_dBm: float = 999,
    desc: str = "",
) -> RFComponent:
    """Construct a component representing typical mixer parameters.

    Args:
        loss_dB (float): conversion loss, in dB
        NF_dB (float): mixer noise figure, in dB
        VSWR (float, optional): VSWR. Defaults to 1.
        IP1dB_dBm (float, optional): Input power at 1 dB compression point.
            Defaults to 999 dBm (never goes into compression).
        desc (str, optional): brief description of component. Defaults to "".

    Returns:
        RFComponent: Generic component with the parameters of the described mixer.
    """
    return RFComponent(-loss_dB, NF_dB, VSWR, IP1dB_dBm, desc)


def Loss(
    loss_dB: float, VSWR: float = 1, Pin_warn_dBm: float = 999, desc: str = ""
) -> RFComponent:
    """Construct a component representing generic loss parameters.

    Args:
        loss_dB (float): component power loss, in dB
        VSWR (float, optional): VSWR. Defaults to 1.
        Pin_warn_dBm (float, optional): Input power at which the analyzer will give a warning.
            Defaults to 999 (no power limit)
        desc (str, optional): brief description of component. Defaults to "".

    Returns:
        RFComponent: Generic component with the parameters of the described lossy component.
    """
    return RFComponent(-loss_dB, loss_dB, VSWR, Pin_warn_dBm, desc)


def AttnPad(loss_dB: float) -> RFComponent:
    """Construct a component representing an ideal attenuator pad.

    Args:
        loss_dB (float): component power loss, in dB

    Returns:
        RFComponent: Generic component with the parameters of the described attenuator.
    """
    return RFComponent(-loss_dB, loss_dB, 1, 999, f"{loss_dB:.0f} dB pad")
