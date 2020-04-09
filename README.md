# Async Tools
Security tools written using Python asyncio. Written for speed.

## web_requester.py
Makes HTTP requests and gets the response code, server header, and site title. Writes results to a CSV file and the terminal. Anything > ~1,500 URLs will take slightly longer on Windows when compared to other platforms.

> Request individual URL(s)
`python3 web_requester.py https://10.2.2.1:443`

> Request URLs from a file
`python3 web_requester.py -f my_10000_urls.txt`

> Request URLs from a file and suppress the output to the terminal.
`python3 web_requester.py -f my_10000_urls.txt --quiet`

## address_resolver.py
Resolves IP address or hostnames quickly. Writes results to a CSV file and the terminal.

> Resolve a range of IP addresses
`python3 address_resolver.py -r 10.10.1.0/24`

> Resolve hostnames or IP addresses from a file
`python3 address_resolver.py -f targets.txt`
