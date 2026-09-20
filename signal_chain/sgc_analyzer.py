"""Analysis tools for RF signal chains.

Perform calculations on a defined signal chain to find its performance parameters
and output.

Typical usage:
    See sgc_example.py for example code.
"""

import copy
import inspect
from typing import Callable, Sequence

from signal_chain.rf_chain import RFChain
from signal_chain.rf_component import RFComponent
from signal_chain.rf_signal import RFSignal
from signal_chain import noise_figure
from signal_chain.utils import sgc_math
from signal_chain.utils import sgc_str


def _convert_noise_input(
    Pin_dBm: float,
    BW: float,
    noise_spec: tuple[str, float],
) -> float:
    """Convert different ways to specify input noise to PSD.

    Args:
        Pin_dBm (float): Signal power, in dBm - used for SNR conversions
        BW (float): Bandwidth, in Hz - used to get PSD from absolute power
        noise_spec (tuple[str, float]): Noise format and input value

    Raises:
        ValueError: Invalid noise specifier format.

    Returns:
        float: Noise Power Spectral Density, in W/Hz
    """
    noise_converters: dict[str, Callable[[float], float]] = {
        "Ni W/Hz": lambda ns: ns,
        "Ni dBm/Hz": sgc_math.undBm,
        "Ni dBm": lambda ns: sgc_math.undBm(ns) / BW,
        "Tin": lambda ns: sgc_math.BOLTZMANN * ns,
        "Input SNR dB": lambda ns: (sgc_math.undBm(Pin_dBm - ns) / BW),
    }

    if noise_spec[0] not in noise_converters:
        raise ValueError(
            f"'{noise_spec[0]}' is not a valid input noise format: "
            f"Options are [{list(noise_converters.keys())}]"
        )

    return noise_converters[noise_spec[0]](noise_spec[1])


def _generate_inlined_text(
    sections: Sequence[RFChain | RFComponent],
    G_cas: list[float],
    F_cas: list[float],
) -> str:
    """Format signal chain output.

    Align parameters of each stage in order from left to right so the values
    can be read as they are being changed by each stage. (Bad explanation...)

    Args:
        sections (Sequence[RFChain | RFComponent]): sequence of signal chain parts
        G_cas (list[float]): Cascaded gain of signal chain.
        F_cas (list[float]): Cascaded noise factor of signal chain.

    Returns:
        str: values formatted into printable string.
    """

    stage_params: dict[str, list[str]] = {
        "Name": [],
        "G": [],
        "NF": [],
        "Si": [],
        "So": [],
        "Ni": [],
        "No": [],
        "SNRi": [],
        "SNRo": [],
        "SNR loss": [],
        "Warning": [],
    }

    accum_params: dict[str, list[str]] = {
        "G tot": [],
        "NF tot": [],
        "SNR loss": [],
    }

    # figure out the width of each column
    param_name_width: int = max(
        max(len(param) for param in stage_params),
        max(len(param) for param in accum_params),
    )

    col_widths: list[int] = []

    for section, G, F in zip(sections, G_cas, F_cas):

        col_widths.append(max(len(section.desc), len(sgc_str.sdB(1))))

        stage_params["Name"].append(section.desc)
        stage_params["G"].append(sgc_str.sdB(section.G))
        stage_params["NF"].append(sgc_str.sdB(section.F))
        stage_params["So"].append(sgc_str.sdBm(section.rf_out.S))
        stage_params["No"].append(sgc_str.sdBm(section.rf_out.N))
        stage_params["SNRi"].append(sgc_str.sdB(section.rf_in.SNR))
        stage_params["SNRo"].append(sgc_str.sdB(section.rf_out.SNR))

        if isinstance(section, RFComponent):
            stage_params["Warning"].append(("WARN" if section.warning else ""))

        accum_params["G tot"].append(sgc_str.sdB(G))
        accum_params["NF tot"].append(sgc_str.sdB(F))
        accum_params["SNR loss"].append(
            sgc_str.sdB(sections[0].rf_in.SNR / section.rf_out.SNR)
        )

    report: list[str] = []

    def align_params(params: dict[str, list[str]]) -> list[str]:
        """
        Convert all fields of a parameter dict into aligned rows of text.
        """
        ret: list[str] = []
        for name, param_strs in params.items():
            if any(param_strs):

                param_strs = [f"{s:>{w}}" for w, s in zip(col_widths, param_strs)]

                ret.append(f"| {name:<{param_name_width}} | {' | '.join(param_strs)} |")

        return ret

    report += align_params(stage_params)
    report.insert(0, "-" * len(report[-1]))
    report.append("-" * len(report[-1]))
    report += align_params(accum_params)
    report.append("-" * len(report[-1]))

    return "\n".join(report)


def analyze_sections(
    *,
    sections: Sequence[RFChain],
    Pin_dBm: float,
    BW_MHz: float,
    noise_spec: tuple[str, float],
    filename: str = "",
) -> None:
    """Perform cascade analysis on signal chain sections.

    Given input parameters, run cascade signal chain analysis and output text
    report to file.

    No more than one of [Ni dBm/Hz, Ni dBm, Tin, SNR_in] can be provided, which
    will be used as the noise input. The noise spectral density will be
    calculated using the other inputs (Pin, BW) when necessary. No input
    defaults to thermal noise, k*T0.

    Args:
        sections (Sequence[RFChain]): Sequence of signal chain sections
        Pin_dBm (float): Input signal power, in dBm
        BW_MHz (float): Bandwidth of signal chain, in MHz
        noise_spec (tuple[str, float]): Specify the input noise. Options:
            'Ni dBm/Hz': Input Noise Power Spectral Density, in dBm/Hz
            'Ni dBm': Input Noise Power, in dBm; NPSD computed with Bandwidth
            'Tin': Input Noise temperature, in Kelvin
            'Input SNR dB': Input SNR; NPSD computed with Pin_dBm and Bandwidth
        filename (str): filename of destination for signal chain analysis
            report. Defaults to stdout.

    Raises:
        ValueError: There are too many noise parameter inputs
    """

    # get the function inputs so they can be recorded in the output report
    input_args = inspect.getargvalues(inspect.currentframe())[3]  # type: ignore
    input_args.pop("sections")
    report: list[str] = [f"{input_args = }\n"]

    # input param unit conversion
    BW: float = BW_MHz * 1e6

    # create input signal object
    rf_in: RFSignal = RFSignal(
        S=sgc_math.undBm(Pin_dBm),
        N=_convert_noise_input(Pin_dBm, BW, noise_spec),
        BW=BW,
    )

    if rf_in.N < sgc_math.kT0:
        report.append(
            "WARNING: Requested input requires noise density below thermal: "
            f"{sgc_str.sdBm(rf_in.N)} dBm/Hz\n"
        )

    #
    # calculations
    #
    sections = copy.deepcopy(sections)

    # run calculations for individual stages
    rf_out = rf_in
    for section in sections:
        rf_out = section.set_input(rf_out)

    # run calculation for full signal chain
    G_cas, F_cas = noise_figure.cascade_G_F(sections)

    #
    # generate report
    #
    for section in sections:
        report.append(f"'{section.desc}' Components:")
        report.append(
            _generate_inlined_text(
                section.components,
                section.G_cas,
                section.F_cas,
            )
        )
        report.append("\n" + section.status())

    report.append("All sections:\n" + _generate_inlined_text(sections, G_cas, F_cas))

    if BW >= 1e9:
        BW_str: str = f"{BW/1e9:.2f} GHz"
    elif BW >= 1e6:
        BW_str: str = f"{BW/1e6:.2f} MHz"
    elif BW >= 1e3:
        BW_str: str = f"{BW/1e3:.2f} kHz"
    else:
        BW_str: str = f"{BW:.2f} Hz"

    report.append(
        "\n"
        "System Totals:\n"
        f"G    = {sgc_str.sdB(G_cas[-1])} dB\n"
        f"NF   = {sgc_str.sdB(F_cas[-1])} dB\n"
        f"Si   = {sgc_str.sdBm(rf_in.S)} dBm\n"
        f"So   = {sgc_str.sdBm(rf_out.S)} dBm\n"
        f"Ni   = {sgc_str.sdBm(rf_in.N)} dBm/Hz"
        f" ({sgc_str.sdBm(rf_in.N * rf_in.BW)} dBm/{BW_str})\n"
        f"No   = {sgc_str.sdBm(rf_out.N)} dBm/Hz"
        f" ({sgc_str.sdBm(rf_out.N * rf_out.BW)} dBm/{BW_str})\n"
        f"SNR_i = {sgc_str.sdB(rf_in.SNR)} dB ({BW_str})\n"
        f"SNR_o = {sgc_str.sdB(rf_out.SNR)} dB ({BW_str})\n"
    )

    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
    else:
        print("\n".join(report))
