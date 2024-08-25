"""
Write code for your launcher here.

You may import library modules allowed by the specs, as well as your own other modules.
"""
from sys import argv
from pathlib import Path
import random
from typing import Tuple, List

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
    
def generate_filename(directory: Path) -> Path:
    while True:
        name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        potential_filename = directory / f"{name}.conf"
        if not potential_filename.exists():
            return potential_filename

def save_config(directory: Path, port: int, records: List[Tuple[str, int]]) -> int:
    filename = generate_filename(directory)
    try:
        with filename.open('w') as f:
            f.write(f"{port}\n")
            for record in records:
                f.write(f"{record[0]},{record[1]}\n")

    except Exception as e:
        print("Error in saveconfig")
    return port+1

def valid_master(master_path: Path) -> bool:
    if not master_path.exists():
        print("INVALID MASTER")
        return False

    with master_path.open() as file:
        lines = file.readlines()

    if len(lines) - 1 > 21504:
        print("INVALID MASTER")
        return False

    try:
        port = int(lines[0].strip())
        if port < 1024 or port > 65535:
            print("INVALID MASTER")
            return False
    except ValueError:
        print("INVALID MASTER")
        return False

    records = {}
    for line in lines[1:]:
        try:
            domain, port_id = line.strip().split(',')
            if not is_subdomain(domain):
                print("INVALID MASTER")
                return False
            try:
                port = int(port_id)
                if port < 1024 or port > 65535:
                    print("INVALID MASTER")
                    return False
            except ValueError:
                return False
            
            if not valid_hostname(domain):
                print("INVALID MASTER")
                return False
            elif domain in records and records[domain] != port_id:
                print("INVALID MASTER")
                return False

            records[domain] = port_id

        except ValueError:
            print("INVALID MASTER")
            return False

    return True

def launcher(master_file: str, output_directory: str) -> None:
    master_path = Path(master_file)
    dir_path = Path(output_directory)

    with master_path.open('r') as file:
        lines = file.readlines()

    base_port = int(lines[0].strip())
    next_port = base_port + 1

    tld_list = []
    tld_dict = {}
    auth_groups = {}

    for line in lines[1:]:
        domain, p = line.strip().split(',')
        parts = domain.split('.')
        tld = parts[-1]
        tld_domain = '.'.join(parts[-2:])
        
        if tld not in tld_list:
            tld_list.append(tld)
        
        if tld not in tld_dict:
            tld_dict[tld] = []
        if tld_domain not in tld_dict[tld]:
            tld_dict[tld].append(tld_domain)

        if tld_domain not in auth_groups:
            auth_groups[tld_domain] = []
        auth_groups[tld_domain].append(domain)

    tld_ports = {tld: next_port + index for index, tld in enumerate(tld_list)}
    save_config(dir_path, base_port, [(tld, tld_ports[tld]) for tld in tld_list])
    
    master_dir = {line.split(',')[0]: int(line.split(',')[1]) for line in lines[1:]}
    current_port_offset = len(tld_list)
    tld_domain_ports = {}
    for tld, tld_domains in tld_dict.items():
        domain_ports = {domain: next_port + current_port_offset + index 
                        for index, domain in enumerate(tld_domains)}
        save_config(dir_path, tld_ports[tld], [(domain, domain_ports[domain]) 
                                               for domain in tld_domains])
        tld_domain_ports.update(domain_ports)
        current_port_offset += len(tld_domains)

    for tld_domain, domains in auth_groups.items():
        domain_ports = {domain: master_dir[domain] for domain in domains}
        save_config(dir_path, tld_domain_ports[tld_domain], 
                    [(domain, domain_ports[domain]) for domain in domains])



def is_subdomain(domain:str) ->bool:
    parts = domain.split('.')
    return len(parts) > 2

def main(args: list[str]) -> None:
    if len(args) != 2:
        print("INVALID ARGUMENTS")
        return
    master_path = Path(args[0])
    dir_path = Path(args[1])
    if not valid_master(master_path):
        return
    elif not dir_path.exists() or not dir_path:
        print("NON-WRITABLE SINGLE DIR")
        return
    
    try:
        test_file = dir_path / "test.txt"
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        print("NON-WRITABLE SINGLE DIR")
        return
    launcher(args[0], args[1])


if __name__ == "__main__":
    main(argv[1:])