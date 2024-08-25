"""
Write code for your recursor here.

You may import library modules allowed by the specs, as well as your own other modules.
"""
import sys
from sys import argv
import socket
import time

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
    A = parts[-1]
    B = parts[-2]
    C = ".".join(parts[:-2])
    return valid_AB(A) and valid_AB(B) and valid_C(C)


def query_to_dns(server_port: int, query: str, timeout: float, server_type: str) -> str:
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(timeout)
        client_socket.connect(('localhost', server_port))
        client_socket.sendall((query + '\n').encode())
        response = client_socket.recv(1024).decode()
        client_socket.close()
        return response.strip()
    except socket.timeout:
        return "TIMEOUT\n"
    except socket.error:
        if server_type == "ROOT":
            return "FAILED TO CONNECT TO ROOT\n"
        elif server_type == "TLD":
            return "FAILED TO CONNECT TO TLD\n"
        elif server_type == "AUTH":
            return "FAILED TO CONNECT TO AUTH\n"
        else:
            return "ERROR\n"



def Recursor(domain: str, root_port: int, timeout: float):
    split_domain = domain.split(".")
    current_query = split_domain[-1]
    total_time = 0
    i = 1

    start_time = time.time()
    while i <= 3:
        if i == 1:
            current_query = split_domain[-1]
            response = query_to_dns(root_port, current_query, timeout, "ROOT")
        elif i == 2:
            current_query = split_domain[-2] + '.' + split_domain[-1]
            response = query_to_dns(root_port, current_query, timeout, "TLD")
        elif i == 3:
            current_query = domain
            response = query_to_dns(root_port, current_query, timeout, "AUTH")
        
        process_time = time.time() - start_time
        total_time += process_time
        
        if total_time > timeout:
            print("NXDOMAIN")
            return
        elif "FAILED" in response or response == "TIMEOUT\n":
            print(response.strip())
            return
        else:
            try:
                root_port = int(response)
            except ValueError:
                print("NXDOMAIN")
                return
        i += 1

    print(response)

def main(args: list[str]):
    if len(args) != 2:
        print("INVALID ARGUMENTS")
        exit(1)
    
    try:
        root_port = int(args[0])
        timeout = float(args[1])
        if (root_port < 1024 or root_port > 65535):
            print("INVALID ARGUMENTS")
            exit(1)
    except ValueError:
        print("INVALID ARGUMENTS")
        exit(1)
    
    while True:
        try:
            domain = input()
            if valid_hostname(domain):
                Recursor(domain, root_port, timeout)
            else:
                print("INVALID")
        except EOFError:
            exit(0)
        except Exception as error:
            print("INVALID")


if __name__ == "__main__":
    main(argv[1:])