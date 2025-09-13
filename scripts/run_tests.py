#!/usr/bin/env python
import argparse
import os
import subprocess
import sys


def run_tests(test_type=None, verbose=False):
    """Run the tests with pytest."""
    # Change to the project root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Build the command
    command = ["pytest"]

    if verbose:
        command.append("-v")

    if test_type:
        if test_type == "unit":
            command.append("tests/unit")
        elif test_type == "integration":
            command.append("tests/integration")
        elif test_type == "functional":
            command.append("tests/functional")
        elif test_type == "performance":
            command.append("tests/performance")

    # Run the tests
    result = subprocess.run(command, capture_output=True, text=True)

    # Print the output
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    # Return the exit code
    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PolyClash tests")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "functional", "performance"],
        help="Type of tests to run",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    sys.exit(run_tests(args.type, args.verbose))
