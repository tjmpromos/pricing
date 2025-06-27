import json
import math
import glob
import argparse
import sys

# Utility functions for professional output formatting
def print_success(message):
    """Print success message with checkmark"""
    print(f"✓ {message}")

def print_error(message):
    """Print error message with X mark"""
    print(f"✗ {message}")

def print_warning(message):
    """Print warning message with warning symbol"""
    print(f"⚠ {message}")

def print_info(message):
    """Print info message with info symbol"""
    print(f"ℹ {message}")

def print_header(message, width=60):
    """Print a professional header"""
    print(f"\n{'='*width}")
    print(f"{message:^{width}}")
    print(f"{'='*width}")

def print_subheader(message, width=50):
    """Print a subheader"""
    print(f"\n{'-'*width}")
    print(f"{message}")
    print(f"{'-'*width}")

def parse_percentage(percentage_str):
    """Parse percentage string and return decimal multiplier

    Args:
        percentage_str (str): Percentage like '6%', '-1.5%', '6', '-1.5'

    Returns:
        float: Decimal multiplier (e.g., 6% -> 1.06, -1.5% -> 0.985)

    Raises:
        ValueError: If percentage string is invalid
    """
    try:
        # Strip whitespace
        clean_str = percentage_str.strip()

        # Check if it ends with exactly one % symbol
        if clean_str.endswith('%'):
            # Ensure there's only one % at the end
            if clean_str.count('%') != 1:
                raise ValueError("Multiple % symbols found")
            # Remove the single % symbol
            clean_str = clean_str[:-1]

        # Convert to float
        percentage_value = float(clean_str)

        # Convert percentage to multiplier (e.g., 6% -> 1.06, -1.5% -> 0.985)
        multiplier = 1 + (percentage_value / 100)

        return multiplier

    except ValueError:
        raise ValueError(f"Invalid percentage format: '{percentage_str}'. Use formats like '6%', '-1.5%', '6', or '-1.5'")

def update_pricing_file(filename, percentage_multiplier=1.06):
    """Update prices in a JSON pricing file by specified percentage for pricable tiers only, ceiling up to avoid fractional cents

    Args:
        filename (str): Path to the JSON pricing file
        percentage_multiplier (float): Multiplier to apply to prices (e.g., 1.06 for 6% increase, 0.985 for -1.5% decrease)
    """

    # Calculate the percentage change for display
    percentage_change = (percentage_multiplier - 1) * 100
    change_sign = "+" if percentage_change >= 0 else ""

    # Read the JSON file
    with open(filename, 'r') as f:
        data = json.load(f)

    # Get the pricable tiers
    pricable_tiers = data.get('pricable', [])
    print_info(f"Pricable tiers: {', '.join(pricable_tiers)}")
    print_info(f"Applying {change_sign}{percentage_change:.1f}% price change")

    # Update prices in rows
    if 'rows' in data:
        for row in data['rows']:
            size = row.get('size', 'Unknown size')
            print(f"\n📊 Updating row: {size}")
            for tier in pricable_tiers:
                if tier in row and isinstance(row[tier], (int, float)):
                    old_price = row[tier]
                    # Apply percentage change
                    new_price = old_price * percentage_multiplier
                    # Ceiling to avoid fractional cents
                    new_price_ceiled = math.ceil(new_price * 100) / 100
                    row[tier] = new_price_ceiled
                    print(f"  ${old_price:.2f} → ${new_price_ceiled:.2f} ({tier})")

    # Write back to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    print_success(f"Updated {filename} successfully!")

def get_matching_files(keywords=None):
    """Get all JSON files that match the keywords"""
    json_files = glob.glob('*.json')

    if keywords is None:
        # No keywords provided - return all JSON files with safety warning
        print_warning("No keywords provided - this will apply to ALL JSON files in the directory!")
        print_info(f"Found {len(json_files)} JSON files total")
        return sorted(json_files)

    matching_files = []
    for file in json_files:
        for keyword in keywords:
            if keyword in file:
                matching_files.append(file)
                break

    return sorted(matching_files)

def interactive_file_selection(matching_files):
    """Allow user to interactively select which files to process"""
    print_header("FILE SELECTION")
    print_info(f"Found {len(matching_files)} matching files:")

    for i, file in enumerate(matching_files, 1):
        print(f"  {i:2d}. {file}")

    print(f"\n📋 Select files to process:")
    print(f"  • Enter file numbers separated by commas (e.g., 1,3,5)")
    print(f"  • Enter 'all' to process all files")
    print(f"  • Enter 'none' or 'quit' to exit")

    while True:
        selection = input(f"\nYour selection: ").strip().lower()

        if selection in ['none', 'quit', 'exit']:
            return []

        if selection == 'all':
            return matching_files

        try:
            # Parse comma-separated numbers
            indices = [int(x.strip()) for x in selection.split(',')]
            selected_files = []

            for idx in indices:
                if 1 <= idx <= len(matching_files):
                    selected_files.append(matching_files[idx - 1])
                else:
                    print_error(f"Invalid file number: {idx}")
                    break
            else:
                return selected_files

        except ValueError:
            print_error("Invalid input. Please enter numbers separated by commas, 'all', or 'none'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Update pricing in JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py -p 6 --keywords dog-tag          # 6% increase
  python script.py -p 6% --keywords dog-tag         # 6% increase
  python script.py -p=-6% --keywords dog-tag        # 6% decrease
  python script.py --percent=-1.5% --keywords dog-tag  # 1.5% decrease
  python script.py --percent -1.5 --keywords dog-tag   # 1.5% decrease
        """)

    # Use --percent/-p flag to avoid confusion with negative numbers
    parser.add_argument('-p', '--percent', required=True,
                       help='Percentage change (e.g., "6", "6%%", "-6%%", "-1.5")')
    parser.add_argument('--files', nargs='*', help='Specific files to process')
    parser.add_argument('--all', action='store_true', help='Process all matching files without confirmation')
    parser.add_argument('--list', action='store_true', help='List matching files and exit')
    parser.add_argument('--keywords', nargs='*',
                       help='Keywords to match in filenames (if not provided, applies to all JSON files with safety warning)')

    args = parser.parse_args()

    # Parse the percentage argument
    try:
        percentage_multiplier = parse_percentage(args.percent)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)

    # Get all matching files (only call this if we need to determine files by keywords)
    if args.files:
        # When specific files are provided, we don't need to use keywords
        matching_files = []
    else:
        # Only use keyword matching when not using specific files
        matching_files = get_matching_files(args.keywords)

    if args.list:
        print_header("MATCHING FILES")
        print_info(f"Found {len(matching_files)} matching files:")
        for file in matching_files:
            print(f"  • {file}")
        sys.exit(0)

    # Determine which files to process
    if args.files:
        # Process specific files provided via command line
        files_to_process = []
        for file in args.files:
            # Check if file exists
            import os
            if os.path.exists(file):
                files_to_process.append(file)
            else:
                print_warning(f"{file} not found or doesn't exist")

    elif args.all:
        # Process all matching files
        files_to_process = matching_files

    else:
        # Interactive selection
        files_to_process = interactive_file_selection(matching_files)

    if not files_to_process:
        print_warning("No files selected for processing.")
        sys.exit(0)

    print_subheader(f"SELECTED FILES ({len(files_to_process)})")
    for file in files_to_process:
        print(f"  ✓ {file}")

    # Confirm before processing
    if not args.all and len(files_to_process) > 1:
        confirm = input(f"\nProceed with updating {len(files_to_process)} files? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print_warning("Operation cancelled.")
            sys.exit(0)

    print_header("PRICE UPDATE PROCESS")

    # Update selected files
    for i, filename in enumerate(files_to_process, 1):
        print_subheader(f"Processing {filename} ({i}/{len(files_to_process)})")
        try:
            update_pricing_file(filename, percentage_multiplier)
        except Exception as e:
            print_error(f"Failed to process {filename}: {e}")
            continue

    print_header("PROCESS COMPLETED")
    print_success(f"Successfully processed {len(files_to_process)} files!")
    print(f"\n🎉 All price updates have been completed successfully!")