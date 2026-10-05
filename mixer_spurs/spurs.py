"""RF Mixer Spur Estimation and Visualization.

The goal of this script is to allow visualization of mixer spurs through
a double-balanced RF mixer. It was inspired by the online calculator tool
from Marki Microwave. 

Reference: https://markimicrowave.com/technical-resources/tools/spur-calculator/

"""

import itertools
import sys
import warnings

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import mplcursors
import numpy as np

"""Constants taken from the Henderson paper."""
HENDERSON = np.array(
    [
        [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        [np.nan, 0, -41, -28, np.nan, np.nan],
        [np.nan, -35, -39, -44, np.nan, np.nan],
        [np.nan, -10, -32, -18, np.nan, np.nan],
        [np.nan, -35, -39, np.nan, np.nan, np.nan],
        [np.nan, -14, np.nan, -14, np.nan, np.nan],
    ]
)

"""Constants taken from the Marki Microwave online spur calculator.

'L', 'M', 'N', and 'H' represent LO drive levels, specific to their own product
line - they make a MM1-0320LS and a MM1-0320HS

L = +10 dBm
M = +13 dBm
N = +16 dBm
H = +19 dBm

Arrays are indexed [LO_order, IF_order].

"""

MARKI_TABLES: dict[str, np.ndarray] = {
    "L": np.array(
        [
            [-8.0, -26.0, -39.0, -45.0, -68.0, -59.0],
            [-8.0, 0.0, -33.0, -28.0, -51.0, -57.0],
            [-8.0, -26.0, -39.0, -35.0, -58.0, -55.0],
            [-8.0, -10.0, -23.0, -18.0, -37.0, -43.0],
            [np.nan, -26.0, -39.0, -21.0, -44.0, -38.0],
            [np.nan, -14.0, -19.0, -14.0, -20.0, -26.0],
        ]
    ),
    "M": np.array(
        [
            [-5.0, -26.0, -39.0, -44.0, -68.0, -59.0],
            [-5.0, 0.0, -32.0, -28.0, -50.0, -57.0],
            [-5.0, -26.0, -39.0, -35.0, -58.0, -54.0],
            [-5.0, -10.0, -23.0, -18.0, -36.0, -43.0],
            [-5.0, -26.0, -39.0, -21.0, -44.0, -37.0],
            [-5.0, -14.0, -18.0, -14.0, -19.0, -26.0],
        ]
    ),
    "N": np.array(
        [
            [-2.0, -27.0, -39.0, -46.0, -68.0, -60.0],
            [-2.0, 0.0, -34.0, -28.0, -52.0, -57.0],
            [-2.0, -27.0, -39.0, -36.0, -58.0, -56.0],
            [-2.0, -10.0, -24.0, -18.0, -38.0, -43.0],
            [-2.0, -27.0, -39.0, -22.0, -44.0, -39.0],
            [-2.0, -14.0, -20.0, -14.0, -21.0, -26.0],
        ]
    ),
    "H": np.array(
        [
            [0.0, -26.0, -39.0, -44.0, -68.0, -58.0],
            [0.0, 0.0, -32.0, -28.0, -50.0, -57.0],
            [0.0, -26.0, -39.0, -34.0, -58.0, -54.0],
            [0.0, -10.0, -22.0, -18.0, -36.0, -43.0],
            [0.0, -26.0, -39.0, -20.0, -44.0, -37.0],
            [0.0, -14.0, -18.0, -14.0, -19.0, -26.0],
        ]
    ),
}


def henderson_table(n_LO: int, m_RF: int, P_RF_dBm: float, P_LO_dBm: float) -> float:
    """Compute Mixer Spur suppression, based on table in Henderson Model paper."""

    dP: float = P_RF_dBm - P_LO_dBm

    return HENDERSON[abs(n_LO), abs(m_RF)] + dP * abs(m_RF - 1)


def marki_calc(n_LO: int, m_RF: int, P_RF_dBm: float, P_LO_dBm: float) -> float:
    """Compute Mixer Spur suppression, based on Marki calculator tool."""

    dP: float = P_RF_dBm - P_LO_dBm

    return MARKI_TABLES["H"][abs(n_LO), abs(m_RF)] + dP * abs(m_RF - 1)


def plot_spurs(
    input_freqs: tuple[float, float],
    output_freqs: tuple[float, float],
    LO: float,
    Pdiff: float,
    suppression_cutoff: float,
):
    order_multiples = (0,) + tuple(val for x in range(1, 6) for val in (x, -x))

    spur_levels: list[tuple[int, int, float]] = []

    # compute the spur suppression levels
    for lo, inp in itertools.combinations_with_replacement(order_multiples, 2):
        # for now, hard coded for 'H' Marki tables
        spur = marki_calc(abs(lo), abs(inp), 19 - Pdiff, 19)
        if np.isnan(spur) or spur < suppression_cutoff:
            continue

        spur_levels.append((lo, inp, spur))

    spur_levels.sort(key=lambda x: x[2], reverse=True)

    # Make the freq-freq plot
    spur_map_fig, spur_map_ax = plt.subplots(1, 1, squeeze=True)  # type: ignore

    # Make the spectrum output plot
    spectrum_fig, spectrum_ax = plt.subplots(1, 1, squeeze=True)  # type: ignore

    for LO_order, input_order, spur in spur_levels:
        mix_start = LO * LO_order + input_order * input_freqs[0]
        mix_end = LO * LO_order + input_order * input_freqs[1]

        if (mix_start < output_freqs[0] and mix_end < output_freqs[0]) or (
            mix_start > output_freqs[1] and mix_end > output_freqs[1]
        ):
            continue

        label = f"LO {LO_order} x Input {input_order}: {spur:.0f} dBc"

        spur_map_ax.plot(input_freqs, (mix_start, mix_end), label=label)

        spectrum_ax.plot((mix_start, mix_end), (spur, spur), label=label)
        spectrum_ax.fill_between(
            (mix_start, mix_end),
            suppression_cutoff,
            y2=spur,  # type: ignore
            alpha=0.2,
        )

    spur_map_ax.set_xlim(input_freqs)
    spur_map_ax.set_ylim(output_freqs)
    spur_map_ax.set_xlabel("Input Frequency [GHz]")
    spur_map_ax.set_ylabel("Output Frequency [GHz]")
    spur_map_ax.grid()
    spur_map_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    spur_map_fig.tight_layout()

    spectrum_ax.set_xlim(output_freqs)
    spectrum_ax.set_ylim(suppression_cutoff, 5)
    spectrum_ax.set_xlabel("Output Frequency [GHz]")
    spectrum_ax.set_ylabel("Spur Level [dBc]")
    spectrum_ax.grid()
    spectrum_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    spectrum_fig.tight_layout()

    # Activate hover annotations
    warnings.filterwarnings(
        action="ignore", message="Pick support for PolyCollection is missing."
    )
    cursor = mplcursors.cursor(spur_map_ax.axes, hover=True)  # type: ignore
    cursor = mplcursors.cursor(spectrum_ax.axes, hover=True)  # type: ignore

    # Customize the annotation text to show our custom labels
    @cursor.connect("add")
    def on_add(sel):
        sel.annotation.set_text(sel.annotation.get_text().split("\n")[0])

    try:
        plt.show()
    except KeyboardInterrupt:
        plt.close("all")


if __name__ == "__main__":
    # try:
    #     if_start = float(input("Input Start: "))
    #     if_stop = float(input("Input Stop: "))
    #     rf_start = float(input("Output Start: "))
    #     rf_stop = float(input("Output Stop: "))
    #     lo = float(input("LO: "))
    #     power_diff = float(input("Power delta: "))
    # except ValueError as e:
    #     print(f"Invalid input: {e}")
    #     sys.exit(0)

    if_start = 1
    if_stop = 1.2
    rf_start = 6
    rf_stop = 20
    lo = 10
    power_diff = 1
    plot_spurs((if_start, if_stop), (rf_start, rf_stop), lo, power_diff, -120)
