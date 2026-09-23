import itertools

import matplotlib.pyplot as plt
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


def henderson_table(
    n_LO: int, m_RF: int, P_RF_dBm: float, P_LO_dBm: float
) -> float | None:
    """Compute Mixer Spur suppression, based on table in Henderson Model paper."""

    dP: float = P_RF_dBm - P_LO_dBm

    suppression: tuple[tuple[float | None, ...], ...] = (
        (None, None, None, None),
        (None, 0.0, dP - 41, 2 * dP - 28),
        (None, -35.0, dP - 44, 2 * dP - 44),
        (None, -10.0, dP - 32, 2 * dP - 18),
        (None, -35.0, dP - 39, None),
        (None, -14.0, None, 2 * dP - 14),
        (None, -35.0, dP - 39),
        (None, -17.0, None, 2 * dP - 11),
    )

    return suppression[n_LO][m_RF]


def marki_calc(n_LO: int, m_RF: int, P_RF_dBm: float, P_LO_dBm: float) -> float | None:
    """Compute Mixer Spur suppression, based on Marki calculator tool."""

    dP: float = P_RF_dBm - P_LO_dBm

    return MARKI_TABLES["H"][abs(n_LO), abs(m_RF)] + dP * abs(m_RF - 1)


def main(
    input_freqs: tuple[float, float],
    output_freqs: tuple[float, float],
    LO: float,
    supression_cutoff: float,
):
    order_multiples = (0,) + tuple(val for x in range(1, 6) for val in (x, -x))

    order_combos = tuple(itertools.combinations_with_replacement(order_multiples, 2))

    plt.figure()

    for LO_order, input_order in order_combos:
        output_start = LO * LO_order + input_order * input_freqs[0]
        output_end = LO * LO_order + input_order * input_freqs[1]

        if (output_start < output_freqs[0] and output_end < output_freqs[0]) or (
            output_start > output_freqs[1] and output_end > output_freqs[1]
        ):
            continue

        supression = marki_calc(abs(LO_order), abs(input_order), 0, 19)
        if (
            supression is not None
            and not np.isnan(supression)
            and supression >= supression_cutoff
        ):
            plt.plot(
                input_freqs,
                (output_start, output_end),
                label=f"LO {LO_order} x Input {input_order}: {supression:.0f} dBc",
            )

    plt.xlim(input_freqs)
    plt.ylim(output_freqs)
    plt.xlabel("Input Frequency [GHz]")
    plt.ylabel("Output Frequency [GHz]")
    plt.grid()
    plt.gca().legend(bbox_to_anchor=(1.05, 1), loc="upper left")  # type: ignore
    plt.tight_layout()

    # Activate hover annotations
    cursor = mplcursors.cursor(plt.gca().axes, hover=True)  # type: ignore

    # Customize the annotation text to show our custom labels
    @cursor.connect("add")
    def on_add(sel):
        sel.annotation.set_text(sel.annotation.get_text().split("\n")[0])

    try:
        plt.show()
    except KeyboardInterrupt:
        plt.close("all")


if __name__ == "__main__":
    main((1, 2), (5, 6), 4, -120)
