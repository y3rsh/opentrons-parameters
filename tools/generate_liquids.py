import csv
import random
from typing import List, Set
from dataclasses import dataclass


class ColorPalette:
    def __init__(self) -> None:
        self.colors: Set[str] = {
            "#000000",
            "#FFFF00",
            "#1CE6FF",
            "#FF34FF",
            "#FF4A46",
            "#008941",
            "#006FA6",
            "#A30059",
            "#FFDBE5",
            "#7A4900",
            "#0000A6",
            "#63FFAC",
            "#B79762",
            "#004D43",
            "#8FB0FF",
            "#997D87",
            "#5A0007",
            "#809693",
            "#FEFFE6",
            "#1B4400",
            "#4FC601",
            "#3B5DFF",
            "#4A3B53",
            "#FF2F80",
            "#61615A",
            "#BA0900",
            "#6B7900",
            "#00C2A0",
            "#FFAA92",
            "#FF90C9",
            "#B903AA",
            "#D16100",
            "#DDEFFF",
            "#000035",
            "#7B4F4B",
            "#A1C299",
            "#300018",
            "#0AA6D8",
            "#013349",
            "#00846F",
            "#372101",
            "#FFB500",
            "#C2FFED",
            "#A079BF",
            "#CC0744",
            "#C0B9B2",
            "#C2FF99",
            "#001E09",
            "#00489C",
            "#6F0062",
            "#0CBD66",
            "#EEC3FF",
            "#456D75",
            "#B77B68",
            "#7A87A1",
            "#788D66",
            "#885578",
            "#FAD09F",
            "#FF8A9A",
            "#D157A0",
            "#BEC459",
            "#456648",
            "#0086ED",
            "#886F4C",
            "#34362D",
            "#B4A8BD",
            "#00A6AA",
            "#452C2C",
            "#636375",
            "#A3C8C9",
            "#FF913F",
            "#938A81",
            "#575329",
            "#00FECF",
            "#B05B6F",
            "#8CD0FF",
            "#3B9700",
            "#04F757",
            "#C8A1A1",
            "#1E6E00",
            "#7900D7",
            "#A77500",
            "#6367A9",
            "#A05837",
            "#6B002C",
            "#772600",
            "#D790FF",
            "#9B9700",
            "#549E79",
            "#FFF69F",
            "#201625",
            "#72418F",
            "#BC23FF",
            "#99ADC0",
            "#3A2465",
            "#922329",
            "#5B4534",
            "#FDE8DC",
            "#404E55",
            "#0089A3",
            "#CB7E98",
            "#A4E804",
            "#324E72",
            "#6A3A4C",
        }
        self.used_colors: Set[str] = set()

    def use_random_color(self) -> str:
        available_colors = self.colors - self.used_colors
        if not available_colors:
            raise Exception("No more available colors.")
        color = random.choice(list(available_colors))
        self.used_colors.add(color)
        return color

    def reset_used_colors(self) -> None:
        self.used_colors.clear()


@dataclass
class LiquidDestination:
    labware_load_name: str
    slot: str
    wells: Set[str]
    name: str
    description: str
    display_color: str
    volume: float

    @property
    def key(self) -> str:
        return f"{self.labware_load_name}_{self.slot}"


class LiquidDestinations:
    def __init__(self) -> None:
        self.destinations: List[LiquidDestination] = []

    def add_destination(self, destination: LiquidDestination) -> None:

        # has this destination already been added?
        liquids_in_same_slot = [
            d for d in self.destinations if d.key == destination.key
        ]

        # Check for overlapping wells with previously added destinations
        if liquids_in_same_slot:
            for liquid in liquids_in_same_slot:
                overlapping_wells = liquid.wells.intersection(destination.wells)
                if overlapping_wells:
                    raise ValueError(
                        f"Wells {overlapping_wells} in labware {destination.labware_load_name} at slot {destination.slot} have already been defined."
                    )
        # Add the destination
        self.destinations.append(destination)

    def get_destinations(self) -> List[LiquidDestination]:
        return self.destinations

    def parse_list_of_lists(
        self, data: List[List[str]], well_delimiter: str = ";"
    ) -> None:
        headers = data[0]
        for row in data[1:]:
            row_dict = dict(zip(headers, row))
            wells = set(row_dict["wells"].split(well_delimiter))
            destination = LiquidDestination(
                labware_load_name=row_dict["labware_load_name"],
                slot=row_dict["slot"],
                wells=wells,
                name=row_dict["name"],
                description=row_dict["description"],
                display_color=row_dict["display_color"],
                volume=float(row_dict["volume"]),
            )
            self.add_destination(destination)


# https://colorhunt.co/palette/17153b2e236c433d8bc8acd6
pallet = ["17153B", "2E236C", "433D8B", "C8ACD6"]
emoji = "🪄✨➡️🥳⬅️😭🤣😂😊❓▶️😝❤️😍😒👌😘💕"

color_palette = ColorPalette()
example_data = [
    [
        "labware_load_name",
        "slot",
        "name",
        "description",
        "display_color",
        "volume",
        "wells",
    ],
    [
        "nest_96_wellplate_100ul_pcr_full_skirt",
        "1",
        "H₂O",
        "Water, 100 µL",
        color_palette.use_random_color(),
        "100.0",
        "A1;B1;C1",
    ],
    [
        "nest_96_wellplate_100ul_pcr_full_skirt",
        "1",
        "1 M NaCl",
        "Sodium Chloride, 1 M",
        color_palette.use_random_color(),
        "100",
        "A3;B3;C3",
    ],
    [
        "nest_96_wellplate_100ul_pcr_full_skirt",
        "1",
        "EtOH",
        "Ethanol, 70%",
        color_palette.use_random_color(),
        "100.0",
        "F1;G1",
    ],
    [
        "nest_96_wellplate_100ul_pcr_full_skirt",
        "1",
        "Tris-HCl",
        "Tris Hydrochloride, 1 M",
        color_palette.use_random_color(),
        "50.0",
        "A10;A11",
    ],
    [
        "nest_96_wellplate_100ul_pcr_full_skirt",
        "1",
        "PBS",
        "Phosphate Buffered Saline, 1X",
        color_palette.use_random_color(),
        "100.0",
        "B10;B11",
    ],
    [
        "nest_96_wellplate_100ul_pcr_full_skirt",
        "1",
        "BSA",
        "Bovine Serum Albumin, 1 mg/mL",
        color_palette.use_random_color(),
        "100.0",
        "C10;C11",
    ],
]


def generate_96_rows() -> List[List[str]]:
    data = [
        [
            "labware_load_name",
            "slot",
            "name",
            "description",
            "display_color",
            "volume",
            "wells",
        ]
    ]
    rows, columns = 8, 12
    # chr(65 + r): Converts row index to corresponding letter (A-H) using ASCII values.
    # c + 1: Converts column index to corresponding number (1-12).
    # f"{chr(65 + r)}{c + 1}": Formats the well name by combining the letter and number.
    well_names = [f"{chr(65 + r)}{c + 1}" for r in range(rows) for c in range(columns)]

    for i in range(96):
        name = f"specimen{i + 1}"
        description = f"Description for {name}"
        display_color = color_palette.use_random_color()
        volume = "20"
        wells = well_names[i]
        row = [
            "nest_96_wellplate_100ul_pcr_full_skirt",
            "1",
            name,
            description,
            display_color,
            volume,
            wells,
        ]
        data.append(row)

    return data


def generate_csv(data: List[List[str]], filename: str) -> None:
    with open(filename, mode="w", newline="\n", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(data)


def main():
    generate_csv(example_data, "example_liquids.csv")
    generate_csv(generate_96_rows(), "96_wellplate_liquids.csv")


if __name__ == "__main__":
    main()
