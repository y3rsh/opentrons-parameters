import csv
from io import StringIO
from opentrons import protocol_api
from dataclasses import dataclass
from typing import List, Set, Union
import pprint

metadata = {
    "name": "Flex Liquid Example",
    "author": "Josh McVey",
}
requirements = {
    "robotType": "OT-2",
    "apiLevel": "2.20",
}


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
    ctx: protocol_api.ProtocolContext

    def __init__(self, ctx) -> None:
        self.ctx = ctx
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
        if not data or not isinstance(data, list) or len(data) < 2:
            data_error = (
                "Data must be a non-empty list of lists with at least two rows."
            )
            self.ctx.comment(data_error)
            raise ValueError(data_error)

        headers = data[0]
        # note these match the properties of this class
        expected_headers = {
            "labware_load_name",
            "slot",
            "wells",
            "name",
            "description",
            "display_color",
            "volume",
        }

        # Validate that all expected headers are present
        unexpected_headers = set(headers) - expected_headers
        missing_headers = expected_headers - set(headers)
        if unexpected_headers or missing_headers:
            error_message = ""
            if unexpected_headers:
                error_message += (
                    f"Unexpected headers: {', '.join(unexpected_headers)}. "
                )
            if missing_headers:
                error_message += f"Missing headers: {', '.join(missing_headers)}."
            self.ctx.comment(error_message)
            raise ValueError(error_message)

        # Process each row of data
        # Fail fast on the first row missing fields or that has empty fields
        CHECK_MISSING_FIELDS = True  # less values than expected
        CHECK_EMPTY_FIELDS = True  # None or empty string
        for index, row in enumerate(data[1:], start=1):
            if CHECK_MISSING_FIELDS:
                if len(row) != len(expected_headers):
                    error = f"There are missing fields in data row: {index}, line {index+1} of the CSV. The row data is: {row}"
                    self.ctx.comment(error)
                    raise ValueError(error)

            if CHECK_EMPTY_FIELDS:
                for value in row:
                    if value is None or value.strip() == "":
                        error = f"There are empty fields in data row: {index}, line {index+1} of the CSV. The row data is: {row}"
                        self.ctx.comment(error)
                        raise ValueError(error)

            # Create a dictionary for the row using zip
            row_dict = dict(zip(headers, row))
            wells = set(row_dict["wells"].split(well_delimiter))
            try:
                volume = float(row_dict["volume"])
            except ValueError:
                error = f"Invalid volume value: {row_dict['volume']} in row: {row_dict}"
                self.ctx.comment(error)
                raise ValueError(error)

            destination = LiquidDestination(
                labware_load_name=row_dict["labware_load_name"],
                slot=row_dict["slot"],
                wells=wells,
                name=row_dict["name"],
                description=row_dict["description"],
                display_color=row_dict["display_color"],
                volume=volume,
            )
            self.add_destination(destination)


@dataclass(frozen=True)
class LabwareSlot:
    labware: str
    slot: str

    def __hash__(self):
        return hash((self.labware, self.slot))

    def __eq__(self, other):
        if not isinstance(other, LabwareSlot):
            return NotImplemented
        return (self.labware, self.slot) == (other.labware, other.slot)


def get_unique_labware_slots(liquids: List[LiquidDestination]) -> Set[LabwareSlot]:
    unique_labware_slots = set()
    for liquid in liquids:
        unique_labware_slots.add(LabwareSlot(liquid.labware_load_name, liquid.slot))
    return unique_labware_slots


def add_parameters(parameters):
    parameters.add_csv_file(
        variable_name="liquids",
        display_name="liquid definitions",
        description="Table of liquids",
    )


def run(ctx: protocol_api.ProtocolContext):

    # Get the values from the RTPs
    liquids = ctx.params.liquids.parse_as_csv()
    ctx.comment(pprint.pformat(liquids))
    liquid_destinations = LiquidDestinations(ctx)
    liquid_destinations.parse_list_of_lists(liquids)
    labwares = get_unique_labware_slots(liquid_destinations.get_destinations())
    for labware in labwares:
        ctx.load_labware(labware.labware, labware.slot)
    for destination in liquid_destinations.get_destinations():
        liquid = ctx.define_liquid(
            name=destination.name,
            description=destination.description,
            display_color=destination.display_color,
        )
        for well in destination.wells:
            ctx.deck[destination.slot].wells_by_name()[well].load_liquid(
                liquid=liquid, volume=destination.volume
            )
