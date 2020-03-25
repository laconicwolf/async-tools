# Async Tools
Security tools written using Python asyncio. Written for speed.

## address_resolver.py
Resolves IP address or hostnames quickly. Writes results to a CSV file and the terminal.

> Resolve a range of IP addresses
`python3 address_resolver.py -r 10.10.1.0/24`

> Resolve hostnames or IP addresses from a file
`python3 address_resolver.py -f targets.txt`
