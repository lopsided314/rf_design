import json

import signal_chain.components as rf_component
import signal_chain.utils.signal_chain_math as sgc_math

def get_VSWR_param(spec: dict[str, float]) -> float:
    """Find if any of the parameters can be turned into a VSWR."""
    match spec:
        case {"VSWR": VSWR} | {"Input VSWR": VSWR}:
            return VSWR
        case {"Input Return Loss dB": rl} | {"Return Loss dB": rl}:
            return sgc_math.return_loss_to_VSWR(rl)  # type: ignore
        case _:
            return 1


def parse_amp(name: str, spec: dict[str, float]) -> dict[str, rf_component.RFComponent]:
    """Take amplifier parameters from the catalog json and turn it into a Component object."""
    return {
        name: rf_component.Amp(
            gain_dB=spec["Gain dB"],
            NF_dB=spec["Noise Figure dB"],
            VSWR=get_VSWR_param(spec),
            OP1dB_dBm=spec.get("OP1dB dBm", 999),
            desc=name,
        )
    }


def parse_mixer(
    name: str, spec: dict[str, float]
) -> dict[str, rf_component.RFComponent]:
    """Take mixer parameters from the catalog json and turn it into a Component object."""
    return {
        name: rf_component.Mixer(
            loss_dB=spec["Conversion Loss dB"],
            NF_dB=spec["Noise Figure dB"],
            VSWR=get_VSWR_param(spec),
            IP1dB_dBm=spec.get("IP1dB dBm", 999),
            desc=name,
        )
    }


def parse_lossy(
    name: str, spec: dict[str, float]
) -> dict[str, rf_component.RFComponent]:
    """Take parameters of lossy component from the catalog json
    and turn it into a Component object."""
    return {
        name: rf_component.Loss(
            loss_dB=spec["Insertion Loss dB"],
            VSWR=get_VSWR_param(spec),
            Pin_warn_dBm=spec.get("Pin Max dBm", 999),
            desc=name,
        )
    }


def read_catalog(filename: str) -> dict[str, rf_component.RFComponent]:
    """Open the parts catalog json given by filename and generate"""
    with open(filename) as f:
        catalog = json.load(f)

    components: dict[str, rf_component.RFComponent] = {}
    for category, parts_list in catalog.items():
        if category == "Amps":
            for part_name, spec in parts_list.items():
                components.update(parse_amp(part_name, spec))
        elif category == "Mixers":
            for part_name, spec in parts_list.items():
                components.update(parse_mixer(part_name, spec))
        else:  # pretend everything else is default lossy component
            for part_name, spec in parts_list.items():
                components.update(parse_lossy(part_name, spec))
    return components
