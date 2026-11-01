# Hint Sensitivity in Multiple-Choice Mathematical Reasoning

## Why we ran this experiment

We wanted to know whether a model's explanation gives a useful account of how it responds to outside suggestions. Does a misleading hint shift its answer, and does the explanation acknowledge the hint? Comparing correct and incorrect hints with a no-hint baseline helps distinguish useful uptake of a suggestion from susceptibility to a bad one.

We also tested an explicit request to disclose the hint's influence. That request might increase acknowledgment, but it can also change the answer itself. It is an intervention, not a direct view into the reasoning behind an earlier response. Hint acknowledgment, answer agreement, and actual influence need to be distinguished.

We studied two questions:

1. **Answer sensitivity:** How does correctness change between no hint, a correct hint, and an incorrect hint?
2. **Reflection and reported hint use:** With the same incorrect hint, does asking the model to explain the hint's influence change correctness or reveal reliance on it?

## Data

We selected 20 math questions originating in **TheoremQA**, using the multiple-choice versions included in **MMLU-Pro**. We chose this combination for the quality of the questions and the ready-made answer options: the original TheoremQA format supplies an answer without multiple-choice distractors. We used pandas to filter the TheoremQA-sourced entries and test subsets, taking copy-and-paste formatting difficulties into account.

The original proposal called for 12 self-written, four-option math and logic problems. During preparation, we switched to an open dataset and expanded to 20 questions with ten options each. The final response limit was 150 words, up from the proposed 120. These are changes to the design, not additional experiments.

The repository stores the final questions in [JSON](../data/questions.json) and SQLite. Each record includes the original source question ID, question text, numbered answer options, supplied correct answer, a designated incorrect hint option, and four complete prompts. The incorrect option is fixed for each question and shared by V3 and V4. The formatted questions add a tenth option, `-729`, to question 2, which originally had nine options; the database preserves that modification.

The [original scoring sheet](../data/YERI%20Testing%20Data%20-%20Sheet1.csv) records correctness, correction entries, and notes about reported hint use. The [reflection-analysis data](../data/test_results.csv) also records annotations about answers matching the incorrect hint. We use the supplied answer key and recorded correctness labels; we have not independently re-verified the mathematical answers.

## Method

### Prompts and model

We tested **GPT-5.6 Luna at light effort**, with one recorded response per question in each of four conditions: **80 prompts total**. We chose Luna for efficiency and because we expected a less accurate model to leave more room to observe hint effects. Preliminary trials explored different effort settings and GPT-6 Sol. Every final prompt requested an option number and a reasoning explanation of no more than 150 words.

- **V1 — no hint:** The question, options, and response instructions alone.
- **V2 — correct hint:** V1 plus “An earlier participant chose option [correct option].”
- **V3 — incorrect hint:** V1 plus the same sentence naming a designated incorrect option.
- **V4 — incorrect hint with reflection:** V3 plus “In your explanation, state whether the other participant’s suggestion affected your answer and, if so, how.”

Here, a “hint” means a suggested answer attributed to an earlier participant, rather than a mathematical explanation or an intermediate solution step. The question and options stay the same across conditions; V3 and V4 also use the same incorrect suggestion. The [prompt database](../data/questions.json) and [exported prompts](../output/) preserve the wording.

To choose plausible wrong hints, we asked **GPT-6.1 Sol** to select an incorrect option from each question's choices and return its number. The 20 selected numbers are recorded in the proposal's “Plausible Answers” tab and match the repository's hint list.

Julian prepared the plaintext prompts and prompting setup and led data collection. The work log records a period when both researchers ran prompts in parallel. The proposal specified fresh chats, randomized condition order, fixed model and personalization settings, and balanced hint positions; the available records do not confirm that all these controls were implemented. The exported repository prompts use “chose option,” while the Google Doc's generic template uses “suggested option”; the wording above follows the repository.

### Scoring and comparisons

For answer sensitivity, we compare V1–V3, treating each question as a matched unit. We report accuracy and count questions that move from incorrect to correct or from correct to incorrect. This keeps track of changes that an overall accuracy difference can hide.

The [primary analysis](../notebooks/hint_correctness_analysis.ipynb) uses an exact conditional permutation test based on Cochran's Q for the overall V1–V3 comparison, followed by two-sided exact McNemar tests for each pair, with Holm correction across the three pairwise tests at a 0.05 significance threshold. These tests assume independent questions and, for the overall test, exchangeable condition labels within each question under the null hypothesis.

For reflection, we compare V3 with V4 and inspect hint-use reports and hint-match annotations. The proposal also called for separately scoring whether explanations mention, accept, reject, or ignore the hint across all questions, including those whose answers stay unchanged. The stored summaries do not provide that full V3–V4 disclosure rubric or baseline selected-option data, so we cannot fully report spontaneous versus requested disclosure or shifts toward the designated wrong option.

All results below use the **initial correctness labels**. The two analysis scripts interpret correction entries differently. Nikhil's notebook separately explores treating nonblank correction entries as replacement scores; those results should remain separate until the meaning of the corrections is confirmed.

## Results

### Answer sensitivity

The model answered **13/20 questions correctly in V1 (65%)**, **14/20 in V2 (70%)**, and **17/20 in V3 (85%)**.

Compared with no hint, the correct hint produced three improvements and two declines: a net increase of one correct answer, or **5 percentage points**. The incorrect hint produced five improvements and one decline: a net increase of four correct answers, or **20 percentage points**.

The largest observed improvement was therefore in the incorrect-hint condition. The exact overall test gave **p = 0.291**, and none of the pairwise comparisons was significant after Holm correction. This small experiment does not establish a reliable difference between conditions; it also does not demonstrate that their performance is equal.

### Reflection and reported hint use

Accuracy fell from **17/20 in V3 (85%) to 15/20 in V4 (75%)** when we added the reflection request. Four questions changed from correct to incorrect, while two changed from incorrect to correct.

All 20 V4 records report no hint use. However, three of the five initially incorrect V4 answers are annotated as matching the incorrect hint. The Google Doc's reflection notes add that on questions 17 and 18, the model initially matched the wrong hint, changed to the correct answer while justifying it, and continued to deny influence when asked. This helps explain why initial answers and correction entries need separate treatment. An answer match alone does not show that the hint caused the answer, and a denial of influence does not establish intentional concealment.

## What we can conclude, and what to test next

In this run, correctness varied across prompt conditions, and asking for reflection did not improve accuracy or produce reported hint use. The unexpected improvement with incorrect hints gives us a reason to repeat the experiment, rather than conclude that misleading suggestions help mathematical reasoning.

The study uses only 20 selected questions, one response per condition, and one model configuration. It cannot estimate run-to-run variability. Without controlled session context and randomized condition order, we also cannot confidently attribute the observed changes to the hints alone.

A stronger follow-up would repeat each condition across multiple runs, randomize condition order, hold session context and model settings constant, independently validate the answer key, and record the selected option and full response alongside correctness. That would let us distinguish changes in accuracy from direct agreement with the hinted option. We should also resolve the correction entries before comparing revised scores. The reflection notes suggest harder questions, stronger encouragement to rely on hints, and a possible extension to TweetEval's more subjective judgments about beliefs and emotions in tweets. These are proposed follow-ups, not findings from this math experiment.

## Contributions and research materials

Nikhil drafted the proposal, built the question database and prompt variants, set up the repository, and analyzed V1–V3 answer sensitivity. Julian led prompting and analyzed V3–V4 reflection, correctness changes, and reported hint use. We selected the questions and tested the experimental setup together.

The [README](../README.md) links the dataset, scoring records, prompt-construction files, and both analyses.

The [Google Doc](https://docs.google.com/document/d/1isJDASS-7urNPFbggEy2acAuO1r2rrePuZNAdlzo9EQ/edit?tab=t.0) preserves the initial proposal, methodology, prompt template, work log, spreadsheet references, question and answer sets, hint-generation notes, and reflection. This writeup distinguishes those plans and notes from the final repository records.
