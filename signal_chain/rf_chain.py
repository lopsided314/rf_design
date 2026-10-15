"""Model sequences of RF components.

Facilitate calculations on ordered sequence of RF components to
model a section of a signal chain.

Typical usage example:
    section = RFChain(
        components=[
            Amp(10, 2, "lna"),
            Loss(1, "bpf"),
            Mixer(3, 4, desc="mixer"),
        ],
        desc="example"
    )

    coax = Coax(
        loss_per_unit_len_dB=.3,
        length=20,
        desc="20 ft coax"
    )
"""

import copy
from typing import Sequence

from signal_chain import noise_figure
from signal_chain.rf_component import RFComponent
from signal_chain.rf_signal import RFSignal

from signal_chain.utils import sgc_math, sgc_str


class RFChain(noise_figure.NoiseFigureStage):
    """Container of RF Components.

    Hold ordered sequence of components and compute their cascaded
    gain and noise factor.

    No values stored in dB.

    Attributes:
        components (list[RFComponent]): contains sequence of RF components
        G (float): Total Gain of sequence
        F (float): Total Noise Factor of sequence
        G_cas (list[float]): Cumulative Gain of components
        OIP3_cas (list[float]): Cumulative Third Order Intercept of components
        F_cas (list[float]): Cumulative Noise Factor of components
        rf_in (RFSignal): Input RF Signal
        rf_out (RFSignal): Output RF Signal
        desc (str): brief description
        warnings (list[str]): warning messages generated during computation
    """

    def __init__(self, components: Sequence[RFComponent], desc: str) -> None:
        """Create a component chain object.

        Args:
            components (Sequence[RFComponent]): ordered sequence of RF components
            desc (str): brief description of component chain

        Raises:
            ValueError: No components were provided
        """
        if len(components) == 0:
            raise ValueError("Cannot have component chain with no components")

        self.components: list[RFComponent] = list(copy.deepcopy(components))
        self.desc: str = desc

        self.G_cas, self.F_cas, self.OIP3_cas = noise_figure.cascade_G_F(
            self.components
        )
        super().__init__(
            G=self.G_cas[-1],
            F=self.F_cas[-1],
            OIP3=self.OIP3_cas[-1],
        )

        self.rf_in: RFSignal = RFSignal()
        self.rf_out: RFSignal = RFSignal()

    def set_input(self, rf_in: RFSignal) -> RFSignal:
        """Set the signal and noise inputs to the section and compute its output.

        Args:
            rf_in (RFSignal): Input signal

        Returns:
            RFSignal: The output of this chain when rf_in is the input
        """

        rf_out = rf_in

        for component in self.components:
            rf_out = component.set_input(rf_out)

        self.rf_in = rf_in
        self.rf_out = rf_out

        return rf_out

    def status(self) -> str:
        """Formatted printable string.

        Generate multi-line string that displays properties of the component
        chain as well as the calculated outputs.

        Returns:
            str: Printable format of the component chain properties.
        """

        # Find the Spurious Free Dynamic Range
        SFDR = (self.OIP3 / (self.rf_out.N * self.rf_out.BW)) ** (2 / 3)

        # Find the maximum output power
        S_clip: float = sgc_math.default_dBm()
        for component in self.components:
            S_clip = min(S_clip, component._Si_warn) * component.G

        # Make the printout a little cleaner if there isn't an actual limit
        if S_clip > 1e9:
            S_clip = sgc_math.default_dBm()

        return (
            f"'{self.desc}' totals:\n"
            f"  G     = {sgc_str.sdB(self.G)} dB\n"
            f"  NF    = {sgc_str.sdB(self.F)} dB\n"
            f"  OIP3  = {sgc_str.sdBm(self.OIP3)} dBm\n"
            f"  OP1dB = {sgc_str.sdBm(S_clip)} dBm\n"
            f"  Si    = {sgc_str.sdBm(self.rf_in.S)} dBm\n"
            f"  So    = {sgc_str.sdBm(self.rf_out.S)} dBm\n"
            f"  Ni    = {sgc_str.sdBm(self.rf_in.N)} dBm/Hz\n"
            f"  No    = {sgc_str.sdBm(self.rf_out.N)} dBm/Hz\n"
            f"  SNRi  = {sgc_str.sdB(self.rf_in.SNR)} dB\n"
            f"  SNRo  = {sgc_str.sdB(self.rf_out.SNR)} dB\n"
            f"  SFDR  = {sgc_str.sdB(SFDR)} dB\n"
            f"{'\n'.join(f'  Warning: {c.warning}' for c in self.components if c.warning)}\n"
        )


class Coax(RFChain):
    """Cable loss as a signal chain section.

    Overload of RFChain so cable loss can easily be integrated into
    signal chain model. By treating cable loss as a signal chain section it
    can be used to connect other sections together.

    The length unit is not defined, the user needs to match the loss/length and
    length units themselves. The length_unit field is just for printing.

    Attributes:
        loss_per_dB (float): Loss per unit length of the coax cable, in dB.
        length (float): The length of the cable, in units matching the loss term.
        desc (str, Optional): Description of coax. Default: 'coax'
        length_unit (str, Optional): Length units, only for printing. Default: ''
    """

    def __init__(
        self,
        loss_per_unit_len_dB: float,
        length: float,
        desc: str = "coax",
        unit: str = "",
    ) -> None:
        """Create a coax model object.

        Args:
            loss_per_unit_len_dB (float): loss per unit length of the cable.
            length (float): length of cable, matching length unit to loss term.
            desc (str, optional): brief description of coax.
        """
        self.loss_per_dB: float = loss_per_unit_len_dB
        self.length: float = length
        self.unit: str = unit
        if not desc:
            desc = "coax"

        super().__init__(
            components=[
                RFComponent(
                    gain_dB=-self.loss_per_dB * length,
                    NF_dB=self.loss_per_dB * length,
                    Pin_warn_dBm=999,
                    OIP3_dBm=999,
                    desc="coax",
                )
            ],
            desc=desc,
        )

    def status(self) -> str:
        """Printable output.

        Returns:
            str: Printable format of the coax properties.
        """
        rf_in: RFSignal = self.components[0].rf_in
        rf_out: RFSignal = self.components[-1].rf_out

        ret = (
            f"Coax '{self.desc}' ({self.length}{self.unit} * {self.loss_per_dB} dB) totals:\n"
            f"  Loss  = {sgc_str.sdB(1/self.G)} dB\n"
            f"  Si    = {sgc_str.sdBm(rf_in.S)} dBm\n"
            f"  So    = {sgc_str.sdBm(rf_out.S)} dBm\n"
            f"  Ni    = {sgc_str.sdBm(rf_in.N)} dBm/Hz\n"
            f"  No    = {sgc_str.sdBm(rf_out.N)} dBm/Hz\n"
            f"  SNR_i = {sgc_str.sdB(rf_in.SNR)} dB\n"
            f"  SNR_o = {sgc_str.sdB(rf_out.SNR)} dB\n"
        )

        return ret


class KnownChain(RFChain):
    """Generic component chain.

    Easy way to add a section with known parameters without having to manually
    make a RF chain with a single generic component.

    """

    def __init__(self, gain_dB: float, NF_dB: float, desc: str):
        super().__init__(
            components=(
                RFComponent(
                    gain_dB=gain_dB,
                    NF_dB=NF_dB,
                    Pin_warn_dBm=999,
                    OIP3_dBm=999,
                    desc="All",
                ),
            ),
            desc=desc,
        )
