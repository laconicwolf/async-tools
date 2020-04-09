#!/usr/bin/env python3


__author__ = 'Jake Miller (@LaconicWolf)'
__date__ = '20200409'
__version__ = '0.01'
__description__ = '''A fast web scanner that pulls title and server information'''


import sys
if sys.version < "3.5":
    print('[-] This script requires at least Python 3.5. Sorry.')
    exit()

import re
import random
import ipaddress
import argparse
import os
import itertools
import time
from urllib.parse import urlparse

# Third party modules
missing_modules = []
try:
    import asyncio
    import aiohttp
    import tqdm
except ImportError as e:
    missing_module = str(e).split(' ')[-1]
    missing_modules.append(missing_module)

if missing_modules:
    for m in missing_modules:
        print('[-] Missing module: {}'.format(m))
        print('[*] Try running "python3 -m pip install {}", or do an Internet search for installation instructions.\n'.format(m.strip("'")))
    exit()


def validate_input_data(data: str) -> str:
    """Checks if input data is in the proto://addr:port format."""
    parsed_url = urlparse(data)
    if bool(parsed_url.scheme):
        if ":" in parsed_url.netloc and parsed_url.netloc.split(':')[-1].isdigit():
            url = data
        else:
            if parsed_url.scheme == 'https':
                url = data + ':443'
            elif parsed_url.schema == 'http':
                url = data + ':80'
            else:
                print(f'[-] Invalid protocol: {data}. Please specify HTTP or HTTPS. (https://example.com). Skipping URL.')
                url = ''
    else:
        print(f'[-] Invalid protocol: {data}. Please specify HTTP or HTTPS. (https://example.com). Skipping URL.')
        url = ''
    return url


def get_random_useragent() -> str:
    """Returns a randomly chosen User-Agent string."""
    win_edge = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randrange(40,50)}.0.{random.randrange(1000,4000)}.{random.randrange(0,999)} Safari/{random.randrange(530,600)}.{random.randrange(0,99)} Edge/12.{random.randrange(0,999)}'
    win_firefox = f'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/2010{random.randrange(0,9999)} Firefox/{random.randrange(41,60)}.{random.randrange(0,99)}'
    win_chrome = f"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randrange(65,99)}.{random.randrange(0,9)}.{random.randrange(1000,4000)}.84 Safari/{random.randrange(540,599)}.36"
    lin_firefox = f'Mozilla/5.0 (X11; Linux i686; rv:30.0) Gecko/2010{random.randrange(0,9999)} Firefox/{random.randrange(41,60)}.{random.randrange(0,99)}'
    mac_chrome = f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randrange(40,99)}.0.{random.randrange(1000,4000)}.38 Safari/537.36'
    ie = f'Mozilla/4.0 (compatible; MSIE 6.{random.randrange(0,1)}; Windows NT 5.0)'
    ua_dict = {
        1: win_edge,
        2: win_firefox,
        3: win_chrome,
        4: lin_firefox,
        5: mac_chrome,
        6: ie
    }
    rand_num = random.randrange(1, (len(ua_dict) + 1))
    return ua_dict[rand_num]


async def fetch_all(urls: list):
    """Launch requests for all web pages. Adapted from: 
    https://gist.github.com/dmahugh/b043ecbc4c61920aa685e0febbabb959
    """
    tasks = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            task = asyncio.ensure_future(fetch(url, session))
            tasks.append(task) # create list of tasks
        _ = await asyncio.gather(*tasks) # gather task responses


async def fetch(url: str, session):
    """Fetch a url, using specified ClientSession. Adapted from:
    https://gist.github.com/dmahugh/b043ecbc4c61920aa685e0febbabb959
    """

    # Sets the timeout so connections don't slow things down
    timeout = aiohttp.ClientTimeout(sock_connect=args.timeout)

    # Sets a random user agent if specified, else just uses the default
    # aiohttp agent.
    if args.random_agent:
        headers = {'User-Agent': get_random_useragent()}
    else:
        headers = None

    # This is some ugly repeat code, but I don't know how else to do 
    # it yet with the proxy. 
    if args.proxy:
        try:
            async with session.get(url, timeout=timeout, ssl=False, proxy=my_proxy, headers=headers) as response:
                
                # Gets the data I plan on keeping, parses a few things, and then appends
                # everything to the Global data variable.
                request_url = url
                response_status_code = response.status
                redirect = 'True' if response.history else 'False'
                response_url = response.url
                response_headers = response.headers
                response_text = await response.text()
                server_header = get_server_header(response_headers)
                site_title = get_html_title(response_text)
                data.append([
                    request_url,
                    response_status_code,
                    redirect,
                    response_url,
                    server_header,
                    site_title
                ])
                p_item = format_for_printing([request_url, response_status_code, redirect, server_header, site_title])

                # Prints to the screen if you want.
                if not args.quiet:
                    print(f"{p_item[0]:45}{p_item[1]:10}{p_item[2]:10}{p_item[3]:25}{p_item[4]:20}")
        except Exception as e:
            if args.debug:
                print(f"[-] {url}: {e}")
            else:
                pass
    
    # Same as above...
    else:
        try:
            async with session.get(url, timeout=timeout, ssl=False, headers=headers) as response:
                request_url = url
                response_status_code = response.status
                redirect = 'True' if response.history else 'False'
                response_url = response.url
                response_headers = response.headers
                response_text = await response.text()
                server_header = get_server_header(response_headers)
                site_title = get_html_title(response_text)
                data.append([
                    request_url,
                    response_status_code,
                    redirect,
                    response_url,
                    server_header,
                    site_title
                ])
                p_item = format_for_printing([request_url, response_status_code, redirect, server_header, site_title])
                if not args.quiet:
                    print(f"{p_item[0]:45}{p_item[1]:10}{p_item[2]:10}{p_item[3]:25}{p_item[4]:20}")
        except Exception as e:
            if args.debug:
                print(f"[-] {url}: {e}")
            else:
                pass

    # Updates the progress bar
    if args.quiet:
        p_bar.update(counter + 1)


def get_html_title(contents: str) -> str:
    """Uses regex to parse the title from the HTML content."""
    try:
        title = re.findall(r'<title.*?>(.+?)</title>', contents, re.IGNORECASE)[0]
    except Exception as e:
        title = ''
    return title


def make_async_requests(urls: list):
    """Fetch list of web pages asynchronously."""
    loop = asyncio.get_event_loop() # event loop
    future = asyncio.ensure_future(fetch_all(urls)) # tasks to do
    loop.run_until_complete(future) # loop until done


def format_for_printing(data: list) -> list:
    """Iterates through items in a list and truncates the strings if
    they are greater than a certain length.
    """
    items = []
    for item in data:
        item = str(item)
        if len(item) >= 50:
            items.append(item[:47] + '...')
        else:
            items.append(item)
    return items


def get_server_header(headers: str) -> str:
    """Returns the HTTP response server header if present, else 
    returns an empty string.
    """
    server_header = headers.get('Server')
    return server_header


def main():
    """Makes asynchronous HTTP(S) requests and records basic information
    including URL, status code, server header, and title. 
    """

    # Makes sure the URLs specify HTTP or HTTPS and has or port
    # or a port is added, default 80 for HTTP or 443 for HTTPS
    urls = [validate_input_data(i) for i in input_data]
    urls = [u for u in urls if u != '']
    
    # Exits if no URLs pass validation
    if not urls: exit()

    # A hack for Windows. Limits to 1500 connections at a time. Otherwise,
    # you'll get this error: ValueError: too many file descriptors in select().
    # This script is faster on non Windows platforms.
    if len(urls) > limit and sys.platform == 'win32':
        while True:
            current_data = urls[:limit]
            make_async_requests(current_data)
            urls[:limit] = []
            if len(urls) == 0:
                break
    else:
        make_async_requests(urls)

    # Write data to CSV
    if args.append:
        with open(csv_name, 'a', encoding="utf-8") as fh:
            for item in data:
                fh.write(f"{item[0]},{item[1]},{item[2]},{item[3]},{item[4]},{item[5]}\n")
    else:
        with open(csv_name, 'w', encoding="utf-8") as fh:
            fh.write("Requested URL,Response Code,isRedirect,Response URL,Server Header,Title\n")
            for item in data:
                fh.write(f"{item[0]},{item[1]},{item[2]},{item[3]},{item[4]},{item[5]}\n")

    print()
    print(f"[+] Results written to {csv_name}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--csv",
        nargs='?',
        default='results.csv',
        help="Specify the name of a csv file to write to."
    )
    parser.add_argument(
        "-r", "--random_agent",
        action="store_true",
        help="Uses a different User-Agent for each request"
    )
    parser.add_argument(
        "-p", "--proxy",
        help="Specify a proxy (http://127.0.0.1:8080)."
    )
    parser.add_argument(
        "-u", "--url",
        nargs="*",
        help="Specify URL(s) to connect."
    )
    parser.add_argument(
        "-f", "--filename",
        help="Specify a file containing URLs in proto://addr:port format."
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
    parser.add_argument(
        "--make_urls_http",
        help="Appends http:// to all input data.",
        action="store_true"
    )
    parser.add_argument(
        "--make_urls_https",
        help="Appends https:// to all input data.",
        action="store_true"
    )
    parser.add_argument(
        "--debug",
        help="Print data about exceptions",
        action="store_true"
    )
    parser.add_argument(
        "-to", "--timeout",
        nargs="?", 
        type=float, 
        default=10, 
        help="Specify number of seconds until a connection timeout (default=10)"
    )
    parser.add_argument(
        "--limit",
        nargs="?", 
        type=int, 
        default=1500, 
        help="Specify number of connections. Windows needs this, otherwise you get an error with a large amount of connections (default=1500)"
    )
    args = parser.parse_args()

    # Initialize input data
    input_data = []

    # Exits if user does not specify URLs via filename or directly
    if not args.filename and not args.url:
        parser.print_help()
        print("[-] Please specify an input file listing IP addresses "
              "and/or hostnames (-f), or specific URLs (-u)")
        exit()

    # Assigns input_data to user supplied URLs via the args.url or args.filename
    if args.url:
        input_data = args.url
    if args.filename:
        filename = args.filename
        if not os.path.exists(filename):
            parser.print_help()
            print(f"[-] The file {filename} cannot be found or you do not have "
                   "permission to open the file.")
            exit()
        with open(filename) as f:
            input_data = f.read().splitlines()


    # Assigns the name to the CSV file to be generated
    if args.csv.endswith(".csv"):
        csv_name = args.csv
    else:
        csv_name = args.csv + '.csv'

    # Proxy support
    if args.proxy:
        my_proxy = args.proxy
        if not args.proxy.startswith('http'):
            print('[-] Please specify the protocol. Example: -p http://your.proxy:port. Only HTTP proxies are currently supported by aiohttp.')
            exit()
    else:
        my_proxy = ''

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

    # Allows easy way to convert a list of IP addresses or domain names
    # to URLs. 
    if args.make_urls_http:
        input_data = ['http://' + i for i in input_data]
    if args.make_urls_https:
        input_data = ['https://' + i for i in input_data]

    # Default set to 1500, this only applies to Windows machines.
    # Limits the number of connections you can have. If you get an error,
    # you can reduce this number until you don't get the error.
    limit = args.limit
    
    # Start async wizardry
    loop = asyncio.get_event_loop()
    
    # Progress bar if you don't have things print to the screen
    if args.quiet:
        p_bar = tqdm.tqdm(range(len(input_data)))
        counter = 0

    # Global variable for output data
    data = []
    main()