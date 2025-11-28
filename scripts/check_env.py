#!/usr/bin/env python3
"""Simple environment variable checker for Convergence_Engine.

This script lists required/optional env variables and prints warnings if any are missing.
It is deliberately minimal so it can be used locally without additional deps.
"""
import os
import sys

REQUIRED = [
    # Optional: these are recommended for specific features
    # 'OLLAMA_API_KEY' is optional — only needed for cloud mode
]

RECOMMENDED = [
    'POSTGRES_PASSWORD',
    'DJINN_DB_PASSWORD',
]

OPTIONAL = [
    'OLLAMA_API_KEY',
    'OLLAMA_BASE_URL',
    'INTERNAL_API_KEY',
    'EXTERNAL_API_KEY',
    'DJINN_DB_USERNAME',
]

def main():
    missing_required = []
    missing_recommended = []
    present_optional = []

    for k in REQUIRED:
        if not os.environ.get(k):
            missing_required.append(k)

    for k in RECOMMENDED:
        if not os.environ.get(k):
            missing_recommended.append(k)

    for k in OPTIONAL:
        if os.environ.get(k):
            present_optional.append(k)

    print('\nEnvironment variable check for Convergence_Engine\n' + '-'*70)
    if missing_required:
        print('[FAIL] Missing required environment variables:')
        for k in missing_required:
            print(f'   - {k}')
    else:
        print('[PASS] Required environment: OK')

    if missing_recommended:
        print('[WARN] Missing recommended environment variables:')
        for k in missing_recommended:
            print(f'   - {k}')
    else:
        print('[PASS] Recommended environment: OK')

    if present_optional:
        print('[INFO] Optional env vars present: ' + ', '.join(present_optional))

    if missing_required:
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
