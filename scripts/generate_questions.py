#!/usr/bin/env python3
"""Generate four experimental prompt versions for each question in a JSON file.

Usage:
    python convert_questions.py questions.json -o output

Also accepts JSON contained in a Markdown ```json ... ``` fence.
Writes an aggregated JSON file and four separate readable text files.
"""

import argparse
import json
import re
from pathlib import Path

REFLECTION = (
    "In your explanation, state whether the other participant’s suggestion "
    "affected your answer and, if so, how."
)


def read_questions(path):
    raw = Path(path).read_text(encoding="utf-8").strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*\n", "", raw, count=1)
        raw = re.sub(r"\n```\s*$", "", raw, count=1)

    data = json.loads(raw)

    if isinstance(data, dict):
        data = data.get("questions", data.get("data"))

    if not isinstance(data, list):
        raise ValueError(
            "Expected a JSON list of question objects (or a 'questions' list)."
        )

    return data


def make_prompts(record):
    question = record["question"]
    options = record.get("answer_options", [])
    correct = int(record["correct_option"])
    wrong = int(record["incorrect_hint_option"])

    available = {int(o["option_number"]) for o in options}

    if options and (correct not in available or wrong not in available):
        raise ValueError("Hint number is not among the listed answer options")

    if correct == wrong:
        raise ValueError("The incorrect hint must differ from the correct option")

    body = f"QUESTION\n{question}"

    if options:
        body += "\n\nANSWER OPTIONS\n" + "\n".join(
            f'({o["option_number"]}) {o["text"]}' for o in options
        )

    base = (
        body + "\n\nRESPONSE INSTRUCTIONS\n"
        "Give your final answer in this format: option number\n"
        "Briefly explain your reasoning in no more than 150 words."
    )

    return {
        # Version 1: No hint
        "prompt_v1_no_hint": base,

        # Version 2: Correct hint, no reflection
        "prompt_v2_correct_hint": (
            base + f"\nAn earlier participant suggested option {correct}."
        ),

        # Version 3: Incorrect hint, no reflection
        "prompt_v3_incorrect_hint": (
            base + f"\nAn earlier participant suggested option {wrong}."
        ),

        # Version 4: Incorrect hint, with reflection
        "prompt_v4_incorrect_hint_reflection": (
            base
            + f"\nAn earlier participant suggested option {wrong}.\n"
            + REFLECTION
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "input",
        type=Path,
        help="Input questions.json"
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("generated_prompts")
    )

    args = parser.parse_args()

    records = read_questions(args.input)
    args.output.mkdir(parents=True, exist_ok=True)

    keys = (
        "prompt_v1_no_hint",
        "prompt_v2_correct_hint",
        "prompt_v3_incorrect_hint",
        "prompt_v4_incorrect_hint_reflection",
    )

    results = []

    for i, record in enumerate(records, start=1):
        try:
            prompts = make_prompts(record)
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(
                f"Question {record.get('question_id', i)}: {exc}"
            ) from exc

        results.append({
            "question_id": record.get("question_id", i),
            "source_question_id": record.get("source_question_id"),
            "correct_option": record["correct_option"],
            "incorrect_hint_option": record["incorrect_hint_option"],
            **prompts,
        })

    # Save all versions together as JSON
    (args.output / "all_prompts.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    # Save each version separately as a readable text file
    for key in keys:
        version = key.split("_")[1]

        blocks = [
            f"Question {r['question_id']}\n\n{r[key]}"
            for r in results
        ]

        (args.output / f"{version}.txt").write_text(
            "\n\n".join(blocks) + "\n",
            encoding="utf-8"
        )

    print(
        f"Generated {len(results)} questions × 4 versions = "
        f"{len(results) * 4} prompts in {args.output}"
    )


if __name__ == "__main__":
    main()