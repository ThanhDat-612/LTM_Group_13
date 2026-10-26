"""
Server-side validation utilities for LTM Group 13.

Responsibilities:
- Validate upload request metadata.
- Validate filename and prevent path traversal.
- Validate file size against project configuration.
- Validate received byte count.
- Validate SHA-256 checksum.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping, Optional


SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,254}$")


class ValidationResult:
    """Simple result object used by the server validation layer."""

    def __init__(self, valid: bool, code: str = "OK", message: str = "Valid"):
        self.valid = valid
        self.code = code
        self.message = message

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        return (
            f"ValidationResult(valid={self.valid!r}, "
            f"code={self.code!r}, message={self.message!r})"
        )

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "code": self.code,
            "message": self.message,
        }


class FileValidator:
    """Validate files and upload metadata received from a client."""

    def __init__(self, max_file_size_mb: int = 500):
        if max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be greater than 0")
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)

    def validate_filename(self, filename: str) -> ValidationResult:
        if not isinstance(filename, str) or not filename.strip():
            return ValidationResult(False, "INVALID_FILENAME", "Filename is empty.")

        # Reject absolute paths and path traversal.
        path = Path(filename)
        if path.is_absolute():
            return ValidationResult(
                False, "INVALID_FILENAME", "Absolute paths are not allowed."
            )

        if "/" in filename or "\\" in filename:
            return ValidationResult(
                False, "INVALID_FILENAME",
                "Directory separators are not allowed in filename."
            )

        if ".." in filename:
            return ValidationResult(
                False, "INVALID_FILENAME",
                "Path traversal is not allowed."
            )

        if filename in {".", ".."}:
            return ValidationResult(
                False, "INVALID_FILENAME", "Invalid filename."
            )

        if not SAFE_FILENAME.fullmatch(filename):
            return ValidationResult(
                False,
                "INVALID_FILENAME",
                "Filename contains unsupported characters or is too long.",
            )

        return ValidationResult(True)

    def validate_size(self, size: Any) -> ValidationResult:
        if isinstance(size, bool):
            return ValidationResult(False, "INVALID_SIZE", "Size must be an integer.")

        try:
            size = int(size)
        except (TypeError, ValueError):
            return ValidationResult(False, "INVALID_SIZE", "Size must be an integer.")

        if size < 0:
            return ValidationResult(False, "INVALID_SIZE", "Size cannot be negative.")

        if size > self.max_file_size_bytes:
            return ValidationResult(
                False,
                "FILE_TOO_LARGE",
                f"File exceeds the maximum size of "
                f"{self.max_file_size_bytes} bytes.",
            )

        return ValidationResult(True)

    def validate_request(self, request: Mapping[str, Any]) -> ValidationResult:
        if not isinstance(request, Mapping):
            return ValidationResult(
                False, "INVALID_REQUEST", "Upload request must be an object."
            )

        filename = request.get("filename")
        size = request.get("size")

        result = self.validate_filename(filename)
        if not result:
            return result

        result = self.validate_size(size)
        if not result:
            return result

        checksum = request.get("checksum")
        if checksum is not None:
            if not isinstance(checksum, str) or not re.fullmatch(
                r"[0-9a-fA-F]{64}", checksum
            ):
                return ValidationResult(
                    False,
                    "INVALID_CHECKSUM",
                    "Checksum must be a valid SHA-256 hexadecimal string.",
                )

        return ValidationResult(True)

    def validate_received_size(
        self, expected_size: int, received_size: int
    ) -> ValidationResult:
        try:
            expected_size = int(expected_size)
            received_size = int(received_size)
        except (TypeError, ValueError):
            return ValidationResult(
                False, "INVALID_SIZE", "Expected and received sizes must be integers."
            )

        if expected_size != received_size:
            return ValidationResult(
                False,
                "SIZE_MISMATCH",
                f"Expected {expected_size} bytes but received {received_size} bytes.",
            )

        return ValidationResult(True)

    def calculate_checksum(self, file_path: str | Path) -> str:
        """Calculate SHA-256 checksum without loading the whole file into RAM."""
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk:
                    break
                sha256.update(chunk)

        return sha256.hexdigest()

    def validate_checksum(
        self, file_path: str | Path, expected_checksum: Optional[str]
    ) -> ValidationResult:
        if not expected_checksum:
            return ValidationResult(True)

        if not isinstance(expected_checksum, str) or not re.fullmatch(
            r"[0-9a-fA-F]{64}", expected_checksum
        ):
            return ValidationResult(
                False, "INVALID_CHECKSUM",
                "Expected checksum is not a valid SHA-256 value."
            )

        actual_checksum = self.calculate_checksum(file_path)

        if actual_checksum.lower() != expected_checksum.lower():
            return ValidationResult(
                False,
                "CHECKSUM_MISMATCH",
                "Checksum does not match the received file.",
            )

        return ValidationResult(True)

    def validate_file(
        self,
        file_path: str | Path,
        expected_size: Optional[int] = None,
        expected_checksum: Optional[str] = None,
    ) -> ValidationResult:
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            return ValidationResult(
                False, "FILE_NOT_FOUND", "File does not exist."
            )

        actual_size = path.stat().st_size

        result = self.validate_size(actual_size)
        if not result:
            return result

        if expected_size is not None:
            result = self.validate_received_size(expected_size, actual_size)
            if not result:
                return result

        return self.validate_checksum(path, expected_checksum)


# Convenience functions for use by other server modules.
def validate_upload_request(
    request: Mapping[str, Any], max_file_size_mb: int = 500
) -> ValidationResult:
    return FileValidator(max_file_size_mb).validate_request(request)


def validate_file(
    file_path: str | Path,
    expected_size: Optional[int] = None,
    expected_checksum: Optional[str] = None,
    max_file_size_mb: int = 500,
) -> ValidationResult:
    return FileValidator(max_file_size_mb).validate_file(
        file_path, expected_size, expected_checksum
    )
