"""Model sequences of RF components.

Facilitate calculations on ordered sequence of RF components to
model a section of a signal chain.

Typical usage example:
    section = ComponentChain(
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

from signal_chain import components as sgc_comp
from signal_chain import noise_figure

from signal_chain.utils import signal_chain_math as sgc_math
from signal_chain.utils import str_format as sgc_str


class ComponentChain(noise_figure.NoiseFigureStage):
    """Container of RF Components.

    Hold ordered sequence of components and compute their cascaded
    gain and noise factor.

    No values stored in dB.

    Attributes:
        components (list[sgc_comp.RFComponent]): contains sequence of RF components
        G (float): Total Gain of sequence
        F (float): Total Noise Factor of sequence
        Gees (list[float]): Cumulative Gain of components
        Effs (list[float]): Cumulative Noise Factor of components
        rf_in (sgc_comp.RFSignal): Input RF Signal
        rf_out (sgc_comp.RFSignal): Output RF Signal
        desc (str): brief description
        warnings (list[str]): warning messages generated during computation
    """

    def __init__(self, components: Sequence[sgc_comp.RFComponent], desc: str) -> None:
        """Create a component chain object.

        Args:
            components (Sequence[sgc_comp.RFComponent]): ordered sequence of RF components
            desc (str): brief description of component chain

        Raises:
            ValueError: No components were provided
        """
        if len(components) == 0:
            raise ValueError("Cannot have component chain with no components")

        self.components: list[sgc_comp.RFComponent] = list(copy.deepcopy(components))
        self.desc: str = desc

        self.Gees, self.Effs = noise_figure.cascade_G_F(self.components)
        super().__init__(self.Gees[-1], self.Effs[-1])

        self.rf_in: sgc_comp.RFSignal = sgc_comp.RFSignal()
        self.rf_out: sgc_comp.RFSignal = sgc_comp.RFSignal()

        self.warnings: list[str] = []

    def set_input(self, rf_in: sgc_comp.RFSignal) -> sgc_comp.RFSignal:
        """Set the signal and noise inputs to the section and compute its output.

        Args:
            rf_in (sgc_comp.RFSignal): Input signal

        Returns:
            sgc_comp.RFSignal: The output of this chain when rf_in is the input
        """

        rf_out = rf_in
        for component in self.components:
            rf_out = component.set_input(rf_out)

        self.warnings = [c.warning for c in self.components if c.warning]

        self.rf_in = rf_in
        self.rf_out = rf_out

        return rf_out

    def status(self, BW: float) -> str:
        """Formatted printable string.

        Generate multi-line string that displays properties of the component
        chain as well as the calculated outputs.

        Returns:
            str: Printable format of the component chain properties.
        """
        Si, Ni = self.components[0].rf_in.S, self.components[0].rf_in.N
        So, No = self.components[-1].rf_out.S, self.components[-1].rf_out.N

        ret = (
            f"'{self.desc}' totals:\n"
            f"  G     = {sgc_str.sdB(self.G)} dB\n"
            f"  NF    = {sgc_str.sdB(self.F)} dB\n"
            f"  Si    = {sgc_str.sdBm(Si)} dBm\n"
            f"  So    = {sgc_str.sdBm(So)} dBm\n"
            f"  Ni    = {sgc_str.sdBm(Ni)} dBm/Hz\n"
            f"  No    = {sgc_str.sdBm(No)} dBm/Hz\n"
            f"  SNR_i = {sgc_str.sdB(Si/(Ni*BW))} dB\n"
            f"  SNR_o = {sgc_str.sdB(So/(No*BW))} dB\n"
        )

        if self.warnings:
            ret += "\n".join(f"  Warning: {w}" for w in self.warnings) + "\n"

        return ret


class Coax(ComponentChain):
    """Cable loss as a signal chain section.

    Overload of ComponentChain so cable loss can easily be integrated into
    signal chain model. By treating cable loss as a signal chain section it
    can be used to connect other sections together.

    The length unit is not defined, the user needs to match the loss/length and
    length units themselves.

    Attributes:
        loss_per_dB (float): Loss per unit length of the coax cable, in dB.
        length (float): The length of the cable, in units matching the loss term.
    """

    def __init__(
        self, loss_per_unit_len_dB: float, length: float, desc: str = ""
    ) -> None:
        """Create a coax model object.

        Args:
            loss_per_unit_len_dB (float): loss per unit length of the cable.
            length (float): length of cable, matching length unit to loss term.
            desc (str, optional): brief description of coax.
        """
        self.loss_per_dB: float = loss_per_unit_len_dB
        self.length: float = length
        if not desc:
            desc = "coax"

        super().__init__(
            [sgc_comp.Loss(self.loss_per_dB * length, desc="coax")],
            desc,
        )

    def __str__(self) -> str:
        """Printable output.

        Returns:
            str: Printable format of the component chain properties.
        """
        total_loss = f"{sgc_math.dB(self.G):.2f}"
        breakdown = f"({self.length}*{self.loss_per_dB})"
        return f"{total_loss} {breakdown} dB from coax '{self.desc}'\n"


class GenericChain(ComponentChain):
    """Generic component chain.

    Easy way to add a section with known parameters without having to manually
    make a component chain with a single generic component.

    """

    def __init__(self, gain_dB: float, NF_dB: float, desc: str):
        super().__init__(
            components=(
                sgc_comp.RFComponent(
                    gain_dB=gain_dB,
                    NF_dB=NF_dB,
                    Pin_warn_dBm=999,
                    desc="All",
                ),
            ),
            desc=desc,
        )
