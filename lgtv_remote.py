import argparse
import sys
from lib.config import TV_IP
from lib.discovery import scan


def cli():
    parser = argparse.ArgumentParser(description="Couch Commander — LG TV Remote")
    parser.add_argument("--ip", default=None, help=f"TV IP address (default: {TV_IP})")
    parser.add_argument("--scan", action="store_true", help="Scan for LG TVs and connect")
    parser.add_argument("--list", action="store_true", help="List LG TVs on the network and exit")
    args = parser.parse_args()

    if args.list:
        print("Scanning for LG TVs...")
        tvs = scan()
        if not tvs:
            print("No TVs found.")
            sys.exit(1)
        for tv in tvs:
            print(f"  {tv['ip']}  ({tv['name']})")
        return

    if args.scan:
        print("Scanning for LG TVs...")
        tvs = scan()
        if not tvs:
            print("No TVs found.")
            sys.exit(1)
        for i, tv in enumerate(tvs):
            print(f"  [{i + 1}] {tv['ip']}  ({tv['name']})")
        if len(tvs) == 1:
            ip = tvs[0]["ip"]
        else:
            choice = input("Select TV: ")
            ip = tvs[int(choice) - 1]["ip"]
        print(f"Connecting to {ip}...")
    else:
        ip = args.ip or TV_IP

    from lib.app import main
    main(ip=ip)


if __name__ == "__main__":
    cli()
