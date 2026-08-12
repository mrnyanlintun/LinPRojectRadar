#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path


def verify(root: Path) -> list[str]:
    failures: list[str] = []
    checksum_file = root / 'CHECKSUMS.sha256'
    if not checksum_file.exists():
        return ['missing CHECKSUMS.sha256']
    for line in checksum_file.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        expected, rel = line.split('  ', 1)
        path = root / rel
        if not path.exists():
            failures.append(f'missing {rel}')
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            failures.append(f'mismatch {rel}')
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    failures = verify(args.root)
    if failures:
        print('FAIL')
        print('\n'.join(failures))
        raise SystemExit(1)
    print('PASS: all programme checksums match')


if __name__ == '__main__':
    main()
