import selectors
import signal
import socket
import logging
import sys

from colorama import Fore, init
from argparse import ArgumentParser

init(autoreset=True)

class ColorfulFormatter(logging.Formatter):
    def format(self, record):
        style = {
            "DEBUG": Fore.GREEN,
            "ERROR": Fore.LIGHTRED_EX,
            "WARNING": Fore.YELLOW
        }.get(record.levelname, Fore.RESET)

        return f"{style}[+]{Fore.RESET} {super().format(record)}"



logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = ColorfulFormatter("[%(asctime)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def forward_conn(sender: socket.socket, receiver: socket.socket, addr):
    try:
        buffer = sender.recv(1024)
        if buffer:
            receiver.sendall(buffer)
        else:
            logger.warning(f"Connection closed at {addr2str(addr)}")
            selector.unregister(sender)
            selector.unregister(receiver)

            sender.close()
            receiver.close()
    except OSError as e:
        logger.warning(e)


def addr2str(addr):
    host, port = addr
    return f"{host}:{port}"


def accept_conn(sock: socket.socket):
    try:
        client, addr = sock.accept()
        logger.debug(f"Accepted connection from {addr2str(addr)}")
        client.setblocking(False)
        remote = (parsed_args.remote_host, parsed_args.remote_port)
        conn = get_remote_socket(remote)

        logger.debug(f"Tunnel created {addr2str(addr)} -> {addr2str(remote)}")
        selector.register(client, selectors.EVENT_READ, data=[forward_conn, client, conn, addr])
        selector.register(conn, selectors.EVENT_READ, data=[forward_conn, conn, client, addr])
    except ConnectionRefusedError:
        logger.error("Remote connection refused")
    except Exception as e:
        logger.error(e)


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("port", type=int, help="Listener port", metavar="PORT")
    parser.add_argument("-host", type=str , help="Listener host", metavar="HOST", default="0.0.0.0")
    parser.add_argument("-rhost", "--remote-host", type=str, metavar="REMOTE_HOST", default="localhost")
    parser.add_argument("-rport", "--remote-port", type=int, metavar="REMOTE_PORT", required=True)
    return parser.parse_args()


def get_remote_socket(addr):
    conn: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(addr)
    conn.setblocking(False)
    return conn


def set_listen_socket(sock, host):
    sock.bind((host, parsed_args.port))
    sock.setblocking(False)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.listen()


def handler(sig, frame):
    logger.warning("Keyboard Interrupted. exiting...")
    for key in list(selector.get_map().values()):
        selector.unregister(key.fileobj)
        key.fileobj.close()
    sys.exit(0)


if __name__ == "__main__":
    parsed_args = parse_arguments()

    selector = selectors.DefaultSelector()

    signal.signal(signal.SIGINT, handler)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv:

        logger.debug(f"Listening at port {parsed_args.port}")
        selector.register(serv, selectors.EVENT_READ, [accept_conn, serv])
        set_listen_socket(serv,parsed_args.host)
        while True:
            events = selector.select()
            for key, mask in events:
                callback, *args = key.data
                callback(*args)
