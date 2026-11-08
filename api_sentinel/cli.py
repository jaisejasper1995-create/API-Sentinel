
"""Command-line interface for API Sentinel."""

import argparse
import json
import sys
from dataclasses import asdict

from api_sentinel.runner import check_contract


def main(argv=None) -> int:
    """Run an API contract check and return a meaningful exit code."""
    parser = argparse.ArgumentParser(
        prog="api-sentinel",
        description="Deterministic API contract validation.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Check one API endpoint against a contract.",
    )

    check_parser.add_argument(
        "--url",
        required=True,
        help="API endpoint URL.",
    )

    check_parser.add_argument(
        "--status",
        type=int,
        required=True,
        help="Expected HTTP status.",
    )

    check_parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Request timeout in seconds.",
    )

    check_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format: text (default) or json.",
    )

    args = parser.parse_args(argv)

    try:
        report = check_contract(
            url=args.url,
            expected_status=args.status,
            timeout=args.timeout,
        )
    except (TypeError, ValueError) as exc:
        print(f"INVALID CONTRACT: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(
            json.dumps(
                asdict(report),
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 0 if report.passed else 1

    if report.passed:
        print(f"PASS | {report.url}")
        print("HTTP status matches expected contract")
        return 0

    print(f"FAIL | {report.url}")

    if report.error:
        print(f"ERROR: {report.error}")
    elif report.status_result:
        print(report.status_result.message)

    return 1


if __name__ == "__main__":
    sys.exit(main())
