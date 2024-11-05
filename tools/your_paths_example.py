import json
from pathlib import Path
import sys
import csv
from typing import List, Optional

# Change this group for each protocol
PROTOCOL_FILE_PATH = Path(
    "/root/github/opentrons-parameters/Flex_Cherrypicking_Every_Run_Parameters.py"
)
RTP_DATA_PATH = Path(
    "/root/github/opentrons-parameters/rtp_data/Flex_Cherrypicking_RTP.json"
)
CSV_RTP_DATA_PATH = Path(
    "/root/github/opentrons-parameters/example_data/Flex-cherrypicking_template-default.csv"
)
CSV_RTP_VARIABLE_NAME = "cherrypicking_sequence"
ANALYSIS_OUTPUT_PATH = Path(
    "/root/github/opentrons-parameters/Flex_Cherrypicking_Every_Run_ParametersANALYSIS.json"
)

# Change ONCE when you setup this tool
# if you are not using custom labware at all you can set this to None
# LABWARE_LIBRARY_PATH = None
LABWARE_LIBRARY_PATH = Path("/mnt/c/Users/joshm/AppData/Roaming/Opentrons/labware")
# Paths for different OS platforms
WINDOWS_PYTHON_PATH = Path(
    "C:\\Program Files\\Opentrons\\resources\\python\\python.exe"
)
# download AppImage
# on Josh's WSL
# move to root
# chmod +x Opentrons-v8.2.0-alpha.0-linux-b49677.AppImage
# ./Opentrons-v8.2.0-alpha.0-linux-b49677.AppImage --appimage-extract
# mv squashfs-root/ /opt/opentrons
LINUX_PYTHON_PATH = Path("/opt/opentrons/resources/python/bin/python3")
MAC_PYTHON_PATH = Path("CHANGE_ME")

# Check important file paths
if not PROTOCOL_FILE_PATH.exists():
    print(f"❌ Protocol file not found at {PROTOCOL_FILE_PATH}")
    raise FileNotFoundError(f"Protocol file is missing: {PROTOCOL_FILE_PATH}")


def opentrons_app_python_executable_path() -> Path:
    """Return the appropriate Python executable path for Opentrons app."""
    if sys.platform == "win32":
        return WINDOWS_PYTHON_PATH
    elif sys.platform == "linux":
        return LINUX_PYTHON_PATH
    elif sys.platform == "darwin":
        return MAC_PYTHON_PATH
    else:
        raise EnvironmentError("Unsupported OS platform")


def get_rtp_data() -> Optional[dict]:
    """Load RTP data from specified path if it exists."""
    if not RTP_DATA_PATH.exists():
        print(f"No RTP data override found at {RTP_DATA_PATH}")
        return None
    with open(RTP_DATA_PATH, "r") as f:
        data = json.load(f)
        print(f"✅ Using RTP data override from {RTP_DATA_PATH}")
        print(json.dumps(data, indent=4))
        return data


def get_csv_rtp_data() -> Optional[Path]:
    """Load CSV RTP data from specified path if it exists and pretty-print it."""
    if not CSV_RTP_DATA_PATH.exists():
        print(f"No CSV RTP data override found at {CSV_RTP_DATA_PATH}")
        return None

    with open(CSV_RTP_DATA_PATH, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Display CSV headers and rows
        if rows:
            print(f"✅ Using CSV RTP data override from {CSV_RTP_DATA_PATH}")
            header, *data_rows = rows
            max_widths = [
                max(len(str(item)) for item in column) for column in zip(*rows)
            ]

            # Print headers with pretty formatting
            header_row = " | ".join(
                f"{col:<{max_widths[i]}}" for i, col in enumerate(header)
            )
            print(header_row)
            print("-" * len(header_row))

            # Print each row with matching column widths
            for row in data_rows:
                print(
                    " | ".join(
                        f"{str(col):<{max_widths[i]}}" for i, col in enumerate(row)
                    )
                )
        else:
            print("CSV file is empty.")

    return CSV_RTP_DATA_PATH


def get_labware_paths() -> Optional[List[Path]]:
    """Load and return paths to all .json labware files in the labware library directory."""
    if LABWARE_LIBRARY_PATH is None:
        print("No labware library path found.")
        return None
    if not LABWARE_LIBRARY_PATH.exists():
        print(f"No labware library found at {LABWARE_LIBRARY_PATH}")
        return None

    print(f"✅ Using labware library from {LABWARE_LIBRARY_PATH}")
    # Find all .json files in the directory and return as a list
    json_files = list(LABWARE_LIBRARY_PATH.glob("*.json"))

    # Check if no JSON files were found
    if not json_files:
        print("No .json files found in the labware library.")
    return json_files
