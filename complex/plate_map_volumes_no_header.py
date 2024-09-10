from dataclasses import dataclass, field
from typing import Dict, List


metadata = {"name": "complex", "author": "Josh McVey", "description": ""}
requirements = {
    "robotType": "Flex",
    "apiLevel": "2.20",
}


@dataclass
class Well:
    row: str
    column: int
    volume: float | int


# Example list of lists where [0][0] is A1, [0][1] is A2, ..., [7][11] is H12
# this is what your CSV looks like, no header row
# the cell position as understood in a spreadsheet view of the CSV
# indicates the target well in the plate
volumes = [
    # 1  2   3   4   5   6   7   8   9   10  11  12
    [99, 97, 96, 96, 92, 95, 94, 94, 99, 99, 99, 94],  # Row A
    [95, 98, 91, 90, 99, 93, 93, 98, 100, 93, 97, 94],  # Row B
    [94, 93, 99, 98, 92, 92, 99, 93, 93, 98, 99, 98],  # Row C
    [96, 96, 96, 96, 97, 97, 96, 100, 100, 100, 92, 99],  # Row D
    [96, 97, 92, 98, 92, 96, 90, 99, 91, 90, 93, 97],  # Row E
    [90, 97, 95, 99, 100, 90, 100, 91, 97, 99, 91, 99],  # Row F
    [99, 96, 99, 98, 98, 100, 97, 98, 92, 98, 92, 99],  # Row G
    [99, 94, 97, 97, 95, 92, 92, 98, 95, 98, 96, 92],  # Row H
]


@dataclass
class Plate:
    """representation of a 96 well plate A1 -> H12"""

    # This allows us to follow the convention used in the Opentrons API
    # plate.wells["A1"] will return the well in the top left corner of the plate
    wells: Dict[str, Well] = field(default_factory=dict)

    def __post_init__(self):
        # Initialize all wells in a 96 well plate
        self.ROWS: List[str] = list("ABCDEFGH")
        self.COLUMNS: List[int] = [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
        ]  # more clear than list(range(1, 13))
        for row in self.ROWS:
            for col in self.COLUMNS:
                well_id = f"{row}{col}"
                self.wells[well_id] = Well(row=row, column=col, volume=0)

    def get_well(self, well_id: str) -> Well:
        return self.wells[well_id.upper()]

    def set_well_volume(self, well_id: str, volume: int | float) -> None:
        self.wells[well_id.upper()].volume = volume

    def load_volumes_from_list(self, volumes: List[List[int | float]]) -> None:
        # Check if there are exactly 8 rows
        if len(volumes) != 8:
            raise ValueError(
                f"Invalid number of rows: expected 8, but got {len(volumes)}"
            )

        # Check if each row has exactly 12 columns
        for i, row in enumerate(volumes):
            if len(row) != 12:
                raise ValueError(
                    f"Invalid number of columns in row {i + 1}: expected 12, but got {len(row)}"
                )
        rows = "ABCDEFGH"
        for i, row in enumerate(volumes):
            for j, volume in enumerate(row):
                well_id = f"{rows[i]}{j+1}"
                self.set_well_volume(well_id, volume)

    def get_row_string(self, row: str) -> str:
        """
        Returns a string representing the specified row in the format A1=99, A2=97, ..., A12=94.

        :param row: The row letter (A-H)
        :return: A formatted string representing the row
        """
        row = row.upper()
        row_string = ", ".join(
            [f"{row}{col}={self.wells[f'{row}{col}'].volume}" for col in range(1, 13)]
        )
        return row_string

    def __str__(self):
        # Create the string representation of the plate
        # ctx.comment() will rip out the /n but testing directly it looks good on the console
        # handles 4 digit int and up to 3 digit float and still looks good
        # 45.8 or 4000
        plate_str = "Plate Layout:\n"
        plate_str += "    " + "  ".join([f"{col:>4}" for col in range(1, 13)]) + "\n"
        plate_str += "  " + "-" * 74 + "\n"
        for row in "ABCDEFGH":
            row_str = [f"{self.wells[f'{row}{col}'].volume:>4}" for col in range(1, 13)]
            plate_str += f"{row} | " + "  ".join(row_str) + "\n"

        return plate_str


def add_parameters(parameters):
    parameters.add_csv_file(
        variable_name="well_map",
        display_name="Well Map with Volumes",
        description="Spreadsheet Cell Position is the well address, value is the volume.",
    )


###### protocol ######


def run(protocol):
    well_map = protocol.params.well_map.parse_as_csv()
    plate = Plate()
    plate.load_volumes_from_list(well_map)
    for row in plate.ROWS:
        protocol.comment(f"Row {row}: {plate.get_row_string(row)}")


###### for testing ######


def main():
    plate = Plate()
    plate.load_volumes_from_list(volumes)
    print(plate.__str__())
    print()
    for row in plate.ROWS:
        print(f"Row {row}:")
        print(plate.get_row_string(row))


# python plate_map_volumes_no_header.py
if __name__ == "__main__":
    main()
