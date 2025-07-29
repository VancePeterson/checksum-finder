import csv
import os

def list_csv_files(directory):
    files = [f for f in os.listdir(directory) if f.lower().endswith('.csv')]
    if not files:
        print("No CSV files found in the directory.")
        exit(1)
    print("Available CSV files:")
    for idx, file in enumerate(files, start=1):
        print(f"{idx}. {file}")
    return files

def select_csv_file(files, directory):
    while True:
        try:
            choice = int(input("Enter the number corresponding to the file you want to use: "))
            if 1 <= choice <= len(files):
                return os.path.join(directory, files[choice - 1])
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")

def parse_hex_input():
    user_input = input("Enter hex values separated by spaces (e.g., 0x85 0x36 0xF7): ")
    hex_pattern = []
    for val in user_input.split():
        try:
            hex_pattern.append(int(val, 16))
        except ValueError:
            print(f"Invalid hex value: {val}")
            exit(1)
    return hex_pattern

def find_all_patterns(csv_file_path, pattern):
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = []
        for row in reader:
            row_data = []
            for cell in row:
                try:
                    val = int(cell.strip(), 16)
                    row_data.append(val)
                except ValueError:
                    row_data.append(None)
            data.append(row_data)

    # Flatten and track positions
    flat_data = []
    positions = []
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            flat_data.append(val)
            positions.append((r, c))

    # Search for all matches
    matches = []
    for i in range(len(flat_data) - len(pattern) + 1):
        if flat_data[i:i + len(pattern)] == pattern:
            matches.append(positions[i])

    if matches:
        print(f"\nFound {len(matches)} match(es):")
        for r, c in matches:
            print(f"Pattern found starting at row {r + 1}, column {c + 1}")
    else:
        print("Pattern not found in the CSV.")

if __name__ == "__main__":
    input_csv_dir = os.path.join(os.path.dirname(__file__), "Input CSV")
    files = list_csv_files(input_csv_dir)
    csv_path = select_csv_file(files, input_csv_dir)
    hex_pattern = parse_hex_input()
    find_all_patterns(csv_path, hex_pattern)
