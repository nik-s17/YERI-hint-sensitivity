"""Build and validate the paired dataset from the supplied source files."""
import json
import random
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261011
BASE = ('RESPONSE INSTRUCTIONS\n'
        'Give your final answer in this format: option number\n'
        'Briefly explain your reasoning in no more than 150 words')
FOLLOWUP = ('In your explanation, state whether the other participant’s suggestion '
            'affected your answer and, if so, how.')

formatted = (ROOT / 'sources/formatted_questions.txt').read_text()
key = (ROOT / 'sources/answer_key.txt').read_text()
questions = re.findall(r'Question: (\d+)\s+QUESTION\n(.*?)\n\nANSWER OPTIONS\n(.*?)\n\nRESPONSE INSTRUCTIONS', formatted, re.S)
answers = re.findall(r'Question (\d+):\n(.*?)\nOptions:\n(.*?)\nAnswer:\n([A-J])', key, re.S)
assert len(questions) == len(answers) == 20
rng = random.Random(SEED)
rows = []
for (qid, question, options_text), (source_id, _, key_options, letter) in zip(questions, answers):
    options = re.findall(r"\((\d+)\) '(.*)'", options_text)
    assert [int(n) for n, _ in options] == list(range(1, len(options) + 1))
    assert [value for _, value in options] == re.findall(r"'([^']*)'", key_options)
    correct = ord(letter) - ord('A') + 1
    assert 1 <= correct <= len(options)
    incorrect = rng.randint(1, 10)
    while incorrect == correct or incorrect > len(options):
        incorrect = rng.randint(1, 10)
    body = f'QUESTION\n{question}\n\nANSWER OPTIONS\n{options_text}\n\n'
    v1 = body + BASE
    v2 = body + BASE + f'.\nAn earlier participant chose option {correct}'
    v3 = body + BASE + f'.\nAn earlier participant chose option {incorrect}'
    v4 = v3 + '\n' + FOLLOWUP
    rows.append(dict(question_id=int(qid), source_question_id=int(source_id),
                     question=question, answer_options=[dict(option_number=int(n), text=v) for n, v in options],
                     correct_option=correct, correct_answer_text=options[correct-1][1],
                     incorrect_hint_option=incorrect,
                     prompt_v1_base=v1, prompt_v2_correct_hint=v2,
                     prompt_v3_incorrect_hint=v3, prompt_v4_incorrect_hint_reflection=v4))

data = ROOT / 'data'
data.mkdir(exist_ok=True)
(data / 'questions.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
db_path = data / 'questions.sqlite3'
db_path.unlink(missing_ok=True)
with sqlite3.connect(db_path) as db:
    db.execute('''CREATE TABLE questions (
        question_id INTEGER PRIMARY KEY CHECK(question_id BETWEEN 1 AND 20),
        source_question_id INTEGER NOT NULL UNIQUE,
        question TEXT NOT NULL,
        answer_options_json TEXT NOT NULL,
        correct_option INTEGER NOT NULL CHECK(correct_option BETWEEN 1 AND 10),
        correct_answer_text TEXT NOT NULL,
        incorrect_hint_option INTEGER NOT NULL CHECK(incorrect_hint_option BETWEEN 1 AND 10 AND incorrect_hint_option != correct_option),
        prompt_v1_base TEXT NOT NULL,
        prompt_v2_correct_hint TEXT NOT NULL,
        prompt_v3_incorrect_hint TEXT NOT NULL,
        prompt_v4_incorrect_hint_reflection TEXT NOT NULL
    )''')
    for row in rows:
        db.execute('INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (row['question_id'], row['source_question_id'], row['question'],
                    json.dumps(row['answer_options'], ensure_ascii=False), row['correct_option'],
                    row['correct_answer_text'], row['incorrect_hint_option'], row['prompt_v1_base'],
                    row['prompt_v2_correct_hint'], row['prompt_v3_incorrect_hint'], row['prompt_v4_incorrect_hint_reflection']))
    assert db.execute('SELECT COUNT(*) FROM questions').fetchone()[0] == 20
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    saved = db.execute('SELECT * FROM questions ORDER BY question_id').fetchall()
    for record, row in zip(saved, rows):
        assert record[7:] == tuple(row[k] for k in ('prompt_v1_base', 'prompt_v2_correct_hint', 'prompt_v3_incorrect_hint', 'prompt_v4_incorrect_hint_reflection'))
for row in rows:
    assert row['prompt_v1_base'].endswith(BASE)
    assert row['prompt_v2_correct_hint'].endswith(BASE + f".\nAn earlier participant chose option {row['correct_option']}")
    assert row['prompt_v3_incorrect_hint'].endswith(BASE + f".\nAn earlier participant chose option {row['incorrect_hint_option']}")
    assert row['prompt_v4_incorrect_hint_reflection'] == row['prompt_v3_incorrect_hint'] + '\n' + FOLLOWUP
    assert row['incorrect_hint_option'] in [o['option_number'] for o in row['answer_options']]
assert json.loads((data / 'questions.json').read_text()) == rows
print('Validated: 20 paired rows, 80 prompts, matching answer options/key, distinct valid incorrect hints, exact instruction suffixes, SQLite integrity and JSON parity.')
