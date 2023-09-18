#!/usr/bin/env python3

import argparse
import os

CONFIG_FILE = "/path/to/config.conf"

def read_records():
    with open(CONFIG_FILE, 'r') as f:
        return [line.strip() for line in f.readlines()]

def write_records(records):
    with open(CONFIG_FILE, 'w') as f:
        for record in records:
            f.write(record + '\n')

def add_record(name, record_type, data):
    records = read_records()
    record_str = f'local-data: "{name} {record_type} {data}"'

    duplicates = [record for record in records if name in record and record_type in record]

    if duplicates:
        overwrite = input(f"Duplicate found for {name} {record_type}. Overwrite? (Y/n): ").strip().lower()
        if overwrite in ["y", ""]:
            records = [record for record in records if record != duplicates[0]]
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage DNS records.')
    parser.add_argument('-a', '--add', action='store_true', help='Add a record.')
    parser.add_argument('-D', '--delete', action='store_true', help='Delete a record.')
    parser.add_argument('--name', type=str, required=True, help='Name for the record.')
    parser.add_argument('--type', type=str, help='Type of the record (e.g. A, MX). Required for adding.')
    parser.add_argument('--data', type=str, help='Data for the record. Required for adding.')

    args = parser.parse_args()

    if args.add and args.delete:
        print("Error: -a (add) and -D (delete) options are mutually exclusive.")
        exit(1)

    if args.add:
        if not args.type or not args.data:
            print("Error: --type and --data are required for adding a record.")
            exit(1)
        add_record(args.name, args.type.upper(), args.data)
    elif args.delete:
        delete_records(args.name)
