import csv
import os
import json

# Configurable limits
MAX_MSG_LEN = 256
MAX_CHK_LEN = 256
DEFINED_MSGS_FILE = "message_structures.json"

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

def load_defined_messages(path):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list) and all(isinstance(entry, dict) for entry in data):
                return data
            else:
                raise ValueError("Invalid structure in message_structures.json")
    except Exception as e:
        print(f"Error loading message definitions: {e}")
        return []

def parse_hex_list(hex_list):
    return [int(x, 16) if isinstance(x, str) and x.startswith("0x") else x for x in hex_list]

def calculate_defined_checksum(data, method):
    ctype = method.get("type", "additive")
    if ctype == "additive":
        total = sum(data)
        mod = method.get("mod", 256)
        correction = method.get("correction", 0)
        return (total + correction) % mod
    elif ctype == "xor":
        result = method.get("seed", 0)
        for b in data:
            result ^= b
        return result % 256
    else:
        raise ValueError(f"Unsupported checksum type: {ctype}")

def match_message(data, structure):
    header = parse_hex_list(structure["header"])
    if data[:len(header)] != header:
        return False

    data_len = structure["data_length"]
    expected_end = len(header) + data_len
    if len(data) < expected_end + 1:
        return False

    include_header = structure["checksum"].get("include_header", False)
    start = 0 if include_header else len(header)
    payload = data[start:expected_end]

    checksum = data[expected_end]
    calc = calculate_defined_checksum(payload, structure["checksum"])
    return checksum == calc

def scan_for_checksums(data, output_file):
    n = len(data)
    total_combos = calculate_total_combinations(n)
    completed = 0

    defined_output_file = "results_defined.txt"
    defined_messages = load_defined_messages(DEFINED_MSGS_FILE)

def extract_sequenced_blocks(data, start_index, block_size=8, counter_start=0x40, counter_end=0x7F, end_marker=0xF0):
    blocks = []
    i = start_index
    expected_counter = counter_start

    while i < len(data):
        if data[i] == end_marker:
            break  # Stop when reaching 0xF0 marker

        if data[i] == expected_counter:
            if i + block_size < len(data):
                block = data[i + 1: i + 1 + block_size]
                blocks.append((expected_counter, block))
                i += block_size + 1
                expected_counter += 1
                if expected_counter > counter_end:
                    expected_counter = counter_start
            else:
                break
        else:
            i += 1
    return blocks

def scan_for_checksums(data, output_file):
    n = len(data)
    total_combos = calculate_total_combinations(n)
    completed = 0

    defined_output_file = "results_defined.txt"
    defined_messages = load_defined_messages(DEFINED_MSGS_FILE)

    try:
        with open(output_file, 'w') as out, open(defined_output_file, 'w') as def_out:
            for start in range(n):
                # Check defined messages
                for struct in defined_messages:
                    header_len = len(struct["header"])
                    msg_len = header_len + struct["data_length"] + 1  # +1 for checksum
                    if start + msg_len <= n:
                        chunk = data[start:start + msg_len]
                        if match_message(chunk, struct):
                            hex_chunk = [f"0x{b:02X}" for b in chunk]
                            def_out.write(f"Matched {struct['name']} at index {start}: {hex_chunk}\n")

                            # Extract blocks starting after this defined message
                            block_start = start + msg_len
                            blocks = extract_sequenced_blocks(data, block_start)

                            for count, block in blocks:
                                hex_block = [f"0x{b:02X}" for b in block]
                                def_out.write(f"  Block 0x{count:02X}: {hex_block}\n")

                # Original brute-force checksum scanning
                max_msg_len = min(MAX_MSG_LEN, n - start - 1)
                for msg_len in range(1, max_msg_len + 1):
                    max_chk_len = min(MAX_CHK_LEN, n - start - msg_len)
                    for chk_len in (2, 4):
                        if chk_len > max_chk_len:
                            continue

                        message = data[start: start + msg_len]
                        checksum_bytes = data[start + msg_len: start + msg_len + chk_len]
                        msg_sum = sum(message)

                        be = interpret_checksum(checksum_bytes, 'big')
                        le = interpret_checksum(checksum_bytes, 'little')

                        for checksum_value, endian in [(be, 'big'), (le, 'little')]:
                            if msg_sum == checksum_value and checksum_value != 0:
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
    input_csv = "Input CSV/stock_to_stock3.csv"
    # input_csv = "test.csv"
    output_file = "Output CSV/results.txt"

    if not os.path.exists(input_csv):
        print(f"Error: Input file '{input_csv}' not found.")
    else:
        hex_data = load_hex_values(input_csv)
        print(f"Loaded {len(hex_data)} hex values")
        scan_for_checksums(hex_data, output_file)
