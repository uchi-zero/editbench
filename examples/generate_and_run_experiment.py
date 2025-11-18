from edit_bench.evaluation import generate_files, test_edits
from os import getenv
from pathlib import Path
from openai import OpenAI
import time
import argparse

GENERATION_PATH = Path(getenv("WORKDIR"), "generations", "whole_file", "gpt-4o-mini")
OUTPUT_FILE="example_results/gpt-4o-mini.json"
PROMPT_FILE="prompts/whole_file.txt"
SPLIT="test"

def gpt_4o_mini_gen_function(prompt, lang):
    client = OpenAI(
        api_key=getenv("OPENAI_API_KEY"),
    )
    max_retries = 5
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                    "role": "user",
                    "content": prompt
                    }
                ]
            )
            generation =  completion.choices[0].message.content
            return generation.split(f"```{lang}")[-1].split("```")[0].strip()
            
        except Exception as e:
            last_exception = e
            
            # Don't sleep on the last attempt
            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                delay = 2 ** attempt
                time.sleep(delay)
    
    # If we get here, all retries failed
    print(last_exception)
    raise last_exception

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_only", action="store_true", help="Whether to generate new files or just test existing ones")
    args = parser.parse_args()

    if args.test_only:
        test_edits(gen_path=GENERATION_PATH, split=SPLIT, output_file=OUTPUT_FILE)
    else:
        generate_files(gpt_4o_mini_gen_function, PROMPT_FILE, GENERATION_PATH, split=SPLIT, max_workers=32)

    # Use our testing function to run tests on the generated files
    test_edits(gen_path=GENERATION_PATH, split=SPLIT, output_file=OUTPUT_FILE)