#!/usr/bin/env python3
"""
Display HumanEditBench results in table or CSV format.

This script reads JSON result files from a directory and displays them in a nice table
or CSV format. It supports both summary statistics and granular per-question results.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datasets import load_dataset


def load_results(results_dir: Path) -> Dict[str, dict]:
    """
    Load all JSON result files from a directory.

    Args:
        results_dir: Path to directory containing JSON result files

    Returns:
        Dictionary mapping model names to their result dictionaries
    """
    results = {}

    for json_file in results_dir.glob("*.json"):
        model_name = json_file.stem
        with open(json_file, "r") as f:
            results[model_name] = json.load(f)

    return results


def get_question_ids_from_dataset(split: str) -> Set[int]:
    """
    Load the HuggingFace dataset and extract question IDs for the given split.

    Args:
        split: Dataset split ("test" or "complete")

    Returns:
        Set of question IDs (as integers) from the dataset
    """
    dataset = load_dataset("copilot-arena/editbench", split=split)
    question_ids = set()

    for item in dataset:
        question_ids.add(item["problem_id"])

    return question_ids


def classify_questions_by_difficulty(results: Dict[str, dict], question_ids: List[str], threshold: int = 20) -> Tuple[Set[str], Set[str]]:
    """
    Classify questions as easy or hard based on how many models get 100% on them.

    Args:
        results: Dictionary of model results
        question_ids: List of question IDs to classify
        threshold: Number of models needed to get 100% for a question to be "easy" (default: 20)

    Returns:
        Tuple of (easy_questions, hard_questions) as sets
    """
    easy_questions = set()
    hard_questions = set()

    for q_id in question_ids:
        # Count how many models got 100% (1.0) on this question
        perfect_count = 0
        for model_data in results.values():
            if q_id in model_data and model_data[q_id] == 1.0:
                perfect_count += 1

        if perfect_count >= threshold:
            easy_questions.add(q_id)
        else:
            hard_questions.add(q_id)

    return easy_questions, hard_questions



def get_question_ids(results: Dict[str, dict], split: Optional[str] = None) -> List[str]:
    """
    Extract question IDs from results, optionally filtered by dataset split.

    Args:
        results: Dictionary of model results
        split: Optional dataset split to filter by ("test" or "complete")

    Returns:
        Sorted list of question IDs (as strings like "question_1")
    """
    # If split is specified, get question IDs from the dataset
    if split:
        dataset_question_ids = get_question_ids_from_dataset(split)
        # Filter to only include questions from this split
        question_ids = set()
        for model_data in results.values():
            for key in model_data.keys():
                if key.startswith("question_"):
                    # Extract numeric ID
                    question_num = int(key.split("_")[1])
                    if question_num in dataset_question_ids:
                        question_ids.add(key)
    else:
        # Get all question IDs from results
        question_ids = set()
        for model_data in results.values():
            for key in model_data.keys():
                if key.startswith("question_"):
                    question_ids.add(key)

    # Convert to sorted list
    question_ids_list = sorted(question_ids, key=lambda x: int(x.split("_")[1]))

    return question_ids_list


def format_value(value: float, decimal_places: int = 4) -> str:
    """Format a float value with specified decimal places."""
    if value is None:
        return "N/A"
    return f"{value:.{decimal_places}f}"


def display_summary_table(results: Dict[str, dict], csv_mode: bool = False, split: Optional[str] = None, show_difficulty: bool = False):
    """
    Display summary statistics (average_test_rate and pass_rate) for each model.

    Args:
        results: Dictionary of model results
        csv_mode: If True, output as CSV; otherwise as formatted table
        split: Optional dataset split to filter by ("test" or "complete")
        show_difficulty: If True, show separate columns for easy and hard questions
    """
    # Sort models alphabetically
    models = sorted(results.keys())

    # Get question IDs for this split if specified
    question_ids = get_question_ids(results, split=split)

    # If showing difficulty, classify questions
    if show_difficulty:
        easy_questions, hard_questions = classify_questions_by_difficulty(results, question_ids)

    if csv_mode:
        # CSV header
        if show_difficulty:
            print("Model,Pass Rate (All),Pass Rate (Easy),Pass Rate (Hard)")
        else:
            print("Model,Pass Rate")

        # CSV rows
        for model in models:
            data = results[model]

            # Calculate overall metrics
            if split:
                scores = []
                for q_id in question_ids:
                    if q_id in data:
                        scores.append(data[q_id])

                if scores:
                    pass_rate = sum(1 for s in scores if s == 1.0) / len(scores)
                else:
                    pass_rate = "N/A"
            else:
                pass_rate = data.get("pass_rate", "N/A")

            pass_str = format_value(pass_rate) if isinstance(pass_rate, float) else pass_rate

            if show_difficulty:
                # Calculate easy questions metrics
                easy_scores = [data[q_id] for q_id in easy_questions if q_id in data]
                if easy_scores:
                    easy_pass = sum(1 for s in easy_scores if s == 1.0) / len(easy_scores)
                    easy_pass_str = format_value(easy_pass)
                else:
                    easy_pass_str = "N/A"

                # Calculate hard questions metrics
                hard_scores = [data[q_id] for q_id in hard_questions if q_id in data]
                if hard_scores:
                    hard_pass = sum(1 for s in hard_scores if s == 1.0) / len(hard_scores)
                    hard_pass_str = format_value(hard_pass)
                else:
                    hard_pass_str = "N/A"

                print(f"{model},{pass_str},{easy_pass_str},{hard_pass_str}")
            else:
                print(f"{model},{pass_str}")
    else:
        # Calculate column widths for table formatting
        max_model_len = max(len(model) for model in models)
        model_width = max(max_model_len, len("Model"))

        # Table header
        if show_difficulty:
            header = f"{'Model':<{model_width}} | {'Pass (All)':>12} | {'Pass (Easy)':>12} | {'Pass (Hard)':>12}"
        else:
            header = f"{'Model':<{model_width}} | {'Pass Rate':>10}"

        separator = "-" * len(header)

        print(separator)
        print(header)
        print(separator)

        # Table rows
        for model in models:
            data = results[model]

            # Calculate overall metrics
            if split:
                scores = []
                for q_id in question_ids:
                    if q_id in data:
                        scores.append(data[q_id])

                if scores:
                    pass_rate = sum(1 for s in scores if s == 1.0) / len(scores)
                else:
                    pass_rate = None
            else:
                pass_rate = data.get("pass_rate", None)

            pass_str = format_value(pass_rate) if pass_rate is not None else "N/A"

            if show_difficulty:
                # Calculate easy questions metrics
                easy_scores = [data[q_id] for q_id in easy_questions if q_id in data]
                if easy_scores:
                    easy_pass = sum(1 for s in easy_scores if s == 1.0) / len(easy_scores)
                    easy_pass_str = format_value(easy_pass)
                else:
                    easy_pass_str = "N/A"

                # Calculate hard questions metrics
                hard_scores = [data[q_id] for q_id in hard_questions if q_id in data]
                if hard_scores:
                    hard_pass = sum(1 for s in hard_scores if s == 1.0) / len(hard_scores)
                    hard_pass_str = format_value(hard_pass)
                else:
                    hard_pass_str = "N/A"

                print(f"{model:<{model_width}} | {pass_str:>12} | {easy_pass_str:>12} | {hard_pass_str:>12}")
            else:
                print(f"{model:<{model_width}} | {pass_str:>10}")

        print(separator)


def display_granular_table(results: Dict[str, dict], csv_mode: bool = False, split: Optional[str] = None):
    """
    Display per-question results for each model.

    Args:
        results: Dictionary of model results
        csv_mode: If True, output as CSV; otherwise as formatted table
        split: Optional dataset split to filter by ("test" or "complete")
    """
    # Sort models alphabetically
    models = sorted(results.keys())

    # Get question IDs (filtered by split if specified)
    question_ids = get_question_ids(results, split=split)

    if csv_mode:
        # CSV header
        header_parts = ["Model"] + [q.replace("question_", "Q") for q in question_ids]
        print(",".join(header_parts))

        # CSV rows
        for model in models:
            data = results[model]
            row_parts = [model]

            for q_id in question_ids:
                value = data.get(q_id, None)
                if value is not None:
                    row_parts.append(format_value(value, decimal_places=2))
                else:
                    row_parts.append("N/A")

            print(",".join(row_parts))
    else:
        # For table mode, this would be very wide, so we'll display in a transposed format
        # where each question is a row and each model is a column

        max_q_len = max(len(q) for q in question_ids)
        q_width = max(max_q_len, len("Question"))

        # Calculate column width for each model (model name or value, whichever is longer)
        col_width = 8  # Minimum width for values like "0.8333"
        for model in models:
            col_width = max(col_width, len(model))

        # Table header
        header_parts = [f"{'Question':<{q_width}}"]
        for model in models:
            header_parts.append(f"{model:^{col_width}}")
        header = " | ".join(header_parts)
        separator = "-" * len(header)

        print(separator)
        print(header)
        print(separator)

        # Table rows (one per question)
        for q_id in question_ids:
            row_parts = [f"{q_id:<{q_width}}"]

            for model in models:
                data = results[model]
                value = data.get(q_id, None)

                if value is not None:
                    val_str = format_value(value, decimal_places=2)
                else:
                    val_str = "N/A"

                row_parts.append(f"{val_str:^{col_width}}")

            print(" | ".join(row_parts))

        print(separator)


def main():
    parser = argparse.ArgumentParser(
        description="Display HumanEditBench results in table or CSV format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic table view
  python display_results_csv.py results/whole_file

  # CSV output for spreadsheet
  python display_results_csv.py results/whole_file --csv

  # Granular per-question results
  python display_results_csv.py results/whole_file --granular

  # Filter by dataset split (test or complete)
  python display_results_csv.py results/whole_file --split test
  python display_results_csv.py results/whole_file --split complete --csv

  # Show easy vs hard columns (easy = 20+ models get 100%, hard = <20 models get 100%)
  python display_results_csv.py results/whole_file --difficulty
  python display_results_csv.py results/whole_file --difficulty --csv

  # Combine split and difficulty
  python display_results_csv.py results/whole_file --split test --difficulty
        """
    )

    parser.add_argument(
        "results_dir",
        type=str,
        help="Path to directory containing JSON result files (e.g., results/whole_file)"
    )

    parser.add_argument(
        "--csv",
        action="store_true",
        help="Output as CSV format (comma-separated) for easy copy-paste to spreadsheets"
    )

    parser.add_argument(
        "--granular",
        action="store_true",
        help="Show per-question results instead of summary statistics"
    )

    parser.add_argument(
        "--split",
        type=str,
        choices=["test", "complete"],
        help="Filter results to only show questions from the specified dataset split"
    )

    parser.add_argument(
        "--difficulty",
        action="store_true",
        help="Show separate columns for easy (20+ models get 100%%) and hard (<20 models get 100%%) questions"
    )

    args = parser.parse_args()

    # Load results
    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"Error: Directory '{results_dir}' does not exist")
        return 1

    if not results_dir.is_dir():
        print(f"Error: '{results_dir}' is not a directory")
        return 1

    results = load_results(results_dir)

    if not results:
        print(f"Error: No JSON result files found in '{results_dir}'")
        return 1


    # Display results with filters
    filter_info = []
    if args.split:
        filter_info.append(f"split={args.split}")
    if args.difficulty:
        filter_info.append(f"showing easy/hard breakdown")

    if filter_info and not args.csv:
        print(f"Filters applied: {', '.join(filter_info)}\n")

    if args.granular:
        if args.difficulty:
            print("Warning: --difficulty flag has no effect with --granular mode")
        display_granular_table(results, csv_mode=args.csv, split=args.split)
    else:
        display_summary_table(results, csv_mode=args.csv, split=args.split, show_difficulty=args.difficulty)

    return 0


if __name__ == "__main__":
    exit(main())
