# Hint Sensitivity in Multiple-Choice Mathematical Reasoning

## Research question

How does adding a hint to a multiple-choice mathematical question affect a language model's answer? In particular, we compared a prompt with no hint, a prompt containing the correct answer as a hint, and a prompt containing an incorrect answer as a hint. We also recorded a fourth condition that asked the model to reflect on an incorrect hint, although that condition is not part of the primary analysis.

## Project design and responsibilities

Nikhil drafted the original proposal, including the research question, prompt types, templates, and planned individual analyses. Nikhil and Julian collaboratively selected and prepared the questions. Nikhil used Jupyter and pandas to filter and organize TheoremQA questions, align them with the multiple-choice options available in MMLU-Pro, and create the final 20-question dataset. Nikhil also set up the GitHub repository, created the question database and prompt variants, and documented the research process.

Julian converted the selected questions into the final plaintext prompting format, generated the hints, configured the prompting setup, and ran the experiment using GPT-5.6 Luna at light effort. Together, Nikhil and Julian tested candidate datasets, models, and prompt formats before conducting the final experiment.

After the experiment, Nikhil analyzed answer sensitivity to hints and prepared the reflection and proposed next steps. The repository contains the shared dataset and experiment records, Nikhil's analysis notebook, and the source files used to construct the prompts.

## Data and method

The final dataset contains 20 selected questions and four prompt versions per question, for 80 total prompts:

1. no hint;
2. a correct hint;
3. an incorrect hint; and
4. an incorrect hint followed by a request for reflection.

The primary analysis compares the first three conditions using the recorded true/false correctness labels. It treats each question as a matched unit and reports accuracy, paired changes, and exact paired tests. The supplied answer key is used as recorded; the mathematical answers were not independently re-verified.

## Results

On the 20 recorded questions, the model answered 13 correctly with no hint (65%), 14 correctly with a correct hint (70%), and 17 correctly with an incorrect hint (85%). Relative to the no-hint condition, the correct-hint condition produced three improvements and two declines, for a net change of +5 percentage points. The incorrect-hint condition produced five improvements and one decline, for a net change of +20 percentage points.

These results suggest that the model's correctness was sensitive to the presence and content of hints in this small sample, with the largest observed improvement occurring in the incorrect-hint condition. However, the experiment does not establish that incorrect hints generally improve performance. It used only 20 questions, one recorded response per condition, and a single model/configuration. The correctness labels alone also do not show whether an incorrect answer was caused by following the hint. Repeated runs, randomized condition order, explicit recording of selected options, and independent validation of the answer key would be needed for a stronger conclusion.

## Repository contents

See the repository README for the file tree, reproducibility instructions, and links to the data, experiment record, prompt-construction script, and analysis notebook.
