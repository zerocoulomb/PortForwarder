# PortForwarder
PortForwarder is written with python language. Forwards incoming traffic to another port on the local or remote server. 

## Usage
```bash
$ python forwarder.py -rport <REMOTE PORT> -rhost <REMOTE HOST> -host <LISTEN HOST> PORT
```

## Use Case
```bash
$ python forwarder.py -rport 80 -rhost 127.0.0.1 8080

[+] 2026-02-03 13:14:37,112 Listening at port 8080
[+] 2026-02-03 13:14:59,000 Accepted connection from 127.0.0.1:40323
[+] 2026-02-03 13:14:59,000 Tunnel created 127.0.0.1:40323 -> 127.0.0.1:80
[+] 2026-02-03 13:15:08,921 Connection closed at 127.0.0.1:40323
```