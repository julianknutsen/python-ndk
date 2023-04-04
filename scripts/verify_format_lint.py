# Copyright 2023 Julian Knutsen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the “Software”), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import os
import subprocess
import sys


def _run_cmd(args: list[str]) -> bool:
    print(f"Running {args} ...")
    output = subprocess.run(args, capture_output=True, text=True, check=False)
    print(output.stdout)
    print(output.stderr)
    return bool(output.returncode)


def main():
    py_files = []
    for root, _, files in os.walk("."):
        for file in files:
            if any(item in root for item in ["venv", "docs", ".tmp"]):
                continue
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    failure = any(
        [
            _run_cmd(["poetry", "check"]),
            _run_cmd(["black", "--check", "."]),
            _run_cmd(["isort", "--check-only", "."]),
            _run_cmd(["pylint"] + py_files),
            _run_cmd(["mypy", "."]),
        ]
    )

    if not failure:
        print("[SUCCESS]")
    else:
        print("[FAILURE]")
        sys.exit(1)
