def main():
    print("Paste hex values (from Excel, separated by tabs/spaces/newlines). End with an empty line:")

    hex_input = []
    while True:
        try:
            line = input()
            if line.strip() == "":
                break
            hex_input.append(line)
        except EOFError:
            break  # handles Ctrl+D to end input

    all_text = " ".join(hex_input)
    # Split on whitespace (tabs, spaces, newlines)
    hex_values = all_text.split()

    total = 0
    for val in hex_values:
        try:
            # Accept both "0x1A" and "1A"
            val = val.replace("0x", "")
            total += int(val, 16)
        except ValueError:
            print(f"⚠️ Skipping invalid hex: {val}")

    result = total % 255
    print(f"\nSum: {total} (dec)")
    print(f"Modulo 255: {result} (dec)")
    print(f"Result in hex: 0x{result:02X}")

if __name__ == "__main__":
    main()
