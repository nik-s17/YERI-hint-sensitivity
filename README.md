# YERI-hint-sensitivity

A four-way paired prompt dataset containing 20 questions and 80 prompts.

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
