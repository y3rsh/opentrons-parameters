import json
from pathlib import Path
import subprocess
from typing import Optional
from your_paths import (
    PROTOCOL_FILE_PATH,
    ANALYSIS_OUTPUT_PATH,
    CSV_RTP_VARIABLE_NAME,
    opentrons_app_python_executable_path,
    get_rtp_data,
    get_csv_rtp_data,
    get_labware_paths,
)


def execute_analyze_command():
    # Retrieve RTP and CSV data
    rtp_data: Optional[dict] = get_rtp_data()
    csv_rtp_data: Optional[Path] = get_csv_rtp_data()

    # Prepare command arguments for RTP values and files, escaping properly
    rtp_arg: Optional[str] = None
    csv_rtp_arg: Optional[str] = None
    if rtp_data:
        rtp_arg = f"--rtp-values={json.dumps(rtp_data)}"
    if csv_rtp_data:
        csv_rtp_data_json = json.dumps({CSV_RTP_VARIABLE_NAME: str(csv_rtp_data)})
        csv_rtp_arg = f"--rtp-files={csv_rtp_data_json}"

    # Construct the command list
    command = [
        str(opentrons_app_python_executable_path()),
        "-I",
        "-m",
        "opentrons.cli",
        "analyze",
    ]

    # Append the arguments only if they exist
    if rtp_arg:
        command.append(rtp_arg)
    if csv_rtp_arg:
        command.append(csv_rtp_arg)

    command.extend(
        [
            "--json-output",
            str(ANALYSIS_OUTPUT_PATH),
            str(PROTOCOL_FILE_PATH),
        ]
    )

    custom_labware_paths = get_labware_paths()
    if custom_labware_paths:
        command.extend([str(path) for path in custom_labware_paths])

    # Print the command as a single string for inspection
    command_string = " ".join(command)
    print("Command to execute:")
    print(command_string)
    print("\n Running command...\n")

    # Execute the command
    result = subprocess.check_output(command)
    print(result.decode())


if __name__ == "__main__":
    execute_analyze_command()
