#!/usr/bin/env python3
"""SentraGuard Lite CLI.

Exactly one command is supported:

    python cli.py analyze --input sample_request.json --output out.json

The CLI always calls the running FastAPI service; it never imports detector
logic directly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests

DEFAULT_API_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 15


def _api_base_url(value: str | None) -> str:
    return (value or os.getenv("API_BASE_URL") or DEFAULT_API_BASE_URL).rstrip("/")


def _format_api_error(response: requests.Response) -> str:
    """Build a useful error without echoing validation ``input`` values."""

    try:
        body = response.json()
    except ValueError:
        return f"HTTP {response.status_code}"

    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, list):
        messages: list[str] = []
        for item in detail:
            if not isinstance(item, dict):
                continue
            location = ".".join(str(part) for part in item.get("loc", []))
            message = item.get("msg", "invalid value")
            messages.append(f"{location}: {message}" if location else message)
        if messages:
            return f"HTTP {response.status_code}: " + "; ".join(messages)
    if isinstance(detail, str):
        return f"HTTP {response.status_code}: {detail}"
    return f"HTTP {response.status_code}"


def analyze(input_path: str, output_path: str, api_base_url: str) -> int:
    """Read a request file, call ``POST /analyze``, and write the response."""

    try:
        with open(input_path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {input_path}: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: could not read {input_path}: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("error: input JSON must be an object", file=sys.stderr)
        return 2

    url = f"{api_base_url}/analyze"
    try:
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT_SECONDS)
    except requests.exceptions.ConnectionError:
        print(
            f"error: could not connect to the API at {api_base_url}. "
            "Is it running?",
            file=sys.stderr,
        )
        return 1
    except requests.exceptions.Timeout:
        print(
            f"error: API request timed out after {DEFAULT_TIMEOUT_SECONDS}s",
            file=sys.stderr,
        )
        return 1
    except requests.exceptions.RequestException as exc:
        print(f"error: API request failed: {exc}", file=sys.stderr)
        return 1

    if response.status_code != 200:
        print(f"error: API returned {_format_api_error(response)}", file=sys.stderr)
        return 1

    try:
        result = response.json()
    except ValueError:
        print("error: API returned invalid JSON", file=sys.stderr)
        return 1

    if not isinstance(result, dict):
        print("error: API response must be a JSON object", file=sys.stderr)
        return 1

    try:
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except OSError as exc:
        print(f"error: could not write {output_path}: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="SentraGuard Lite command-line client",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a JSON request through POST /analyze",
    )
    analyze_parser.add_argument(
        "--input",
        required=True,
        help="Path to the request JSON file",
    )
    analyze_parser.add_argument(
        "--output",
        required=True,
        help="Path to write the response JSON file",
    )
    analyze_parser.add_argument(
        "--api-base-url",
        default=None,
        help=(
            "API base URL. Defaults to the API_BASE_URL environment variable "
            f"or {DEFAULT_API_BASE_URL}."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        return analyze(args.input, args.output, _api_base_url(args.api_base_url))
    return 2


if __name__ == "__main__":
    sys.exit(main())
