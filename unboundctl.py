#!/usr/bin/env python3

import argparse
import os
from prettytable import PrettyTable

CONFIG_FILE = os.getenv("UNBOUND_CONFIG")
VALID_RECORD_TYPES = ["A", "AAAA", "CNAME", "MX", "NS", "SOA", "SRV", "TXT"]

def is_duplicate(name, record_type, records):
    return any(record for record in records if f'"{name} {record_type}' in record)

def read_records():
    if not CONFIG_FILE:
        print("Error: UNBOUND_CONFIG environment variable not set.")
        exit(1)
    
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
        exit(1)
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        print(f"Error reading from config file: {e}")
        exit(1)

def write_records(records):
    try:
        with open(CONFIG_FILE, 'w') as f:
            for record in records:
                f.write(record + '\n')
    except Exception as e:
        print(f"Error writing to config file: {e}")
        exit(1)

def list_records():
    records = read_records()
    if not records:
        print("No records found.")
        return

    table = PrettyTable(['Name', 'Type', 'Data'])
    sorted_records = []

    for record in records:
        # Extract data between quotes
        quoted_data = record.split('"')[1] if '"' in record else None
        if not quoted_data:
            print(f"Skipped malformed record: {record}")
            continue

        record_parts = quoted_data.split()
        if len(record_parts) != 3:  # We expect 'name record_type data' format
            print(f"Skipped malformed record: {record}")
            continue

        name, record_type, data = record_parts
        sorted_records.append((name, record_type, data))

    # Sort by record type
    sorted_records.sort(key=lambda x: x[1])

    for name, record_type, data in sorted_records:
        table.add_row([name, record_type, data])

    print(table)



def add_record(name, record_type, data):
    if record_type not in VALID_RECORD_TYPES:
        print(f"Invalid record type: {record_type}. Valid types are: {', '.join(VALID_RECORD_TYPES)}")
        return

    records = read_records()
    record_str = f'local-data: "{name} {record_type} {data}"'

    if is_duplicate(name, record_type, records):
        overwrite = input(f"Duplicate found for {name} {record_type}. Overwrite? (Y/n): ").strip().lower()
        if overwrite in ["y", ""]:
            records = [record for record in records if not is_duplicate(name, record_type, record)]
            records.append(record_str)
            write_records(records)
            os.system("systemctl restart unbound")
            print(f"Added and overwritten record: {name} {record_type} {data}")
        else:
            print("Duplicate not overwritten.")
    else:
        records.append(record_str)
        write_records(records)
        os.system("systemctl restart unbound")
        print(f"Added record: {name} {record_type} {data}")

def delete_records(name):
    records = read_records()
    to_delete = [record for record in records if name in record]

    if not to_delete:
        print(f"No records found for {name}.")
        return

    for record in to_delete:
        records.remove(record)

    write_records(records)
    os.system("systemctl restart unbound")
    print(f"All records for {name} removed.")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Manage DNS records.')
    parser.add_argument('-a', '--add', action='store_true', help='Add a record.')
    parser.add_argument('-D', '--delete', action='store_true', help='Delete a record.')
    parser.add_argument('--name', type=str, help='Name for the record.')
    parser.add_argument('--type', type=str, help='Type of the record (e.g. A, MX). Required for adding.')
    parser.add_argument('--data', type=str, help='Data for the record. Required for adding.')
    parser.add_argument('-l', '--list', action='store_true', help='List all records.')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()

    if args.add and args.delete:
        print("Error: -a (add) and -D (delete) options are mutually exclusive.")
        exit(1)

    if args.add:
        if not args.type or not args.data or not args.name:
            print("Error: --name, --type and --data are required for adding a record.")
            exit(1)
        add_record(args.name, args.type.upper(), args.data)

    elif args.list:
        list_records()

    elif args.delete:
        if not args.name:
            print("Error: --name is required for deleting a record.")
            exit(1)
        delete_records(args.name)
