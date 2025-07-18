import csv
import os

# Configurable limits
MAX_MSG_LEN = 256
MAX_CHK_LEN = 256

def load_hex_values(csv_file):
    hex_values = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            for value in row:
                clean = value.strip().replace('\ufeff', '')
                if clean:
                    try:
                        hex_values.append(int(clean, 16))
                    except ValueError:
                        continue
    return hex_values

def interpret_checksum(bytes_list, endian='big'):
    return int.from_bytes(bytes_list, byteorder=endian)

def calculate_total_combinations(n):
    total = 0
    for start in range(n):
        max_msg_len = min(MAX_MSG_LEN, n - start - 1)
        for msg_len in range(1, max_msg_len + 1):
            max_chk_len = min(MAX_CHK_LEN, n - start - msg_len)
            for chk_len in (2, 4):
                if chk_len > max_chk_len:
                    continue
                total += 2  # big and little endian
    return total

def scan_for_checksums(data, output_file):
    n = len(data)
    total_combos = calculate_total_combinations(n)
    completed = 0

    try:
        with open(output_file, 'w') as out:
            for start in range(n):
                max_msg_len = min(MAX_MSG_LEN, n - start - 1)
                for msg_len in range(1, max_msg_len + 1):
                    max_chk_len = min(MAX_CHK_LEN, n - start - msg_len)
                    for chk_len in (2, 4):
                        if chk_len > max_chk_len:
                            continue

                        message = data[start : start + msg_len]
                        checksum_bytes = data[start + msg_len : start + msg_len + chk_len]
                        msg_sum = sum(message)

                        be = interpret_checksum(checksum_bytes, 'big')
                        le = interpret_checksum(checksum_bytes, 'little')

                        for checksum_value, endian in [(be, 'big'), (le, 'little')]:
                            if msg_sum == checksum_value:
                                checksum_str = f"0x{checksum_value:0{chk_len * 2}X}"
                                hex_message = [f"0x{byte:02X}" for byte in message]
                                out.write(
                                    f"Index: {start}, Length: {msg_len}, Message: {hex_message}, Checksum: {checksum_str} ({endian})\n"
                                )
                        completed += 2

                        if completed % 1_000_000 == 0 or completed == total_combos:
                            percent = (completed / total_combos) * 100
                            print(f"Progress: {percent:.2f}%", end='\r')
    except KeyboardInterrupt:
        print(f"\nInterrupted! Processed {completed:,} / {total_combos:,} combinations ({(completed / total_combos) * 100:.2f}%)")
        print("Results written so far saved to:", output_file)

if __name__ == "__main__":
    input_csv = "hex_input.csv"
    output_file = "results.txt"

    if not os.path.exists(input_csv):
        print(f"Error: Input file '{input_csv}' not found.")
    else:
        hex_data = load_hex_values(input_csv)
        print(f"Loaded {len(hex_data)} hex values")
        scan_for_checksums(hex_data, output_file)
