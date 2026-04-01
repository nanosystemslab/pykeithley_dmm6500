"""Command-line interface."""

import argparse
import time

from pykeithley_dmm6500.dmm6500 import DMM6500


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="pykeithley_dmm6500",
        description="Keithley DMM6500 command-line tool",
    )
    parser.add_argument(
        "ip_address",
        help="IP address of the DMM6500",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DMM6500.DEFAULT_PORT,
        help="TCP port (default: %(default)s)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("identify", help="Query instrument identity (*IDN?)")

    measure_parser = sub.add_parser("measure", help="Take a DC voltage measurement")
    measure_parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Number of readings (default: 1)",
    )
    measure_parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.5,
        help="Delay between readings in seconds (default: 0.5)",
    )
    measure_parser.add_argument(
        "--range",
        type=float,
        default=10,
        help="Voltage range (default: 10)",
    )
    measure_parser.add_argument(
        "--nplc",
        type=float,
        default=1,
        help="NPLC value (default: 1)",
    )

    sub.add_parser("reset", help="Reset instrument to factory defaults")

    return parser


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    return create_parser().parse_args()


def main() -> None:
    """PyKeithley_DMM6500."""
    args = parse_args()

    with DMM6500(args.ip_address, port=args.port) as dmm:
        if args.command == "identify":
            print(dmm.identify())

        elif args.command == "reset":
            dmm.reset()
            print("Instrument reset.")

        elif args.command == "measure":
            dmm.configure_dcv(range=args.range, nplc=args.nplc)
            for i in range(args.count):
                value = dmm.measure()
                print(f"{value:+.8e}")
                if i < args.count - 1:
                    time.sleep(args.delay)


if __name__ == "__main__":
    main()
