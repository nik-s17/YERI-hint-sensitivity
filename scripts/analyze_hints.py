#!/usr/bin/env python3
"""Analyze a four-variant hint experiment stored as CSV.

Usage:
    python analyze_hints.py results.csv
    python analyze_hints.py results.csv --json summary.json

Expected columns are Question Number, Answers, variants V1..V4 (T/F), their
correction columns, "V4 Used Hint?", and "Same Incorrect Answer as Hint?".
Question Number and Answers are retained for traceability but are not used in
the aggregate calculations. Column matching ignores case, spaces, underscores,
punctuation, and parentheses.
"T" and "F" are treated as correctness indicators; blank values are omitted.
"Corrections" means the model changed to the opposite truth value at some
point; it is not treated as an additional independent trial.
"V4 Used Hint?" is analyzed as self-reported reliance, not independently
verified hint use.
"Same Incorrect Answer as Hint?" is a separate outcome the experimenter
annotated; the script never infers it from correctness alone.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd


VARIANTS = ("V1", "V2", "V3", "V4")


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def find_column(columns, *aliases: str) -> str | None:
    lookup = {norm(column): column for column in columns}
    for alias in aliases:
        if norm(alias) in lookup:
            return lookup[norm(alias)]
    return None


def boolish(value: object):
    if pd.isna(value) or not str(value).strip():
        return None

    value = norm(value)

    if value in {"t", "true", "1", "yes", "y", "correct"}:
        return True
    if value in {"f", "false", "0", "no", "n", "incorrect"}:
        return False

    return None


def counts(values) -> dict:
    parsed = [boolish(value) for value in values]
    known = [value for value in parsed if value is not None]

    return {
        "n": len(known),
        "missing_or_unrecognized": len(parsed) - len(known),
        "yes": sum(known),
        "no": len(known) - sum(known),
        "yes_rate": sum(known) / len(known) if known else None,
    }


def make_graphs(summary: dict, output_dir: Path) -> list[Path]:
    """Save PNG charts for the main outcomes and return their paths."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    # Correctness rate by variant.
    data = summary["correctness_by_variant"]
    labels = list(data)
    rates = [data[label]["accuracy"] for label in labels]
    heights = [0 if rate is None else rate * 100 for rate in rates]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        labels,
        heights,
        color=["#5379a8", "#64a17b", "#d18b45", "#8b6aad"],
    )
    ax.set_ylim(0, 100)
    ax.set_ylabel("Correct (%)")
    ax.set_title("Accuracy by variant")
    ax.grid(axis="y", alpha=0.25)

    for bar, label, rate in zip(bars, labels, rates):
        text = (
            "no data"
            if rate is None
            else f"{rate:.1%} ({data[label]['correct']}/{data[label]['n']})"
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            text,
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    path = output_dir / "accuracy_by_variant.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # Paired answer changes from V3 to V4.
    paired = summary["paired_answer_comparisons"]["V4_vs_V3"]
    labels = [
        "V4 became correct",
        "V4 became incorrect",
        "Same answer",
    ]
    values = [
        paired["b_became_correct"],
        paired["b_became_incorrect"],
        paired["same"],
    ]
    colors = ["#2d9a72", "#d45d5d", "#8998a6"]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(labels, values, color=colors)
    ax.set_xlabel("Number of paired questions")
    ax.set_title(f"V4 compared with V3 (paired n={paired['n_paired']})")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(values + [1]) * 1.18)

    for bar, value in zip(bars, values):
        ax.text(
            value + 0.04,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
        )

    fig.tight_layout()
    path = output_dir / "v4_vs_v3_changes.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # Correction flags by variant.
    data = summary["corrections_by_variant"]
    labels = list(data)
    yes_values = [data[label]["yes"] for label in labels]
    no_values = [data[label]["no"] for label in labels]

    fig, ax = plt.subplots(figsize=(8, 5))
    positions = list(range(len(labels)))
    ax.bar(
        positions,
        yes_values,
        label="Correction marked T/Yes",
        color="#5c9b78",
    )
    ax.bar(
        positions,
        no_values,
        bottom=yes_values,
        label="Correction marked F/No",
        color="#cf9b54",
    )
    ax.set_xticks(positions, labels)
    ax.set_ylabel("Number of questions")
    ax.set_title("Correction flags by variant")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path = output_dir / "corrections_by_variant.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # Coded hint use and matching-hint outcomes, if data are present.
    disclosure = [
        (
            "V4 self-reported hint use",
            summary.get("v4_self_reported_hint_use"),
        ),
        (
            "Same incorrect answer as hint",
            summary.get("same_incorrect_answer_as_hint"),
        ),
    ]
    available = [
        (label, item)
        for label, item in disclosure
        if item is not None and item["n"] > 0
    ]

    if available:
        labels = [label for label, _ in available]
        yes_values = [item["yes"] for _, item in available]
        no_values = [item["no"] for _, item in available]

        fig, ax = plt.subplots(figsize=(8, 4.5))
        positions = list(range(len(labels)))
        ax.barh(
            positions,
            yes_values,
            label="Yes / True",
            color="#5379a8",
        )
        ax.barh(
            positions,
            no_values,
            left=yes_values,
            label="No / False",
            color="#c7d0d8",
        )
        ax.set_yticks(positions, labels)
        ax.set_xlabel("Number of coded responses")
        ax.set_title("Hint-use disclosure and hint-answer match")
        ax.legend()
        ax.grid(axis="x", alpha=0.25)
        ax.set_axisbelow(True)
        fig.tight_layout()
        path = output_dir / "hint_disclosure.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(path)

    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Input results CSV")
    parser.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        help="Also write the summary as JSON",
    )
    parser.add_argument(
        "--graphs-dir",
        type=Path,
        help="Folder for PNG charts (default: graphs beside the CSV)",
    )
    args = parser.parse_args()

    if not args.csv.is_file():
        parser.error(f"CSV file not found: {args.csv}")

    try:
        df = pd.read_csv(args.csv, dtype=str, keep_default_na=False)
    except Exception as exc:
        print(f"Could not read {args.csv}: {exc}", file=sys.stderr)
        return 2

    cols = df.columns
    answer_cols = {
        variant: find_column(
            cols,
            variant,
            f"{variant} (T/F)",
            f"{variant} T/F",
        )
        for variant in VARIANTS
    }
    corr_cols = {
        variant: find_column(
            cols,
            f"{variant} Corrections",
            f"{variant} Correction",
        )
        for variant in VARIANTS
    }
    use_col = find_column(
        cols,
        "V4 Used Hint?",
        "V4 Used Hint",
        "Used Hint?",
    )
    same_col = find_column(
        cols,
        "Same Incorrect Answer as Hint?",
        "Same Incorrect Answer as Hint",
    )

    missing = [
        variant
        for variant, column in answer_cols.items()
        if column is None
    ]

    if missing:
        parser.error(
            "Missing answer column(s): "
            + ", ".join(missing)
            + f". Found: {list(cols)}"
        )

    answers = {
        variant: df[column].map(boolish)
        for variant, column in answer_cols.items()
    }
    corrections = {
        variant: (
            df[column].map(boolish)
            if column
            else pd.Series([None] * len(df))
        )
        for variant, column in corr_cols.items()
    }

    def paired(a: str, b: str) -> dict:
        pairs = [
            (x, y)
            for x, y in zip(answers[a], answers[b])
            if x is not None and y is not None
        ]
        changes = sum(x != y for x, y in pairs)

        return {
            "n_paired": len(pairs),
            "same": len(pairs) - changes,
            "changed": changes,
            "b_became_correct": sum(not x and y for x, y in pairs),
            "b_became_incorrect": sum(x and not y for x, y in pairs),
        }

    summary = {
        "input": str(args.csv),
        "rows": len(df),
        "answer_columns": answer_cols,
        "correction_columns": corr_cols,
        "self_report_column": use_col,
        "same_hint_answer_column": same_col,
        "correctness_by_variant": {
            variant: {
                "n": sum(value is not None for value in answers[variant]),
                "missing_or_unrecognized": sum(
                    value is None for value in answers[variant]
                ),
                "correct": sum(value is True for value in answers[variant]),
                "incorrect": sum(value is False for value in answers[variant]),
                "accuracy": (
                    sum(value is True for value in answers[variant])
                    / sum(
                        value is not None
                        for value in answers[variant]
                    )
                    if any(
                        value is not None
                        for value in answers[variant]
                    )
                    else None
                ),
            }
            for variant in VARIANTS
        },
        "corrections_by_variant": {
            variant: counts(corrections[variant])
            for variant in VARIANTS
        },
        "paired_answer_comparisons": {
            "V4_vs_V3": paired("V3", "V4"),
            "V4_vs_V1": paired("V1", "V4"),
            "V4_vs_V2": paired("V2", "V4"),
        },
        "v4_self_reported_hint_use": (
            counts(df[use_col]) if use_col else None
        ),
        "same_incorrect_answer_as_hint": (
            counts(df[same_col]) if same_col else None
        ),
    }

    print(f"Rows: {summary['rows']}\n")
    print("Correctness (T/F parsed as correct/incorrect):")

    for variant, values in summary["correctness_by_variant"].items():
        accuracy = values["accuracy"]
        percent = "n/a" if accuracy is None else f"{accuracy:.1%}"

        print(
            f"  {variant}: {values['correct']}/{values['n']} correct "
            f"({percent}); {values['missing_or_unrecognized']} "
            "missing/unrecognized"
        )

    print("\nAnswer changes (paired rows with both answers present):")

    for comparison, values in summary["paired_answer_comparisons"].items():
        print(
            f"  {comparison}: {values['changed']} changed of "
            f"{values['n_paired']}; "
            f"V4 correct after incorrect={values['b_became_correct']}, "
            f"V4 incorrect after correct={values['b_became_incorrect']}"
        )

    print("\nCorrection flags:")

    for variant, values in summary["corrections_by_variant"].items():
        print(
            f"  {variant}: {values['yes']} yes, {values['no']} no "
            f"(n={values['n']}; "
            f"missing={values['missing_or_unrecognized']})"
        )

    print("\nV4 self-reported hint use:")

    if use_col:
        values = summary["v4_self_reported_hint_use"]
        print(
            f"  {values['yes']} yes, {values['no']} no "
            f"(n={values['n']})"
        )
    else:
        print("  column not found")

    print("Same incorrect answer as hint (experimenter-coded):")

    if same_col:
        values = summary["same_incorrect_answer_as_hint"]
        print(
            f"  {values['yes']} yes, {values['no']} no "
            f"(n={values['n']})"
        )
    else:
        print("  column not found")

    print(
        "\nInterpretation: the V4 vs V3 comparison is the closest estimate "
        "of the effect of the disclosure request, assuming those conditions "
        "differ only by that request. It is paired and descriptive; "
        "correctness alone does not establish whether a hint caused an answer."
    )

    question_col = find_column(cols, "Question Number")

    if question_col:
        identifiers = df[question_col].astype(str).str.strip()
        identifiers = identifiers[identifiers != ""]
        duplicate_ids = identifiers[identifiers.duplicated()].unique().tolist()

        if duplicate_ids:
            print(
                "\nNote: repeated question numbers found: "
                + ", ".join(duplicate_ids)
                + ". Confirm whether these are repeated runs or duplicate rows."
            )

    if args.json_path:
        args.json_path.write_text(
            json.dumps(summary, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nWrote JSON summary: {args.json_path}")

    graphs_dir = args.graphs_dir or args.csv.parent / "graphs"

    try:
        graph_paths = make_graphs(summary, graphs_dir)
    except ImportError as exc:
        print(f"Could not create charts: {exc}", file=sys.stderr)
        print(
            "Install the chart dependency with: "
            "python -m pip install matplotlib",
            file=sys.stderr,
        )
        return 2

    print(f"\nSaved {len(graph_paths)} graph(s) in: {graphs_dir}")

    for graph_path in graph_paths:
        print(f"  {graph_path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())