"""Signal chain computation example.

Example program showing how to use the signal chain library.
"""

from signal_chain import components as sgc_comp
from signal_chain.component_chain import ComponentChain
from signal_chain import sgc_analyzer


def example() -> None:
    """Demonstrate how to use the signal chain library to analyze a problem.

    The problem shown here is Example 10.2 in Pozar's Microwave Engineering, 4e.
    """

    # make a list of one or more components
    components: list[sgc_comp.RFComponent] = [
        sgc_comp.Amp(10, 2, OP1dB_dBm=0, desc="lna"),
        sgc_comp.Loss(1, desc="bpf"),
        sgc_comp.Mixer(3, 4, desc="mixer"),
    ]

    # make a list of one or more sections
    sections: list[ComponentChain] = [
        ComponentChain(desc="Example 10.2", components=components),
    ]

    # perform analysis with desired inputs
    sgc_analyzer.analyze_sections(
        sections=sections,
        Pin_dBm=-82.8,
        BW_MHz=10,
        Tin=150,
        filename="sgc_example.txt",
    )
