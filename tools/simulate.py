import subprocess
import sys
from tools.your_paths import PROTOCOL_FILE_PATH


# TODO Labware definitions Path
def execute_opentrons_command():
    command = [
        sys.executable,
        "-I",
        "-m",
        "opentrons.simulate",
        PROTOCOL_FILE_PATH,
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        print("Command executed successfully:")
        print(result.stdout)
    else:
        print("Command failed with return code:", result.returncode)
        print(result.stderr)


if __name__ == "__main__":
    execute_opentrons_command()
