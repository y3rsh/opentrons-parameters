from dataclasses import dataclass
from pydantic import BaseModel, validator, ValidationError
from typing import List, Set
from opentrons import protocol_api
import pprint

metadata = {
    "name": "Flex Liquid Example",
    "author": "Josh McVey",
}
requirements = {
    "robotType": "OT-2",
    "apiLevel": "2.20",
}


# Pydantic bundled in the App/Robot is version 1.10.17 as of 8/9/2024
class LiquidDestination(BaseModel):
    labware_load_name: str
    slot: str
    wells: Set[str]
    name: str
    description: str
    display_color: str
    volume: float

    @validator("volume")
    def volume_value(cls, value):
        if value is None:
            raise ValueError("Volume cannot be None")
        if not (0 < value <= 100.00):
            raise ValueError(
                "Volume must be greater than 0 and less than or equal to 100.00"
            )
        return value

    @validator("wells", pre=True)
    def split_wells(cls, value):
        if not value:
            raise ValueError("Wells cannot be None")
        if isinstance(value, str):
            return set(value.split(";"))
        return value

    @validator("labware_load_name", "slot", "name", "description", "display_color")
    def no_empty_strings(cls, value):
        if not value:
            raise ValueError("Field cannot be None")
        if value.strip() == "":
            raise ValueError("Field cannot be empty string")
        return value

    @property
    def key(self) -> str:
        if not self.labware_load_name or not self.slot:
            raise ValueError("Labware name and slot must be defined")
        return f"{self.labware_load_name}_{self.slot}"


class LiquidDestinations:
    ctx: protocol_api.ProtocolContext

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.destinations: List[LiquidDestination] = []

    def add_destination(self, destination: LiquidDestination) -> None:
        # has this destination already been added?
        liquids_in_same_slot = [d for d in self.destinations if d.key == destination.key]

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
        self, data: List[List[str]]
    ) -> None:
        if not data or not isinstance(data, list) or len(data) < 2:
            data_error = "Data must be a non-empty list of lists with at least two rows."
            self.ctx.comment(data_error)
            raise ValueError(data_error)

        headers = data[0]
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
                error_message += f"Unexpected headers: {', '.join(unexpected_headers)}. "
            if missing_headers:
                error_message += f"Missing headers: {', '.join(missing_headers)}."
            self.ctx.comment(error_message)
            raise ValueError(error_message)

        # Process each row of data
        for index, row in enumerate(data[1:], start=1):
            row_dict = dict(zip(headers, row))

            try:
                destination = LiquidDestination.parse_obj(row_dict)
                self.add_destination(destination)
            except ValidationError as e:
                error = f"Validation error in row {index + 1}: {e.json()}"
                self.ctx.comment(error)
                raise ValueError(error)


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
    ctx.comment(pprint.pformat(liquids, indent=4, width=80))
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
