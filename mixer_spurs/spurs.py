import itertools

import matplotlib.pyplot as plt
import mplcursors


def henderson_table(
    n_LO: int, m_RF: int, P_RF_dBm: float, P_LO_dBm: float
) -> float | None:
    """Compute Mixer Spur suppression, based on Henderson Model paper."""

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

    try:
        return suppression[n_LO][m_RF]
    except IndexError:
        return None
        # raise ValueError(f"No suppression value for {m_RF=}, {n_LO=}")


def marki_calc(n_LO: int, m_RF: int, P_RF_dBm: float, P_LO_dBm: float) -> float | None:
    """Compute Mixer Spur suppression, based on Marki calculator tool."""

    dP: float = P_RF_dBm - P_LO_dBm

    suppression_LO_10dBm_LMixer: tuple[tuple[float, ...], ...] = (
        (  # LO 0
            dP - 8,
            -26,
            dP - 39,
            2 * dP - 45,
            3 * dP - 68,
            4 * dP - 59,
        ),
        (  # LO 1
            dP - 8,
            0,
            dP - 33,
            2 * dP - 28,
            3 * dP - 51,
            4 * dP - 57,
        ),
        (  # LO 2
            dP - 8,
            -26,
            dP - 39,
            2 * dP - 35,
            3 * dP - 58,
            4 * dP - 55,
        ),
        (  # LO 3
            dP - 8,
            -10,
            dP - 23,
            2 * dP - 18,
            3 * dP - 37,
            4 * dP - 43,
        ),
        (  # LO 4
            dP - 8,
            -26,
            dP - 39,
            2 * dP - 21,
            3 * dP - 44,
            4 * dP - 38,
        ),
        (  # LO 5
            dP - 8,
            -14,
            dP - 19,
            2 * dP - 14,
            3 * dP - 20,
            4 * dP - 26,
        ),
    )

    try:
        return suppression_LO_10dBm_LMixer[n_LO][m_RF]
    except IndexError:
        return None
        # raise ValueError(f"No suppression value for {m_RF=}, {n_LO=}")


def main(
    input_freqs: tuple[float, float],
    output_freqs: tuple[float, float],
    LO: float,
    suppression_cutoff: float,
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

        supression = marki_calc(abs(LO_order), abs(input_order), 0, 10)
        if supression is not None and suppression_cutoff < supression:
            plt.plot(
                input_freqs,
                (output_start, output_end),
                label=f"LO {LO_order} x Input {input_order}: {supression} dBc",
            )

    plt.xlim(input_freqs)
    plt.ylim(output_freqs)
    plt.xlabel("Input Frequency [GHz]")
    plt.ylabel("Output Frequency [GHz]")
    plt.grid()
    plt.gca().legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    # Activate hover annotations
    cursor = mplcursors.cursor(plt.gca().axes, hover=True)

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
