import datetime
import hashlib
import os
from typing import List
import re
import ipaddress

def utc_now():
    return datetime.datetime.now(datetime.UTC)

def clean_name(text):
    # Removes all special characters except spaces and alphanumeric characters
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-_.]', '', text)
    return cleaned

def compute_file_hash(file_path, algorithm='sha256'):
    """Compute the hash of a file using the specified algorithm."""
    hash_func = hashlib.new(algorithm)

    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):  # Read the file in chunks of 8192 bytes
            hash_func.update(chunk)

    return hash_func.hexdigest()

def compute_folder_hash(folder_path, algorithm='sha256', extra_string_list: List[str] = None):
    if extra_string_list is None:
        extra_string_list = []
    extra_string_list = [x for x in extra_string_list if x is not None]
    hash_func = hashlib.new(algorithm)
    hashes = []
    if not os.path.exists(folder_path):
        return None
    files = os.listdir(folder_path)
    if len(files) == 0:
        return None
    files = [x for x in files if not os.path.isdir(os.path.join(folder_path, x))]
    files.sort()
    for file in files:
        hashes.append(compute_file_hash(os.path.join(folder_path, file)))
    hashes = hashes + extra_string_list
    hash_func.update(''.join(hashes).encode())

    return hash_func.hexdigest()


def is_valid_host(value: str) -> bool:
    if value is None or not isinstance(value, str):
        return False

    # Strip leading scheme, if any available
    if value.startswith("http://"):
        value = value[len("http://"):]
    if value.startswith("https://"):
        value = value[len("https://"):]

    # Match: [IPv6]:port or hostname:port or IPv4:port
    # Regex: optional [brackets], host part, optional :port

    host_port_pattern = re.compile(r'''
        ^
        (?P<host>                  # Host part
            \[[^\]]+\]             # [IPv6]
            |                      # or
            [^:\[\]]+              # hostname or IPv4
        )
        (?::(?P<port>\d{1,5}))?    # Optional :port
        $
        ''', re.VERBOSE)

    m = host_port_pattern.match(value)
    if not m:
        return False

    host = m.group('host')
    port = m.group('port')

    # Remove brackets from IPv6 if present
    if host.startswith('[') and host.endswith(']'):
        host = host[1:-1]

    # Validate port if given
    if port is not None:
        try:
            port = int(port)
            if not (0 < port < 65536):
                return False
        except ValueError:
            return False

    # Check if it's a valid IP (IPv4 or IPv6)
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass  # Not an IP address

    # Else, check if it's a valid hostname
    # "localhost" and simple names allowed, but must not be empty string
    if host and re.match(r'^[a-zA-Z0-9.-]+$', host):
        return True

    return False

def to_posix_path(path):
    if os.sep != "/":
        return path.replace(os.sep, "/")
    return path


def from_posix_path(path: str) -> str:
    if os.sep != "/":
        return path.replace("/", os.sep)
    return path
