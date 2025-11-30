"""
check_mysql_port.py

Probe script that:
- scans common MySQL ports on localhost
- checks if the port is open (TCP socket)
- attempts to authenticate using mysql-connector if the port is open

Usage:
    # optional: set env vars DB_USER, DB_PASSWORD, DB_HOST
    python check_mysql_port.py --user root --password "" 

"""
import socket
import argparse
import os
import mysql.connector
from mysql.connector import Error

COMMON_PORTS = [3306, 33060, 3307, 3308]


def is_port_open(host: str, port: int, timeout=1.0) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except Exception:
            return False


def try_mysql_login(host: str, port: int, user: str, password: str, timeout=5):
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connection_timeout=timeout
        )
        if conn.is_connected():
            ver = conn.get_server_info()
            conn.close()
            return True, ver
    except Error as e:
        return False, str(e)
    return False, "unknown"


def main():
    parser = argparse.ArgumentParser(description="Probe MySQL ports and attempt login.")
    parser.add_argument("--host", default=os.getenv("DB_HOST", "localhost"), help="DB host (default localhost)")
    parser.add_argument("--user", default=os.getenv("DB_USER", "root"), help="DB user")
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", ""), help="DB password")
    parser.add_argument("--ports", nargs="*", type=int, default=COMMON_PORTS, help="Ports to probe")
    args = parser.parse_args()

    host = args.host
    user = args.user
    password = args.password
    ports = args.ports

    print(f"Probing host={host} user={user} ports={ports}")

    found_open = []
    for p in ports:
        open_ = is_port_open(host, p)
        print(f"Port {p}: {'OPEN' if open_ else 'closed'}")
        if open_:
            found_open.append(p)

    if not found_open:
        print("No common MySQL ports are open on the host. You may need to check mysqld service or firewall.")
        return

    for p in found_open:
        print(f"\nAttempting MySQL login on {host}:{p} as user '{user}' (password hidden)")
        ok, info = try_mysql_login(host, p, user, password)
        if ok:
            print(f"SUCCESS: Connected to MySQL on port {p}. Server version: {info}")
        else:
            print(f"FAILED to authenticate on port {p}: {info}")


if __name__ == '__main__':
    main()
