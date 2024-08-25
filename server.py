"""
Write code for your server here.

You may import library modules allowed by the specs, as well as your own other modules.
"""
import socket
from sys import argv
from pathlib import Path
from typing import Dict, Any

def valid_hostname(hostname: str) -> bool:
    def valid_AB(string: str) -> bool:
        if not string:
            return False
        for char in string:
            if not (char.isalnum() or char == '-'):
                return False
        return True
    
    def valid_C(string: str) -> bool:
        if (not string or string[0] == '.' or string[-1] == '.'):
            return False
        for char in string:
            if not (char.isalnum() or char == '-' or char == '.'):
                return False
        return True

    parts = hostname.split('.')
    if len(parts) >= 3:
        A = parts[-1]
        B = parts[-2]
        C = ".".join(parts[:-2])
        return valid_AB(A) and valid_AB(B) and valid_C(C)
    elif len(parts) == 2:
        A = parts[-1]
        B = parts[-2]
        return valid_AB(A) and valid_AB(B)
    elif len(parts) == 1:
        return valid_AB(parts[-1])

def load_config(config_file: str) -> int:
    records = {}
    try:
        with open(config_file, 'r') as file:
            lines = file.readlines()
            port = int(lines[0].strip())
            for line in lines[1:]:
                domain, domain_port = line.strip().split(',')
                if not valid_hostname(domain):
                    print("INVALID CONFIGURATION")
                    exit(1)
                if (domain in records) and (records[domain] != domain_port):
                    print("INVALID CONFIGURATION")
                    exit(1)
                records[domain] = domain_port
            return port, records
    except FileNotFoundError:
        print("INVALID CONFIGURATION")
        exit(1)
    except IndexError:
        print("INVALID CONFIGURATION")
        exit(1)
    except ValueError:
        print("INVALID CONFIGURATION")

def handle_query(domain: str, records: Dict[str, Any], client_socket: socket.socket) -> None:
    if domain in records:
        client_socket.sendall((str(records[domain]) + '\n').encode())
        print(f"resolve {domain} to {records[domain]}")
    else:

        client_socket.sendall("NXDOMAIN\n".encode())
        print(f"resolve {domain} to NXDOMAIN")


def command(command_str: str, records: Dict[str, Any], client_socket: socket.socket) -> None:
    if command_str == '!EXIT':
        client_socket.close()
        return False
    elif command_str.startswith('!ADD'):
        a, domain, port_id = command_str.split()
        records[domain] = int(port_id)
    elif command_str.startswith('!DEL'):
        a, domain = command_str.split()
        if domain in records:
            del records[domain]
    else:
        print("INVALID")

def request(client_socket: socket.socket, address, set, records) -> None:
    data = client_socket.recv(1024).decode()

    message = data.split("\n")[0]
    data = data.split("\n", 1)[1]

    if message.startswith('!'):
        if command(message, records, client_socket) == False:
            return False
    else:
        handle_query(message, records, client_socket)
    client_socket.close()

def run_server(port: int, records: Dict[str, Any]) -> None:
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', port))
        server_socket.listen()
        set = {}

        while True:
            client_socket, address = server_socket.accept()
            if request(client_socket, address, set, records) == False:
                break
    except PermissionError:
        print("INVALID CONFIGURATION")
        exit(1)
    except OSError as e:
        if e.errno == 98:
            print("address already in use")
            exit(1)
        else:
            raise e
        
def main(args: list[str]) -> None:
    if len(args) != 1:
        print("INVALID ARGUMENTS")
        exit(1)

    config_file = args[0]
    if not Path(config_file).exists():
        print("INVALID CONFIGURATION")
        exit(1)

    port, records = load_config(config_file)
    run_server(port, records)

if __name__ == "__main__":
    main(argv[1:])