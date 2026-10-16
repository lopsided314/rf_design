"""RF Mixer Spur Estimation and Visualization.

The goal of this script is to allow visualization of mixer spurs through
a double-balanced RF mixer. It was inspired by the online calculator tool
from Marki Microwave.

Reference: https://markimicrowave.com/technical-resources/tools/spur-calculator/

"""

import itertools
import sys

import matplotlib.pyplot as plt
import mplcursors
import numpy as np

#
# Constants taken from the Henderson paper. Just the ones in the table on
# page 1, not the general equation.
#
# Arrays are indexed [n_LO, m_RF].
#
HENDERSON = np.array(
    [
        [0, np.nan, np.nan, np.nan, np.nan, np.nan],
        [0, 0, -41, -28, np.nan, np.nan],
        [0, -35, -39, -44, np.nan, np.nan],
        [0, -10, -32, -18, np.nan, np.nan],
        [0, -35, -39, np.nan, np.nan, np.nan],
        [0, -14, np.nan, -14, np.nan, np.nan],
    ]
)

#
# Constants ripped from the Marki Microwave online spur calculator.
#
# 'L', 'M', 'N', and 'H' represent LO drive levels, specific to their own product
# line, e.g. they make a MM1-0320LS and a MM1-0320HS
#
# L = +10 dBm
# M = +13 dBm
# N = +16 dBm
# H = +19 dBm
#
# Arrays are indexed [n_LO, m_RF].
#
MARKI_TABLES: dict[str, np.ndarray] = {
    "L": np.array(
        [
            [0, -26.0, -39.0, -45.0, -68.0, -59.0],
            [0, 0.0, -33.0, -28.0, -51.0, -57.0],
            [0, -26.0, -39.0, -35.0, -58.0, -55.0],
            [0, -10.0, -23.0, -18.0, -37.0, -43.0],
            [0, -26.0, -39.0, -21.0, -44.0, -38.0],
            [0, -14.0, -19.0, -14.0, -20.0, -26.0],
        ]
    ),
    "M": np.array(
        [
            [0, -26.0, -39.0, -44.0, -68.0, -59.0],
            [0, 0.0, -32.0, -28.0, -50.0, -57.0],
            [0, -26.0, -39.0, -35.0, -58.0, -54.0],
            [0, -10.0, -23.0, -18.0, -36.0, -43.0],
            [0, -26.0, -39.0, -21.0, -44.0, -37.0],
            [0, -14.0, -18.0, -14.0, -19.0, -26.0],
        ]
    ),
    "N": np.array(
        [
            [0, -27.0, -39.0, -46.0, -68.0, -60.0],
            [0, 0.0, -34.0, -28.0, -52.0, -57.0],
            [0, -27.0, -39.0, -36.0, -58.0, -56.0],
            [0, -10.0, -24.0, -18.0, -38.0, -43.0],
            [0, -27.0, -39.0, -22.0, -44.0, -39.0],
            [0, -14.0, -20.0, -14.0, -21.0, -26.0],
        ]
    ),
    "H": np.array(
        [
            [0, -26.0, -39.0, -44.0, -68.0, -58.0],
            [0, 0.0, -32.0, -28.0, -50.0, -57.0],
            [0, -26.0, -39.0, -34.0, -58.0, -54.0],
            [0, -10.0, -22.0, -18.0, -36.0, -43.0],
            [0, -26.0, -39.0, -20.0, -44.0, -37.0],
            [0, -14.0, -18.0, -14.0, -19.0, -26.0],
        ]
    ),
}


def henderson_table(n_LO: int, m_RF: int, P_delta: float) -> float:
    """Compute Mixer Spur suppression, based on table in Henderson Model paper."""

    try:
        return HENDERSON[abs(n_LO), abs(m_RF)] + P_delta * (abs(m_RF) - 1)
    except IndexError:
        return np.nan


def marki_calc(n_LO: int, m_RF: int, P_delta: float) -> float:
    """Compute Mixer Spur suppression, based on Marki calculator tool."""

    try:
        return MARKI_TABLES["H"][abs(n_LO), abs(m_RF)] + P_delta * (abs(m_RF) - 1)
    except IndexError:
        return np.nan


def plot_spurs(
    input_freqs: tuple[float, float],
    output_freqs: tuple[float, float],
    LO: float,
    Pdiff: float,
    LO_suppression: float,
    suppression_cutoff: float,
):
    """Generate plots to visualize mixer spurs.

    Args:
        input_freqs (tuple[float, float]): Input frequency range
        output_freqs (tuple[float, float]): Output frequency range
        LO (float): LO frequency
        Pdiff (float): Power difference between LO and RF signals (P_RF - P_LO)
        LO_isolation (float): Isolation from L to R port
        suppression_cutoff (float): Mimimum spur level to show on plots
    """

    spur_levels: list[tuple[int, int, float]] = []

    # compute the spur suppression levels
    for n_LO, m_RF in itertools.product(range(-5, 6), repeat=2):

        spur = marki_calc(abs(n_LO), abs(m_RF), Pdiff)
        if np.isnan(spur) or spur < suppression_cutoff or n_LO == m_RF == 0:
            continue

        if m_RF == 0:
            spur_levels.append((n_LO, m_RF, LO_suppression - Pdiff))
        else:
            spur_levels.append((n_LO, m_RF, spur))

    spur_levels.sort(key=lambda x: x[2], reverse=True)

    # Make the freq-freq plot
    spur_web_fig, spur_web_ax = plt.subplots(1, 1, squeeze=True)

    # Make the spectrum plot
    spectrum_fig, spectrum_ax = plt.subplots(1, 1, squeeze=True)

    # add all the spurs to the plots
    for n_LO, m_RF, spur in spur_levels:
        mixed_start = LO * n_LO + m_RF * input_freqs[0]
        mixed_end = LO * n_LO + m_RF * input_freqs[1]

        if (mixed_start < output_freqs[0] and mixed_end < output_freqs[0]) or (
            mixed_start > output_freqs[1] and mixed_end > output_freqs[1]
        ):
            continue

        label = f"LO {n_LO} x Input {m_RF}: {spur:.0f} dBc"
        spur_web_ax.plot(input_freqs, (mixed_start, mixed_end), label=label)

        # If it is one of the LO harmonics, make it a nice little arrow instead
        # of the highlighted span
        if m_RF == 0:
            spectrum_ax.plot(
                (mixed_start, mixed_end),
                (suppression_cutoff, spur),
                label=label,
            )
            spectrum_ax.plot(
                mixed_end,
                spur,
                marker="^",
                markeredgecolor=spectrum_ax.lines[-1].get_color(),
                markerfacecolor=spectrum_ax.lines[-1].get_color(),
            )
        else:
            spectrum_ax.plot(
                (mixed_start, mixed_end),
                (spur, spur),
                label=label,
            )
            spectrum_ax.fill_between(
                (mixed_start, mixed_end),
                suppression_cutoff,
                y2=spur,
                alpha=0.2,
                color=spectrum_ax.lines[-1].get_color(),
            )

    spur_web_ax.set_xlim(input_freqs)
    spur_web_ax.set_ylim(output_freqs)
    spur_web_ax.set_xlabel("Input Frequency [GHz]")
    spur_web_ax.set_ylabel("Output Frequency [GHz]")
    spur_web_ax.grid()
    spur_web_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    spur_web_ax.set_title(f"Spur Web: LO = {LO}, $\\Delta$P = {Pdiff} dB")
    spur_web_fig.tight_layout()

    spectrum_ax.set_xlim(output_freqs)
    spectrum_ax.set_ylim(suppression_cutoff, 5)
    spectrum_ax.set_xlabel("Output Frequency [GHz]")
    spectrum_ax.set_ylabel("Spur Level [dBc]")
    spectrum_ax.grid()
    spectrum_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    spectrum_ax.set_title(
        f"Spur Spectrum: In = {input_freqs}, LO = {LO}, $\\Delta$P = {Pdiff} dB"
    )
    spectrum_fig.tight_layout()

    # Activate hover annotations
    web_cursor = mplcursors.cursor(spur_web_ax.lines, hover=True)
    spectrum_cursor = mplcursors.cursor(spectrum_ax.lines, hover=True)

    # Customize the annotation text to show our custom labels
    #
    # LLM Slop, don't know how this works
    @web_cursor.connect("add")
    def on_add_web(sel):
        sel.annotation.set_text(sel.annotation.get_text().split("\n")[0].strip())

    @spectrum_cursor.connect("add")
    def on_add_spectum(sel):
        sel.annotation.set_text(sel.annotation.get_text().split("\n")[0].strip())

    try:
        plt.show()
    except KeyboardInterrupt:
        plt.close("all")


if __name__ == "__main__":

    def _float_split(prompt: str) -> tuple[float, float]:
        """fuck shit ass"""
        first, second = input(prompt).replace(",", " ").replace("/", " ").split()

        return float(first), float(second)

    if False:
        try:
            if_start, if_stop = _float_split("Input Start / Stop: ")
            rf_start, rf_stop = _float_split("Output Start / Stop: ")
            lo = float(input("LO: "))
        except (ValueError, IndexError) as e:
            print(f"Invalid input: {e}")
            sys.exit(0)
    else:
        if_start, if_stop = 5.5, 6.5
        rf_start, rf_stop = 0, 17
        lo = 8.3

    # Not included in user input because idk I didn't want it there
    power_diff = -20  # Power difference between LO and IF/RF input
    min_spur_level_dBc = -100  # Minimum displayed spur level
    lo_suppression = -40  # isolation between L and R port on mixer

    plot_spurs(
        (if_start, if_stop),
        (rf_start, rf_stop),
        lo,
        power_diff,
        lo_suppression,
        min_spur_level_dBc,
    )
