from opentrons import protocol_api
from dataclasses import dataclass
from typing import List, Set, Union


metadata = {
    "name": "OT-2 CSV RTP with No Headers",
    "author": "Josh McVey",
    "description": "Use 2D access in the CSV",
}
requirements = {
    "robotType": "OT-2",
    "apiLevel": "2.20",
}


def add_parameters(parameters):
    parameters.add_csv_file(
        variable_name="csv",
        display_name="1 Row CSV",
        description="Table of labware, wells, and volumes to transfer.",
    )


def evaluate_list_of_lists(
    list_of_lists: List[List[str]], ctx: protocol_api.ProtocolContext
) -> List[str]:
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
    one_row_csv = ctx.params.csv.parse_as_csv()
    evaluate_list_of_lists(one_row_csv, ctx)
