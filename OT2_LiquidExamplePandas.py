import pandas as pd
from opentrons import protocol_api
from typing import List, Set
import pprint

metadata = {
    "name": "Flex Liquid Example with Pandas",
    "author": "Josh McVey",
}
requirements = {
    "robotType": "OT-2",
    "apiLevel": "2.20",
}


class LiquidDestinations:
    ctx: protocol_api.ProtocolContext

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.destinations = pd.DataFrame()

    def add_destination(self, destination: pd.DataFrame) -> None:
        # Check for overlapping wells with previously added destinations
        for _, row in destination.iterrows():
            if not self.destinations.empty:
                overlapping = self.destinations[
                    (self.destinations["labware_load_name"] == row["labware_load_name"])
                    & (self.destinations["slot"] == row["slot"])
                    & (
                        self.destinations["wells"].apply(
                            lambda wells: any(well in wells for well in row["wells"])
                        )
                    )
                ]
                if not overlapping.empty:
                    overlapping_wells = set(row["wells"]).intersection(
                        *overlapping["wells"].tolist()
                    )
                    raise ValueError(
                        f"Wells {overlapping_wells} in labware {row['labware_load_name']} at slot {row['slot']} have already been defined."
                    )
        self.destinations = pd.concat(
            [self.destinations, destination], ignore_index=True
        )

    def get_destinations(self) -> pd.DataFrame:
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

        # Convert the list of lists into a DataFrame
        headers = data[0]

        # Expected headers
        expected_headers = {
            "labware_load_name",
            "slot",
            "wells",
            "name",
            "description",
            "display_color",
            "volume",
        }

        # Validate headers
        if not set(headers).issuperset(expected_headers):
            missing_headers = expected_headers - set(headers)
            unexpected_headers = set(headers) - expected_headers
            error_message = ""
            if missing_headers:
                error_message += f"Missing headers: {', '.join(missing_headers)}. "
            if unexpected_headers:
                error_message += f"Unexpected headers: {', '.join(unexpected_headers)}."
            self.ctx.comment(error_message)
            raise ValueError(error_message)

        df = pd.DataFrame(data[1:], columns=headers)

        # Convert 'volume' to float and validate
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        if df["volume"].isnull().any():
            invalid_rows = df[df["volume"].isnull()]
            error = f"Invalid volume values found: {invalid_rows}"
            self.ctx.comment(error)
            raise ValueError(error)

        # Split wells by the delimiter
        df["wells"] = df["wells"].apply(lambda x: set(x.split(well_delimiter)))

        # Check for empty fields
        if df.isnull().values.any() or (df.applymap(lambda x: x == "").any().any()):
            error = "There are empty fields in the data."
            self.ctx.comment(error)
            raise ValueError(error)

        # Add destinations
        self.add_destination(df)


def get_unique_labware_slots(destinations: pd.DataFrame) -> Set[str]:
    unique_labware_slots = set(
        destinations[["labware_load_name", "slot"]].apply(tuple, axis=1)
    )
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
        ctx.load_labware(labware[0], labware[1])
    for _, destination in liquid_destinations.get_destinations().iterrows():
        liquid = ctx.define_liquid(
            name=destination["name"],
            description=destination["description"],
            display_color=destination["display_color"],
        )
        for well in destination["wells"]:
            ctx.deck[destination["slot"]].wells_by_name()[well].load_liquid(
                liquid=liquid, volume=destination["volume"]
            )
