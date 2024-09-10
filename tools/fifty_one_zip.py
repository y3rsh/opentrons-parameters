import csv
import os
import zipfile

# Define directory and create it if it doesn't exist
output_dir = "csv_files"
os.makedirs(output_dir, exist_ok=True)

# Generate 50 CSV files
for i in range(1, 52):
    filename = f"csv_file_{i}.csv"
    file_path = os.path.join(output_dir, filename)
    # Write the filename (without .csv extension) to the file
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([f"csv_file_{i}"])

# Create a ZIP file
zip_filename = "csv_files.zip"
with zipfile.ZipFile(zip_filename, "w") as zip_file:
    for root, dirs, files in os.walk(output_dir):
        for file_name in files:
            zip_file.write(os.path.join(root, file_name), file_name)
