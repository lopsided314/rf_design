"""Analysis tools for RF signal chains.

Perform calculations on a defined signal chain to find its performance parameters
and output.

Typical usage:
    See sgc_example.py for example code.
"""

import copy
from typing import Sequence

from signal_chain import component_chain
from signal_chain import noise_figure
import signal_chain.utils.signal_chain_math as sgc_math
import signal_chain.utils.str_format as sgc_str

import inspect


def analyze_sections(
    *,
    sections: Sequence[component_chain.ComponentChain],
    Pin_dBm: float,
    BW_MHz: float,
    Ni_dBm_Hz: float | None = None,
    Ni_dBm: float | None = None,
    Tin: float | None = None,
    SNR_in: float | None = None,
    filename: str = "",
) -> None:
    """Perform cascade analysis on signal chain sections.

    Given input parameters, run cascade signal chain analysis and output text
    report to file.

    No more than one of [Ni_dBm_Hz, Ni_dBm, Tin, SNR_in] can be provided, which
    will be used as the noise input. The noise spectral density will be
    calculated using the other inputs (Pin, BW) when necessary. No input
    defaults to thermal noise, k*T0.

    Args:
        sections (Sequence[ComponentChain]): Sequence of signal chain sections
        Pin_dBm (float): Input signal power, in dBm
        BW_MHz (float): Bandwidth of signal chain, in MHz
        Ni_dBm_Hz (float): Input Noise Power Spectral Density, in dBm/Hz
        Ni_dBm (float): Input Noise Power, in dBm
        Tin (float): Input Noise temperature, in Kelvin
        filename (str): filename of destination for signal chain analysis
            report. Defaults to stdout.

    Raises:
        ValueError: There are too many noise parameter inputs
    """

    if len([v for v in (Ni_dBm_Hz, Ni_dBm, Tin, SNR_in) if v is not None]) > 1:
        raise ValueError("Cannot have more than 1 input noise value defined")

    # get the function inputs so they can be recorded in the output
    input_args = inspect.getargvalues(inspect.currentframe())[3].items()  # type: ignore
    input_args = {arg: val for arg, val in input_args if val and arg != "sections"}

    reports: list[str] = [f"{input_args = }\n"]

    # input param unit conversion
    Si: float = sgc_math.undBm(Pin_dBm)
    BW: float = BW_MHz * 1e6

    if Ni_dBm_Hz:
        Ni = sgc_math.undBm(Ni_dBm_Hz)
    elif Ni_dBm:
        Ni = sgc_math.undBm(Ni_dBm) / BW
    elif Tin:
        Ni = sgc_math.BOLTZMANN * Tin
    elif SNR_in:
        Ni = sgc_math.undBm(Pin_dBm - SNR_in) / BW
    else:
        # default to thermal noise
        Ni = sgc_math.kT0

    if Ni < sgc_math.kT0:
        reports.append(
            f"WARNING: Requested input requires noise density below thermal: "
            f"{sgc_str.sdBm(Ni)} dBm/Hz\n"
        )

    #
    # calculations
    #
    sections = copy.deepcopy(sections)

    # run calculations for individual stages
    sections[0].set_input(Si, Ni, BW)
    for s_prev, s_next in zip(sections[:-1], sections[1:]):
        s_next.set_input(s_prev.components[-1].So, s_prev.components[-1].No, BW)

    # run calculation for full signal chain
    Gees, Effs = noise_figure.cascade_G_F(sections)

    #
    # generate report
    #
    reports += [section.status() for section in sections]

    reports.append(_generate_inlined_text(sections, Gees, Effs))

    start, end = sections[0], sections[-1]

    if BW_MHz < .001:
        BW_str: str = f"{BW_MHz*1000000:.2f} Hz"
    elif BW_MHz < 1:
        BW_str: str = f"{BW_MHz*1000:.2f} kHz"
    elif BW_MHz > 1000:
        BW_str: str = f"{BW_MHz/1000:.2f} GHz"
    else:
        BW_str: str = f"{BW_MHz:.2f} MHz"

    reports.append("")
    reports.append("System Totals:")
    reports.append(f"  G    = {sgc_str.sdB(Gees[-1])} dB")
    reports.append(f"  NF   = {sgc_str.sdB(Effs[-1])} dB")
    reports.append(f"  Si   = {sgc_str.sdBm(start.Si)} dBm")
    reports.append(f"  So   = {sgc_str.sdBm(end.So)} dBm")
    reports.append(
        f"  Ni   = {sgc_str.sdBm(start.Ni)} dBm/Hz "
        f"({sgc_str.sdBm(start.Ni * BW)} dBm/{BW_str})"
    )
    reports.append(
        f"  No   = {sgc_str.sdBm(end.No)} dBm/Hz "
        f"({sgc_str.sdBm(end.No * BW)} dBm/{BW_str})"
    )
    reports.append(
        f"  SNR_i = {sgc_str.sdB(start.Si/(start.Ni * BW))} dB ({BW_str})"
    )
    reports.append(f"  SNR_o = {sgc_str.sdB(end.So/(end.No * BW))} dB ({BW_str})")

    report = "\n".join(reports) + "\n"

    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
    else:
        print(report)


def _generate_inlined_text(
    sections: Sequence[component_chain.ComponentChain],
    Gees: list[float],
    Effs: list[float],
) -> str:
    """Format signal chain output.

    Align parameters of each stage in order from left to right so the values
    can be read as they are being changed by each stage. (Bad explanation...)

    Args:
        sections (Sequence[ComponentChain]): sequence of signal chain sections.
        Gees (list[float]): Cascaded gain of signal chain.
        Effs (list[float]): Cascaded noise factor of signal chain.

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
    }

    accum_params: dict[str, list[str]] = {
        "G tot": [],
        "NF tot": [],
        "SNR loss": [],
    }

    # figure out the longest parameter name
    width: int = max(
        max(len(param) for param in stage_params),
        max(len(param) for param in accum_params),
    )

    # make each line start with its parameter, padded to the correct length
    stage_params = {s: [s.ljust(width)] for s in stage_params}
    accum_params = {s: [s.ljust(width)] for s in accum_params}

    # more functions to make string formatting shorter
    # right-justified string decibels
    def rsdB(x: float) -> str:
        return sgc_str.sdB(x).rjust(width)

    def rsdBm(x: float) -> str:
        return sgc_str.sdBm(x).rjust(width)

    for section, G, F in zip(sections, Gees, Effs):
        width = max(len(section.desc), len(sgc_str.sdB(1)))

        stage_params["Name"].append(section.desc.rjust(width))
        stage_params["G"].append(rsdB(section.G))
        stage_params["NF"].append(rsdB(section.F))
        # stage_params["Si"].append(lsdBm(section.Si))
        stage_params["So"].append(rsdBm(section.So))
        # stage_params["Ni"].append(lsdBm(section.Ni))
        stage_params["No"].append(rsdBm(section.No))
        # stage_params["SNRi"].append(lsdBm(section.SNR_i))
        # stage_params["SNRo"].append(lsdB(section.SNR_o))
        # stage_params["SNR loss"].append(rsdB(section.SNR_i / section.SNR_o))

        accum_params["G tot"].append(rsdB(G))
        accum_params["NF tot"].append(rsdB(F))
        accum_params["SNR loss"].append(rsdB(sections[0].SNR_i / section.SNR_o))

    lines: list[str] = []
    for param_list in stage_params.values():
        if len(param_list) > 1:
            lines.append("| " + " | ".join(param_list) + " |")

    lines.append("-" * len(lines[-1]))

    for param_list in accum_params.values():
        if len(param_list) > 1:
            lines.append("| " + " | ".join(param_list) + " |")

    return "\n".join(lines)
