from pathlib import Path
import zipfile

# Define directory and create it if it doesn't exist
output_dir = Path("../example_data/csv_files")
output_dir.mkdir(parents=True, exist_ok=True)

# Generate 50 CSV files
for i in range(1, 52):
    filename = f"csv_file_{i}.csv"
    file_path = output_dir / filename
    # Write the filename with single double quotes around it
    with file_path.open(mode="w", newline="") as file:
        file.write(f'"csv_file_{i}"\n')  # Manually write the line with double quotes

# Create a ZIP file
zip_filename = Path("../example_data/csv_files.zip")
with zipfile.ZipFile(zip_filename, "w") as zip_file:
    for file_path in output_dir.iterdir():
        if file_path.is_file():
            zip_file.write(file_path, file_path.name)
