"""Shared security core for the upload server and standalone security checker.

Run the independent checker with:
    python -m server.security --self-test
    python -m server.security --scan PATH [--max-size-mb 500]

This module is also imported by UploadHandler; there is no second copy of the
validation rules.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

from server.validator import FileValidator, ValidationResult


class SecurityManager:
    """One security policy shared by the server and the standalone tool."""

    def __init__(self, max_file_size_mb: int = 500):
        self.validator = FileValidator(max_file_size_mb=max_file_size_mb)

    def validate_upload_request(self, request: Mapping[str, Any]) -> ValidationResult:
        return self.validator.validate_request(request)

    def validate_received_file(
        self,
        file_path: str | Path,
        expected_size: int,
        expected_checksum: str | None,
    ) -> ValidationResult:
        return self.validator.validate_file(
            file_path,
            expected_size=expected_size,
            expected_checksum=expected_checksum,
        )

    def safe_destination(self, upload_dir: str | Path, filename: str) -> Path:
        """Build a destination only after strict filename validation."""
        result = self.validator.validate_filename(filename)
        if not result:
            raise ValueError(f"{result.code}: {result.message}")
        root = Path(upload_dir).resolve()
        destination = (root / filename).resolve()
        if destination.parent != root:
            raise ValueError("INVALID_FILENAME: Destination escapes upload directory")
        return destination


def _self_test(max_size_mb: int) -> int:
    security = SecurityManager(max_size_mb)
    cases = [
        ("valid filename", security.validator.validate_filename("report.pdf"), True),
        ("path traversal", security.validator.validate_filename("../secret.txt"), False),
        ("absolute path", security.validator.validate_filename("/etc/passwd"), False),
        ("windows path", security.validator.validate_filename(r"..\\secret.txt"), False),
        ("empty filename", security.validator.validate_filename(""), False),
        ("negative size", security.validator.validate_size(-1), False),
        ("oversized file", security.validator.validate_size(max_size_mb * 1024 * 1024 + 1), False),
        ("valid SHA-256", security.validator.validate_request({"filename":"a.txt", "size":1, "checksum":"a" * 64}), True),
        ("invalid SHA-256", security.validator.validate_request({"filename":"a.txt", "size":1, "checksum":"bad"}), False),
    ]
    passed = 0
    print("=== SECURITY CORE SELF-TEST ===")
    for name, result, expected in cases:
        ok = bool(result) is expected
        passed += int(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {result.code} - {result.message}")
    print(f"\nResult: {passed}/{len(cases)} tests passed")
    return 0 if passed == len(cases) else 1


def _scan(path: Path, max_size_mb: int) -> int:
    security = SecurityManager(max_size_mb)
    print("=== FILE SECURITY CHECK ===")
    if not path.exists() or not path.is_file():
        print(f"[FAIL] File not found: {path}")
        return 2
    name_result = security.validator.validate_filename(path.name)
    size_result = security.validator.validate_size(path.stat().st_size)
    checksum = security.validator.calculate_checksum(path) if size_result else None
    results = [("Filename", name_result), ("File size", size_result)]
    for label, result in results:
        print(f"[{'PASS' if result else 'FAIL'}] {label}: {result.code} - {result.message}")
    if checksum:
        print(f"[INFO] SHA-256: {checksum}")
    print("[INFO] This checks filename, size and computes integrity hash; it does not scan malware.")
    return 0 if all(bool(result) for _, result in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Standalone checker using the server's shared security core")
    parser.add_argument("--self-test", action="store_true", help="Run built-in security tests")
    parser.add_argument("--scan", type=Path, help="Check a local file")
    parser.add_argument("--max-size-mb", type=int, default=500)
    args = parser.parse_args()
    if args.max_size_mb <= 0:
        parser.error("--max-size-mb must be greater than zero")
    if args.self_test:
        return _self_test(args.max_size_mb)
    if args.scan:
        return _scan(args.scan, args.max_size_mb)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
