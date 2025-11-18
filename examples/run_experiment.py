from edit_bench.evaluation import test_edits
from os import getenv
from pathlib import Path

# Path to the generations 
GENERATION_PATH = Path(getenv("WORKDIR"), "generations", "whole_file", "gpt-o3-mini")
# Path to the output file
OUTPUT_FILE="example_results/gpt-o3-mini.json"
# test (108 problems) or complete (540 problems)
SPLIT="test"

# Use our testing function to run tests on the generated files
test_edits(gen_path=GENERATION_PATH, split=SPLIT, output_file=OUTPUT_FILE)