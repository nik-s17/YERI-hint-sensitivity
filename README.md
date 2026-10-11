# YERI-hint-sensitivity

A four-way paired prompt dataset containing 20 questions and 80 prompts.

## Database files

- [`data/questions.sqlite3`](data/questions.sqlite3): SQLite database, with one `questions` table containing exactly 20 rows.
- [`data/questions.json`](data/questions.json): the same 20 records in UTF-8 JSON for convenient import and inspection.

Each row contains four full prompts, including the question and numbered answer options:

1. `prompt_v1_base`: base prompt with the requested response instructions.
2. `prompt_v2_correct_hint`: adds an earlier participant's choice using the supplied correct answer.
3. `prompt_v3_incorrect_hint`: adds an earlier participant's choice using a randomly selected incorrect option.
4. `prompt_v4_incorrect_hint_reflection`: uses the same incorrect hint as version 3 and asks whether and how the suggestion affected the answer.

Metadata includes sequential `question_id`, original `source_question_id`, question text, answer options, `correct_option`, `correct_answer_text`, and `incorrect_hint_option`. SQLite stores options as `answer_options_json`; JSON stores them as `answer_options` objects.

## Construction details

The formatted question wording and option order are preserved from the supplied collection. Answer letters A–J from the supplied answer key are mapped to option numbers 1–10. “Correct” means correct according to that supplied key; the mathematical answers have not been independently verified or corrected. Source wording, ambiguities, and any answer-key errors remain intact.

Incorrect hints are random integers drawn from 1–10, with draws rejected if they match the supplied correct option or refer to an unavailable option. Question 2 has only nine options, so its hint must be 1–9. The random seed is `20261011` so regeneration preserves the pairings.

The `\\where (number) is right/wrong` annotations in the request describe construction rules; they are not included in the prompts. Version 1 ends with `words` without a period, as requested. Versions 2–4 include the period after `words.` and use literal numeric choices. No answer-key metadata is embedded in the question body.

## Rebuild and validate

Run `python3 scripts/build_database.py` using Python 3.8 or newer. Only the standard library is required. This rebuilds both database files and checks row count, option alignment, hint validity, the exact response-instruction endings, SQLite integrity, and JSON parity.

The original supplied files are preserved in [`sources/`](sources/).
