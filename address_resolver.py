#!/usr/bin/env python3


__author__ = 'Jake Miller and Ivan DaSilva.'
__date__ = '20200325'
__version__ = '0.01'
__description__ = '''A tool that takes a list of IP addresses or hostnames and tries to resolve them.'''


import sys
if sys.version < "3.5":
    print('[-] This script requires at least Python 3.5. Sorry.')
    exit()

import re
import ipaddress
import socket
import argparse
import os
import itertools
import time

# Third party modules
missing_modules = []
try:
    import asyncio
    import aiodns
except ImportError as error:
    missing_module = str(error).split(' ')[-1]
    missing_modules.append(missing_module)

if missing_modules:
    for m in missing_modules:
        print(f'[-] Missing module: {m}')
        print('[*] Try running "pip3 install {}", or do an Internet search for installation instructions.'.format(m.strip("'")))
    exit()


def ip_range(input_string: str) -> list: 
    """Accepts a dash specified range and returns a list of ip addresses
    within that range. Adapted from:
    https://stackoverflow.com/questions/20525330/python-generate-a-list-of-ip-addresses-from-user-input
    """
    octets = input_string.split('.')
    chunks = [list(map(int, octet.split('-'))) for octet in octets]
    ranges = [range(c[0], c[1] + 1) if len(list(c)) == 2 else c for c in chunks]
    addrs = ['.'.join(list(map(str, address))) for address in itertools.product(*ranges)]
    return addrs


def cidr_ip_range(input_string: str) -> list:
    """Accepts a CIDR range and returns a list of ip addresses
    within the CIDR range.
    """
    addr_obj = ipaddress.ip_network(input_string)
    addrs = [str(addr) for addr in addr_obj.hosts()]
    return addrs


def validate_input_data(data: list) -> tuple:
    """Iterates through a list of input data to check for IP addresses and
    hostnames. Returns a tuple of IP addresses and hostnames.
    """
    # Intialize the return variables
    ip_addresses = []
    hostnames = []
    invalid_entries = []

    for item in data:
        if item[0].isdigit():

            # Check if IPv4 address
            pattern = r"^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$"
            match = re.match(pattern, item)
            if (match):
                try:
                    ipaddress.IPv4Network(item)
                    ip_addresses.append(item)
                except Exception as e:
                    invalid_entries.append(item)
            else:
                hostnames.append(item)
        else:
            hostnames.append(item)
    return ip_addresses, hostnames, invalid_entries


async def find_ipaddress(hostname: str):
    """Takes a hostname and attempts to resolve an IP address."""
    try:
        resolver = aiodns.DNSResolver(timeout=1)
        result = await resolver.gethostbyname(hostname, socket.AF_INET)
        ip = result.addresses[0]
    except Exception as e:
        ip = "Unable to resolve"
    resolved_data.append((ip, hostname))
    if not args.quiet:
        print(f"{ip:20}{hostname:20}")


async def find_all_ipaddrs(hostnames: list):
    """Takes a list of hostnames and attempts to resolve the IP 
    addresses.
    """
    tasks = []
    for hostname in hostnames:
        task = asyncio.ensure_future(find_ipaddress(hostname))
        tasks.append(task)
    await asyncio.gather(*tasks, return_exceptions=True)


async def find_hostname(ip_addr: str):
    """Takes an IP address and attempts to resolve the hostname."""
    try:
        resolver = aiodns.DNSResolver(timeout=0.5)
        result = await resolver.gethostbyaddr(ip_addr)
        host_name = result.name
    except Exception as e:
        host_name = "Unable to resolve"
    if not args.quiet:
        print(f"{ip_addr:20}{host_name:20}")
    resolved_data.append((ip_addr, host_name))


async def find_all_hosts(ip_addrs: list):
    """Takes a list of IP address and attempts to resolve the 
    hostnames.
    """
    tasks = []
    for ip_addr in ip_addrs:
        task = asyncio.ensure_future(find_hostname(ip_addr))
        tasks.append(task)
    await asyncio.gather(*tasks, return_exceptions=True)


def main():
    # Windows will error out if it has a certain number of hosts, so
    # this takes 500 hosts at a time until complete.
    if len(input_data) > 500 and sys.platform == 'win32':
        while True:
            current_data = input_data[:500]
            ipaddresses,hostnames,invalid_entries = validate_input_data(current_data)
            asyncio.run(find_all_hosts(ipaddresses))
            asyncio.run(find_all_ipaddrs(hostnames))
            input_data[:500] = []
            if len(ipaddresses) == 0 and len(hostnames) == 0:
                break
    else:
        ipaddresses,hostnames,invalid_entries = validate_input_data(input_data)
        asyncio.run(find_all_hosts(ipaddresses))
        asyncio.run(find_all_ipaddrs(hostnames))
    
    if args.append:
        with open(csv_name, 'a') as fh:
            fh.write("IP Address,Hostname\n")
            for data in resolved_data:
                fh.write(f"{data[0]},{data[1]}\n")
    else:
        with open(csv_name, 'w') as fh:
            fh.write("IP Address,Hostname\n")
            for data in resolved_data:
                fh.write(f"{data[0]},{data[1]}\n")

    print(f"[+] Results written to {csv_name}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # TODO
    parser.add_argument(
        "-csv", "--csv",
        nargs='?',
        default='results.csv',
        help="Specify the name of a csv file to write to."
    )
    parser.add_argument(
        "-r", "--range",
        help="Specify the network range (10.10.10.0/24 or 10.10.10.20-40)."
    )
    parser.add_argument(
        "-f", "--filename",
        help="Specify a file containing hostnames or IP addresses."
    )
    parser.add_argument(
        "-q", "--quiet",
        help="Suppresses output to the terminal. CSV will still be created.",
        action="store_true"
    )
    parser.add_argument(
        "-a", "--append",
        help="Will write to the CSV file in append mode.",
        action="store_true"
    )
    args = parser.parse_args()

    if not args.filename and not args.range:
        parser.print_help()
        print("[-] Please specify an input file listing IP addresses "
              "and/or hostnames (-f) or a range of IP address (-r).")
        exit()

    # Initialize input data
    input_data = []

    if args.filename:
        filename = args.filename
        if not os.path.exists(filename):
            parser.print_help()
            print(f"[-] The file {filename} cannot be found or you do not have "
                   "permission to open the file.")
            exit()
        with open(filename) as f:
            input_data = f.read().splitlines()

    if args.range:
        if not '-' in args.range and not '/' in args.range:
            if sys.version.startswith('3'):
                parser.print_help()
                print("[-] Please either specify a CIDR range or an octet range with a dash ('-').")
                exit()
            else:
                parser.print_help()
                print("[-] Please specify an octet range with a dash ('-').")
                exit()

        # https://www.regextester.com/93987
        cidr_regex = r'^([0-9]{1,3}\.){3}[0-9]{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$'

        # adapted from https://stackoverflow.com/questions/10086572/ip-address-validation-in-python-using-regex
        dash_regex = r'^[\d+-?]{1,7}\.[\d+-?]{1,7}\.[\d+-?]{1,7}\.[\d+-?]{1,7}$'

        if '-' in args.range:
            if '/' in args.range:
                print("[-] Please either use CIDR notation or specify octet range with a dash ('-'), not both.")
                exit()
            if not re.findall(dash_regex, args.range):
                parser.print_help()
                print('[-] Invalid IP range detected. Please try again.')
                exit()
            ip_addrs = ip_range(args.range)

            # Additional validation to dump any octet larger than 255
            for addr in ip_addrs:
                octets = str(addr).split('.')
                invalid_addr = [octet for octet in octets if int(octet) > 255]
                if invalid_addr:
                    continue
                input_data.append(addr)
        elif '/' in args.range:
            try:
                if not re.findall(cidr_regex, args.range):
                    parser.print_help()
                    print('[-] Invalid CIDR range detected. Please try again.')
                    exit()
                input_data = cidr_ip_range(args.range)
            except ValueError as error:
                parser.print_help()
                print('[-] Invalid CIDR range detected. Please try again.')
                print(f'[-] {error}')
                exit()

    if args.csv.endswith(".csv"):
        csv_name = args.csv
    else:
        csv_name = args.csv + '.csv'

    # Print banner
    print()
    word_banner = '{} version: {}. Coded by: {}'.format(sys.argv[0].title()[:-3], __version__, __author__)
    print('=' * len(word_banner))
    print(word_banner)
    print('=' * len(word_banner))
    print()
    time.sleep(1)

    # Remove duplicates from the list
    input_data = list(set(input_data))
    
    # Start async wizardry
    loop = asyncio.get_event_loop()
    
    # TODO
    resolved_data = []

    main()