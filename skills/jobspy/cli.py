#!/usr/bin/env python3

import argparse
import sys

from skills.jobspy import search, tracker


def build_parser():
    p = argparse.ArgumentParser(
        prog="jobspy",
        description="Job search and application tracking helpers.",
    )
    sub = p.add_subparsers(dest="command")

    sub.add_parser("search", help="Search job boards")

    sub.add_parser("tracker", help="Track job applications")

    return p


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    parser = build_parser()

    if not argv or argv[0] in {"-h", "--help"}:
        parser.print_help()
        return 0

    command, rest = argv[0], argv[1:]
    if command == "search":
        return search.main(rest, prog="jobspy search")
    if command == "tracker":
        return tracker.main(rest, prog="jobspy tracker")

    parser.error(f"unknown command: {command}")


if __name__ == "__main__":
    main(sys.argv[1:])
