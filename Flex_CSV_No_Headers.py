from opentrons import protocol_api
from dataclasses import dataclass
from typing import List, Set, Union


metadata = {
    "name": "CSV RTP with No Headers",
    "author": "Josh McVey",
    "description": "Use 2D access in the CSV",
}
requirements = {
    "robotType": "Flex",
    "apiLevel": "2.20",
}

TRASH_LOCATION = "A3"  # Where the trash is located



def add_parameters(parameters):
    parameters.add_str(
        display_name="Pipette Type & Tiprack",
        variable_name="pipette_and_tips",
        choices=[
            {
                "display_name": "50s w/ standard tips",
                "value": "flex_1channel_50,opentrons_flex_96_tiprack_50ul",
            },
            {
                "display_name": "50s w/ filter tips",
                "value": "flex_1channel_50,opentrons_flex_96_filtertiprack_50ul",
            },
            {
                "display_name": "1000s w/ standard 200 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_tiprack_200ul",
            },
            {
                "display_name": "1000s w/ filter 200 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_filtertiprack_200ul",
            },
            {
                "display_name": "1000s w/ standard 1000 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_tiprack_1000ul",
            },
            {
                "display_name": "1000s w/ filter 1000 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_filtertiprack_1000ul",
            },
        ],
        default="flex_1channel_50,opentrons_flex_96_tiprack_50ul",
        description="Select the pipette and tip type",
    )
    parameters.add_str(
        display_name="Pipette Mount",
        variable_name="pipette_mount",
        choices=[
            {"display_name": "left", "value": "left"},
            {"display_name": "right", "value": "right"},
        ],
        default="left",
        description="Select the pipette mount.",
    )
    parameters.add_csv_file(
        variable_name="csv",
        display_name="1 Row CSV",
        description="Table of labware, wells, and volumes to transfer.",
    )


FLEX_DECK_SLOTS = [
    "A1",
    "A2",
    "A3",
    "B1",
    "B2",
    "B3",
    "C1",
    "C2",
    "C3",
    "D1",
    "D2",
    "D3",
]

from typing import List

def evaluate_list_of_lists(list_of_lists: List[List[str]], ctx) -> List[str]:
    """
    Evaluates a list of lists and raises an error if there is more than one row.
    Prints the number of items in the first row and returns that list.

    Args:
        list_of_lists (List[List[str]]): A list containing sublists of strings.

    Returns:
        List[str]: The first list in the list of lists.

    Raises:
        ValueError: If there is more than one row in the input list.
    """
    if len(list_of_lists) != 1:
        raise ValueError("There is more than one row in the list.")
    
    first_row = list_of_lists[0]
    ctx.comment(f"Number of items in the first row: {len(first_row)}")
    for index, item in enumerate(first_row):
        ctx.comment(f"Item {index}: {item}")
    return first_row




def run(ctx: protocol_api.ProtocolContext):
    # Get the values from the RTPs
    pipette_type = ctx.params.pipette_and_tips.split(",")[0]
    tip_type = ctx.params.pipette_and_tips.split(",")[1]
    pipette_mount = ctx.params.pipette_mount
    one_row_csv = ctx.params.csv.parse_as_csv()

    # load trash
    trash = ctx.load_trash_bin(TRASH_LOCATION)

    # load tipracks
    tipracks = [ctx.load_labware(tip_type, "C1")]

    # load pipette
    pipette = ctx.load_instrument(pipette_type, pipette_mount, tip_racks=tipracks)




