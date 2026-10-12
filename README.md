# YERI-hint-sensitivity

This repository contains the dataset, prompt construction files, experiment record, and analysis for a small study of how hints affect a language model's answers to multiple-choice mathematical questions.

## Research question and result

We asked: how does a model's answer correctness change when the same question is presented with no hint, a correct hint, or an incorrect hint? A fourth prompt version asked the model to reflect on an incorrect hint.

The final experiment used 20 questions and one recorded response for each of four prompt versions (80 prompts total). In the primary three-condition comparison, GPT-5.6 Luna answered 13/20 questions correctly with no hint (65%), 14/20 with a correct hint (70%), and 17/20 with an incorrect hint (85%). Compared with no hint, the correct-hint condition had 3 improvements and 2 declines; the incorrect-hint condition had 5 improvements and 1 decline.

These results are descriptive rather than definitive. The sample is small, uses one response per condition, and cannot establish that incorrect hints generally improve performance or that a hint caused any particular answer.

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
│   └── YERI Testing Data - Sheet1.csv  # Recorded model responses and scores
├── notebooks/
│   ├── hint_correctness_analysis.ipynb  # Nikhil's primary analysis
│   ├── hint_correctness_analysis.py      # Same analysis as a Python script
│   └── requirements.txt
├── scripts/
│   └── build_database.py          # Rebuilds and validates JSON/SQLite data
└── sources/
    ├── formatted_questions.txt    # Prompt source text
    └── answer_key.txt             # Supplied answer key
```

The `data/` directory contains the shared dataset and experiment data. The `notebooks/` directory contains the individual hint-sensitivity analysis. The `sources/` directory preserves the supplied source materials, while `scripts/` contains the reproducible database-building step.

## Database files

- [`data/questions.sqlite3`](data/questions.sqlite3): SQLite database, with one `questions` table containing exactly 20 rows.
- [`data/questions.json`](data/questions.json): the same 20 records in UTF-8 JSON for convenient import and inspection.

Each row contains four full prompts, including the question and numbered answer options:

1. `prompt_v1_base`: base prompt with the requested response instructions.
2. `prompt_v2_correct_hint`: adds an earlier participant's choice using the supplied correct answer.
3. `prompt_v3_incorrect_hint`: adds an earlier participant's choice using a user-specified incorrect option.
4. `prompt_v4_incorrect_hint_reflection`: uses the same incorrect hint as version 3 and asks whether and how the suggestion affected the answer.

Metadata includes sequential `question_id`, original `source_question_id`, question text, answer options, `correct_option`, `correct_answer_text`, and `incorrect_hint_option`. SQLite stores options as `answer_options_json`; JSON stores them as `answer_options` objects.

## Construction details

The formatted question wording and option order are preserved from the supplied collection, with the requested addition of question 2's tenth option, `-729`. Answer letters A–J from the supplied answer key are mapped to option numbers 1–10. “Correct” means correct according to that supplied key; the mathematical answers have not been independently verified or corrected. Source wording, ambiguities, and any answer-key errors remain intact.

Incorrect hints are fixed to the user-specified list, in question order: `7, 9, 2, 7, 5, 6, 4, 7, 2, 9, 10, 1, 1, 6, 1, 4, 9, 1, 9, 1`. Versions 3 and 4 share the same incorrect hint for each question. All questions now have ten options.

The `\\where (number) is right/wrong` annotations in the request describe construction rules; they are not included in the prompts. All four versions include the period after `words.` and versions 2–4 use literal numeric choices. No answer-key metadata is embedded in the question body.

## Rebuild and validate

Run `python3 scripts/build_database.py` using Python 3.8 or newer. Only the standard library is required. This rebuilds both database files and checks row count, option alignment, hint validity, the exact response-instruction endings, SQLite integrity, and JSON parity.

The original supplied files are preserved in [`sources/`](sources/).

## Testing data and statistical analysis

The supplied testing CSV is preserved unchanged at [`data/YERI Testing Data - Sheet1.csv`](data/YERI%20Testing%20Data%20-%20Sheet1.csv).

Open [`notebooks/hint_correctness_analysis.ipynb`](notebooks/hint_correctness_analysis.ipynb) in Jupyter and run all cells. Install the packages with `%pip install numpy pandas scipy matplotlib statsmodels` in a notebook cell if needed. The same code is also available in [`notebooks/hint_correctness_analysis.py`](notebooks/hint_correctness_analysis.py), separated into notebook-style cells. Python 3.9 or newer is recommended. Run the notebook from the repository root or its `notebooks` directory; otherwise set `CSV_PATH` to your downloaded file.

The notebook compares V1, V2, and V3 using question-paired binary outcomes. It includes accuracy plots with 95% Wilson intervals, improvement/decline counts, question-level heatmaps, an exact conditional omnibus test using Cochran's Q, and two-sided exact McNemar tests with Holm correction across three comparisons. Original T/F scores are the primary analysis; a separately labeled sensitivity analysis assumes nonblank correction entries replace the original scores. It validates question IDs and T/F labels, excludes blank-ID note rows, and checks the CSV answer key against the prompt database when available. Free-text CSV notes are data, not requests to execute additional experiments.

Interpretation is limited to the recorded responses and scoring labels. Twenty selected questions with one response per condition provide limited power and do not measure model sampling variability. The notebook explains the independence and exchangeability assumptions and why nonsignificance does not establish equivalence.

## Use for prompting

Clone this private repository while authenticated, or download `data/questions.json` from its GitHub file page. Each `prompt_v*` field is already a complete string containing the question, options, and response instructions. Send one such string as the user message for an independent model call; no option reconstruction is required.

```python
import json
from pathlib import Path

rows = json.loads(Path("data/questions.json").read_text(encoding="utf-8"))
prompt = rows[0]["prompt_v3_incorrect_hint"]
print(prompt)  # Send this string as your model's user message.

# Optional: inspect only the option texts.
option_texts = [option["text"] for option in rows[0]["answer_options"]]
```

To evaluate all 80 prompts, loop over the 20 records and their four `prompt_v*` fields. Use a fresh conversation for each prompt so earlier versions do not influence later ones. Keep the model and generation settings consistent, and save the question ID, version, model response, and returned option number. Compare that number with `correct_option` for scoring against the supplied key. Keep answer-key metadata outside the model's input.
