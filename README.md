# YERI-hint-sensitivity

This repository contains the dataset, prompt construction files, experiment record, and analysis for a small study of how hints affect a language model's answers to multiple-choice mathematical questions. We used 20 questions originating in **TheoremQA**, specifically the multiple-choice versions included in **MMLU-Pro**, within a four-condition hint framework to study GPT-5.6 Luna's answer sensitivity and reported hint use.

## Research question and result

The proposal framed the project around two related questions: **how hints affect answer correctness**, and **how asking the model to reflect on a hint affects its answer and its account of hint use**. We tested GPT-5.6 Luna at light effort on 20 questions, with one recorded response for each of four prompt versions (80 prompts total).

**Nikhil's question compared V1, V2, and V3:** does correctness change with no hint, a correct hint, or an incorrect hint? The model answered 13/20 questions correctly in V1 (65%), 14/20 in V2 (70%), and 17/20 in V3 (85%). The largest observed increase was therefore in the incorrect-hint condition: 20 percentage points above the no-hint condition.

**Julian's question compared V3 and V4:** when both contain the same incorrect hint, does adding a request to explain whether the hint influenced the answer change correctness or reveal reliance on the hint? Accuracy fell from 17/20 in V3 (85%) to 15/20 in V4 (75%). All 20 V4 records reported no hint use, although three of the five initially incorrect V4 answers were annotated as matching the incorrect hint.

These results describe a small sample with one response per condition. They do not establish that incorrect hints generally improve performance, or that matching a hint proves influence or intentional concealment. Results here use the initial correctness labels; the two analyses interpret correction entries differently, and the supplied answer key has not been independently verified.

For the fuller research writeup, see [`docs/research_writeup.md`](docs/research_writeup.md).

## Repository tree

```text
.
├── README.md
├── docs/
│   └── research_writeup.md       # Printable research summary
├── data/
│   ├── questions.json            # 20 questions and four complete prompts each
│   ├── questions.sqlite3         # Same dataset in SQLite format
│   ├── YERI Testing Data - Sheet1.csv  # Original scoring sheet and notes
│   ├── test_results.csv           # Experiment scores with hint-match annotations
│   └── graphs/                   # Julian's exported analysis charts
├── notebooks/
│   ├── hint_correctness_analysis.ipynb  # Nikhil's primary analysis
│   ├── hint_correctness_analysis.py      # Same analysis as a Python script
│   └── requirements.txt
├── scripts/
│   ├── build_database.py          # Rebuilds and validates JSON/SQLite data
│   ├── generate_questions.py      # Exports prompts to readable text and JSON
│   └── analyze_hints.py           # Julian's reflection/hint-disclosure analysis
├── output/
│   ├── all_prompts.json           # Exported prompt collection
│   ├── v1.txt … v4.txt            # Plaintext prompts for each condition
│   └── hint_analysis_graphs/      # Additional saved analysis charts
└── sources/
    ├── formatted_questions.txt    # Prompt source text
    └── answer_key.txt             # Supplied answer key
```

The `data/` directory contains the shared dataset and experiment data. Nikhil's individual hint-sensitivity analysis is in `notebooks/`; Julian's analysis is in `scripts/analyze_hints.py`, with saved charts in `data/graphs/` and `output/hint_analysis_graphs/`. The `sources/` directory preserves the supplied source materials, while `scripts/` also contains the database-building and prompt-export steps. The repository additionally contains `.idea/` editor configuration files, omitted from the research file tree above.

## Individual analyses

**Nikhil — answer sensitivity to hints.** The [analysis notebook](notebooks/hint_correctness_analysis.ipynb) compares V1–V3 using paired correctness outcomes. Accuracy was 65% without a hint, 70% with a correct hint, and 85% with an incorrect hint. Relative to V1, V2 produced three improvements and two declines (+5 percentage points), while V3 produced five improvements and one decline (+20 percentage points). The analysis examines whether hint conditions differ in correctness and discusses the limits of this small experiment.

**Julian — reflection and reported hint use.** The [analysis script](scripts/analyze_hints.py) uses [test_results.csv](data/test_results.csv) to examine V3–V4 changes and hint-use reports. Accuracy fell from 85% to 75% when the reflection request was added: four questions declined and two improved. All 20 V4 records reported no hint use, while three of five initially incorrect answers matched the incorrect hint according to experimenter annotations. The analysis examines this discrepancy, which warrants further testing but does not by itself establish influence or concealment.

## Dataset source

The questions were selected from the TheoremQA-sourced entries in MMLU-Pro. We used the question versions and multiple-choice answer options provided in MMLU-Pro, rather than the original answer-only TheoremQA format, and added the no-hint, correct-hint, incorrect-hint, and reflection variants for this experiment.

## Database files

- [`data/questions.sqlite3`](data/questions.sqlite3): SQLite database, with one `questions` table containing exactly 20 rows.
- [`data/questions.json`](data/questions.json): the same 20 records in UTF-8 JSON for convenient import and inspection.

Each row contains four full prompts, including the question and numbered answer options:

1. `prompt_v1_base`: base prompt with the requested response instructions.
2. `prompt_v2_correct_hint`: adds an earlier participant's choice using the supplied correct answer.
3. `prompt_v3_incorrect_hint`: adds an earlier participant's choice using a user-specified incorrect option.
4. `prompt_v4_incorrect_hint_reflection`: uses the same incorrect hint as version 3 and asks whether and how the suggestion affected the answer.

Metadata includes sequential `question_id`, original `source_question_id`, question text, answer options, `correct_option`, `correct_answer_text`, and `incorrect_hint_option`. SQLite stores options as `answer_options_json`; JSON stores them as `answer_options` objects.
