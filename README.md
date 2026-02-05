# Python Selectors TCP Proxy (Educational)

Educational TCP proxy built with Python `selectors`.

For educational and laboratory use only.

This project was created as a learning exercise while studying:
- socket programming
- non-blocking I/O
- event-driven networking
- proxy/relay architecture

## Features

- non-blocking sockets
- selectors event loop
- bidirectional TCP relay
- partial send handling
- graceful connection teardown
- traffic hexdump (bounded output)

## Limitations

- single session only
- no TLS support
- not production hardened
- for lab / educational use only

## Usage

```bash
python proxy.py <remote_host> <remote_port>

