
"""Command-line interface for API Sentinel."""

import argparse
import json
import sys
from dataclasses import asdict

from api_sentinel.config import load_contract
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
        help="Check an endpoint or reusable JSON contract.",
    )

    check_parser.add_argument(
        "--url",
        help="API endpoint URL.",
    )

    check_parser.add_argument(
        "--status",
        type=int,
        help="Expected HTTP status.",
    )

    check_parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Request timeout in seconds.",
    )

    check_parser.add_argument(
        "--contract",
        help="Path to a reusable JSON contract file.",
    )

    check_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format: text (default) or json.",
    )

    args = parser.parse_args(argv)

    if args.contract:
        if (
            args.url is not None
            or args.status is not None
            or args.timeout is not None
        ):
            print(
                "INVALID CONTRACT: --contract cannot be combined "
                "with --url, --status, or --timeout",
                file=sys.stderr,
            )
            return 2

        try:
            settings = load_contract(args.contract)
        except (OSError, ValueError, TypeError) as exc:
            print(f"INVALID CONTRACT: {exc}", file=sys.stderr)
            return 2

    else:
        # Preserve argparse's original SystemExit(2) behavior.
        if args.url is None or args.status is None:
            check_parser.error(
                "--url and --status are required "
                "unless --contract is provided"
            )

        settings = {
            "url": args.url,
            "expected_status": args.status,
            "timeout": (
                args.timeout
                if args.timeout is not None
                else 2.0
            ),
        }

    try:
        report = check_contract(**settings)
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

        for result in report.json_results:
            print(f"PASS | {result.check}: {result.message}")

        return 0

    print(f"FAIL | {report.url}")

    if report.error:
        print(f"ERROR: {report.error}")

    if report.status_result and not report.status_result.passed:
        print(report.status_result.message)

    for result in report.json_results:
        if not result.passed:
            print(f"FAIL | {result.check}: {result.message}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
