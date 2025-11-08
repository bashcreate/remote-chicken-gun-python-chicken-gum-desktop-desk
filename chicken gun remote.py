#!/usr/bin/env python3
"""
Project helper CLI for Remote Chicken Gun
Provides commands to inspect the repository, list Python files, find entry points, and help generate requirements.
This is a safe helper script created to make it easier to work with this repository locally.
"""

import argparse
import os
import subprocess
import sys
import textwrap

PROJECT_NAME = "Remote Chicken Gun"

README_SNIPPET = textwrap.dedent(
    """
    This repository is a Python project. Use this helper to inspect the repository,
    list Python files, find likely entry points, and (optionally) generate
    a requirements.txt using pipreqs if it is installed.

    Typical workflow:
      python main.py info
      python main.py list-files
      python main.py find-entrypoints
      python main.py gen-reqs
    """
)

def list_py_files():
    """Print all tracked .py files under the repository folder."""
    for root, dirs, files in os.walk('.'):
        # skip virtual env directories commonly named .venv or venv
        if any(part in ('.venv', 'venv', '__pycache__') for part in root.split(os.sep)):
            continue
        for f in files:
            if f.endswith('.py'):
                print(os.path.normpath(os.path.join(root, f)))

def find_entrypoints():
    """Search .py files for the common entrypoint pattern: if __name__ == '__main__'"""
    results = []
    for root, dirs, files in os.walk('.'):
        if any(part in ('.venv', 'venv', '__pycache__') for part in root.split(os.sep)):
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    text = fh.read()
            except Exception:
                continue
            if "if __name__ == '__main__'" in text or 'if __name__ == "__main__"' in text:
                results.append(path)
    if not results:
        print('No entrypoints found (files containing "if __name__ == \\"__main__\\").')
    else:
        print('Files with entrypoints:')
        for r in results:
            print(os.path.normpath(r))

def gen_requirements():
    """Attempt to generate requirements.txt using pipreqs. If pipreqs is not installed, print instructions."""
    # Check if pipreqs available
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'show', 'pipreqs'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Run pipreqs
        print('Running: pipreqs --force .')
        subprocess.check_call([sys.executable, '-m', 'pipreqs', '--force', '.'])
        print('\nrequirements.txt generated (or updated) in the repository root.')
    except subprocess.CalledProcessError:
        print('pipreqs appears to be installed but failed to run. You can run: pip install pipreqs && pipreqs --force .')
    except Exception:
        print('pipreqs is not installed. To install run:')
        print('  pip install pipreqs')
        print('Then run:')
        print('  pipreqs --force .')

def show_readme_snippet():
    print(README_SNIPPET)

def run_shell(cmd):
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f'Command failed with exit code {e.returncode}: {cmd}')

def main():
    parser = argparse.ArgumentParser(prog='main.py', description='Project helper CLI for %s' % PROJECT_NAME)
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('info', help='Show short README snippet and project info')
    sub.add_parser('list-files', help='List all .py files in the repo (skips venv/.venv)')
    sub.add_parser('find-entrypoints', help='Find files that contain a __main__ entrypoint')
    sub.add_parser('gen-reqs', help='Generate requirements.txt using pipreqs (if installed)')

    args = parser.parse_args()

    if args.cmd == 'info':
        show_readme_snippet()
    elif args.cmd == 'list-files':
        list_py_files()
    elif args.cmd == 'find-entrypoints':
        find_entrypoints()
    elif args.cmd == 'gen-reqs':
        gen_requirements()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
