#!/usr/bin/env python3
"""
Copy mkcert's user (root) certificate into the folder next to this script.

What it does:
- Runs: mkcert -CAROOT
- Finds: rootCA.pem inside that CAROOT directory
- Copies it to: the same directory where this script file lives

Notes:
- This copies ONLY the public root certificate (rootCA.pem).
- It does NOT copy rootCA-key.pem (the private key),
  because that file is secret.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def get_mkcert_caroot() -> Path:
    """
    CAROOT = the directory where mkcert stores its local Certificate
    Authority (CA) files.
    """
    try:
        result = subprocess.run(
            ["mkcert", "-CAROOT"],
            # check=True: raise an error if the command fails
            check=True,
            # capture_output=True: capture stdout/stderr instead of printing
            capture_output=True,
            # text=True: decode output as text (str) instead of bytes
            text=True
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            (
                "mkcert was not found. Make sure mkcert is installed "
                "and available in PATH."
            )
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"mkcert failed with exit code {e.returncode}. stderr:\n{e.stderr}"
        ) from e

    caroot_str = (result.stdout or "").strip()
    if not caroot_str:
        raise RuntimeError("mkcert returned an empty CAROOT path.")

    return Path(caroot_str)


def main() -> int:
    # Script directory = folder where this .py file is located
    script_dir = Path(__file__).resolve().parent

    caroot = get_mkcert_caroot()

    # PEM = a common text format for certificates
    src_cert = caroot / "rootCA.pem"
    dst_cert = script_dir / "rootCA.pem"

    if not src_cert.is_file():
        raise RuntimeError(f"Source certificate not found: {src_cert}")

    # copy2 = copy file content + metadata (timestamps, etc.)
    shutil.copy2(src_cert, dst_cert)

    print("Done.")
    print(f"Copied: {src_cert}")
    print(f"To:     {dst_cert}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
