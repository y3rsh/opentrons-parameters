import importlib.util
import json
from your_paths import PROTOCOL_FILE_PATH, RTP_DATA_PATH

# Ensure the protocol file path exists
if not PROTOCOL_FILE_PATH.exists():
    raise FileNotFoundError(f"Protocol file not found at {PROTOCOL_FILE_PATH}")

# Load the module from the specified file path
spec = importlib.util.spec_from_file_location("protocol_module", PROTOCOL_FILE_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load module from {PROTOCOL_FILE_PATH}")
protocol_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol_module)

# Access add_parameters from the dynamically loaded module
add_parameters = protocol_module.add_parameters


# Custom class to capture parameter details
class MockParameters:
    def __init__(self):
        self.params = {}

    def add_str(self, display_name, variable_name, choices, default, description):
        self.params[variable_name] = default

    def add_int(
        self, display_name, variable_name, default, min_val, max_val, description
    ):
        self.params[variable_name] = default

    def add_bool(self, display_name, variable_name, default, description):
        self.params[variable_name] = default

    # Ignore calls to add_csv_file
    def add_csv_file(self, variable_name, display_name, description):
        pass


# Initialize MockParameters instance
parameters = MockParameters()

# Call the add_parameters function, passing in the mock parameters object
add_parameters(parameters)

# Write the captured parameters to a JSON file
output_file = RTP_DATA_PATH
with output_file.open("w") as f:
    json.dump(parameters.params, f, indent=4)

print(f"Parameters saved to {output_file}")
