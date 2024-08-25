from sys import argv
from pathlib import Path
from typing import List

def read_file(filepath: Path) -> str:
    try:
        with filepath.open('r') as file:
            return file.read()
    except:
        return None

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

def is_valid_port(port: str) -> bool:
    try:
        num = int(port)
        return 1024 <= num <= 65535
    except ValueError:
        return False
def get_filename(path: Path) -> str:
    return path.name

def verify(master_file: Path, directory_of_single_files: Path) -> str:
    if not master_file.exists():
        return "invalid master"
    
    master_dir = {}
    try:
        with master_file.open('r') as file:
            master_lines = file.readlines()
        master_base_port = int(master_lines[0].strip())
        if not is_valid_port(master_lines[0].strip()):
            return "invalid master"
        for line in master_lines[1:]:
            domain, port = line.strip().split(',')
            if len(domain.split('.')) < 2 or not valid_hostname(domain) or not is_valid_port(port):
                return "invalid master"
            master_dir[domain] = int(port)
    except ValueError:
        return "invalid master"
    except IndexError:
        return "invalid master"

    single_files = list(directory_of_single_files.glob("*.conf"))
    root_file_content = None
    for single_file in single_files:
        with single_file.open('r') as f:
            content = f.readlines()
            if int(content[0].strip()) == master_base_port:
                root_file_content = content
                break

    if not root_file_content:
        return "invalid master"

    tld_ports = {line.split(',')[0]: int(line.split(',')[1]) for line in root_file_content[1:]}
    for tld, tld_port in tld_ports.items():
        tld_file_content = None
        for single_file in single_files:
            with single_file.open('r') as f:
                content = f.readlines()
                if int(content[0].strip()) == tld_port:
                    tld_file_content = content
                    break

        if not tld_file_content:
            return "invalid single"

        sld_ports = {line.split(',')[0]: int(line.split(',')[1]) for line in tld_file_content[1:]}
        for sld_domain, sld_domain_port in sld_ports.items():
            subdomain_file_content = None
            for single_file in single_files:
                with single_file.open('r') as f:
                    content = f.readlines()
                    if int(content[0].strip()) == sld_domain_port:
                        subdomain_file_content = content
                        break

            if not subdomain_file_content:
                return "neq"

            for line in subdomain_file_content[1:]:
                domain, port = line.strip().split(',')
                if domain not in master_dir or master_dir[domain] != int(port):
                    return "neq"

    return "eq"

def main(args: list[str]) -> None:
    if len(args) != 2:
        print("invalid arguments")
        return

    master_file = Path(args[0])
    directory_of_single_files = Path(args[1])
    if not directory_of_single_files.exists() or not directory_of_single_files.is_dir():
        print("singles io error")
        return
    
    result = verify(master_file, directory_of_single_files)
    if result == None:
        result = "invalid master"
    print(result)

if __name__ == "__main__":
    main(argv[1:])