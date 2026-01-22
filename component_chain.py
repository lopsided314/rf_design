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

import signal_chain.components as rf_component
from signal_chain import noise_figure

import signal_chain.utils.signal_chain_math as sgc_math
import signal_chain.utils.str_format as sgc_str


class ComponentChain(noise_figure.NoiseFigureStage):
    """Container of RF Components.

    Hold ordered sequence of components and compute their cascaded
    gain and noise factor.

    No values stored in dB.

    Attributes:
        components (list[rf_component.RFComponent]): container of component sequence
        G (float): Total Gain of sequence
        F (float): Total Noise Factor of sequence
        Te (float): effective noise temperate of component sequence
        Si (float): Input signal power (W)
        So (float): Output signal power (W)
        Ni (float): Input noise power spectral density (W/Hz)
        No (float): Output noise power spectral density (W/Hz)
        SNR_i (float): SNR at sequence input
        SNR_o (float): SNR at sequence output

        desc (str): brief description
        warnings (list[str]): warning messages generated during computation
    """

    def __init__(
        self, components: Sequence[rf_component.RFComponent], desc: str
    ) -> None:
        """Create a component chain object.

        Args:
            components (Sequence[RFComponent]): ordered sequence of RF components
            desc (str): brief description of component chain

        Raises:
            ValueError: No components were provided
        """
        super().__init__()
        if len(components) == 0:
            raise ValueError("Cannot have component chain with no components")

        self.components: list[rf_component.RFComponent] = list(
            copy.deepcopy(components)
        )
        self.desc: str = desc

        self._G_accum, self._F_accum = noise_figure.cascade_G_F(self.components)
        self.G, self.F = self._G_accum[-1], self._F_accum[-1]
        self.Te = sgc_math.Te(self.F)

        self.Si: float = sgc_math.DBM_INIT
        self.So: float = sgc_math.DBM_INIT
        self.Ni: float = sgc_math.DBM_INIT
        self.No: float = sgc_math.DBM_INIT
        self.SNR_i: float = sgc_math.DB_INIT
        self.SNR_o: float = sgc_math.DB_INIT

        self.warnings: list[str] = []

    def set_input(self, Si: float, Ni: float, BW: float) -> None:
        """Set the signal and noise inputs to the section and compute its output.

        Args:
            Si (float): Input signal power (W)  
            Ni (float): Input noise power spectral density (W/Hz)
            BW (float): Bandwidth to use for SNR calculation (Hz)
        """

        self.Si = Si
        self.Ni = Ni
        self.SNR_i = Si / (BW * Ni)

        self.components[0].set_input(Si, Ni, BW)
        for c_prev, c_next in zip(self.components[:-1], self.components[1:]):
            c_next.set_input(c_prev.So, c_prev.No, BW)

        self.So = self.components[-1].So
        self.No = self.components[-1].No
        self.SNR_o = self.So / (BW * self.No)

        self.warnings = [c.warning for c in self.components if c.warning]

    def status(self) -> str:
        """Formatted printable string.

        Generate multi-line string that displays properties of the component
        chain as well as the calculated outputs.
        
        Returns:
            str: Printable format of the component chain properties.
        """
        first, last = self.components[0], self.components[-1]
        ret = (f"'{self.desc}' totals:\n"
               f"  G     = {sgc_str.sdB(self.G)} dB\n"
               f"  NF    = {sgc_str.sdB(self.F)} dB\n"
               f"  Si    = {sgc_str.sdBm(first.Si)} dBm\n"
               f"  So    = {sgc_str.sdBm(last.So)} dBm\n"
               f"  Ni    = {sgc_str.sdBm(first.Ni)} dBm/Hz\n"
               f"  No    = {sgc_str.sdBm(last.No)} dBm/Hz\n"
               f"  SNR_i = {sgc_str.sdB(first.SNR_i)} dB\n"
               f"  SNR_o = {sgc_str.sdB(last.SNR_o)} dB\n")
        if self.warnings:
            ret += "\n".join("  Warning: " + w for w in self.warnings) + "\n"
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

    def __init__(self, loss_per_unit_len_dB: float, length: float, desc: str = "") -> None:
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
        super().__init__((rf_component.Loss(self.loss_per_dB * length),), desc)

    def __str__(self) -> str:
        """Printable output.

        Returns:
            str: Printable format of the component chain properties.
        """
        total_loss = f"{sgc_math.dB(self.G):.2f}"
        breakdown = f"({self.length}*{self.loss_per_dB})"
        return f"{total_loss} {breakdown} dB from coax '{self.desc}'\n"
