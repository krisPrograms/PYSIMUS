import subprocess
import os

# Prism may or may not be preserved
PRISM: str
PRISM_PATH = "bin/prism/bin/prism"
if os.path.isfile(PRISM_PATH):
    PRISM = PRISM_PATH
else:
    PRISM = "prism"

# Take a model path and query string, and write the results to a specified file.
# Returns exit code of the process.
def query_dtmc (model_file: str, query_string: str, result_filename: str) -> int:
    return subprocess.run([
        PRISM,
        model_file,
        "-pctl", query_string,
        "-exportresults", f"{result_filename}:csv"
    ], capture_output=True).returncode

# Take a model path and query string, and write the results to a specified file.
def query_dtmc_with_file (model_file: str, query_file: str, result_filename: str) -> int:
    return subprocess.run([
        PRISM,
        model_file,
        query_file,
        "-exportresults", f"{result_filename}:csv"
    ], capture_output=True).returncode
