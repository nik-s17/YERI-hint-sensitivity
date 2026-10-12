# %% [markdown]
# # Hint effects on answer correctness
# Each question is a matched unit with outcomes in V1 (no hint), V2 (correct
# hint), and V3 (incorrect hint). T=1 and F=0. This analysis uses the supplied
# correctness labels, not an independent mathematical check of the answer key.
# The original labels are primary. A sensitivity analysis treats nonblank
# correction entries as replacement scores; confirm that interpretation before
# reporting corrected results. Free-text notes and V4 are outside this analysis.
#
# Tests: exact conditional permutation test using Cochran's Q for the overall
# comparison; two-sided exact McNemar tests for the three pairs; Holm correction
# within each scoring scenario. The corrected scenario is exploratory, not a
# second opportunity to obtain significance. Alpha=0.05.
#
# Assumptions: independent questions; exchangeable version labels within a
# question under the omnibus null. These 20 selected questions and one recorded
# answer per version do not estimate run-to-run variability or establish causal
# effects if sessions, model settings, or question order differed.
#
# Install if needed in a notebook cell:
# `%pip install numpy pandas scipy matplotlib statsmodels`

# %%
from pathlib import Path
from collections import defaultdict
from itertools import permutations, combinations
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.stats import binomtest
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.contingency_tables import cochrans_q
from IPython.display import display

CSV_NAME = 'YERI Testing Data - Sheet1.csv'
# Works from the repository root, its notebooks folder, or beside the CSV.
candidates = [Path('data') / CSV_NAME, Path('../data') / CSV_NAME, Path(CSV_NAME)]
CSV_PATH = next((p for p in candidates if p.exists()), None)
if CSV_PATH is None:
    raise FileNotFoundError('Set CSV_PATH to the downloaded testing CSV.')
ALPHA = 0.05
VERSIONS = ['V1', 'V2', 'V3']
LABELS = ['V1: no hint', 'V2: correct hint', 'V3: incorrect hint']

# %%
raw = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
raw.columns = raw.columns.str.strip()
ids = raw['Question Number'].str.strip()
# Blank-ID rows contain trailing notes, not experimental observations.
if (ids.ne('') & ~ids.str.fullmatch(r'\d+')).any():
    raise ValueError('Unexpected nonnumeric question ID.')
data = raw.loc[ids.ne('')].copy()
data.index = data['Question Number'].astype(int)
data = data.sort_index()
if data.index.duplicated().any() or set(data.index) != set(range(1, 21)):
    raise ValueError('Expected unique question IDs 1–20.')

def decode(series, allow_blank=False):
    values = series.str.strip().str.upper()
    allowed = ['T', 'F', ''] if allow_blank else ['T', 'F']
    if not values.isin(allowed).all():
        raise ValueError(f'Invalid/missing T/F scores in {series.name}')
    return values.map({'T': 1, 'F': 0})

original = pd.DataFrame({v: decode(data[f'{v} (T/F)']) for v in VERSIONS}).astype(int)
corrected = original.copy()
changes = []
for version in VERSIONS:
    column = f'{version} Corrections'
    if column not in data.columns:
        continue
    overrides = decode(data[column], allow_blank=True)
    for qid in overrides.dropna().index:
        before, after = int(original.loc[qid, version]), int(overrides.loc[qid])
        corrected.loc[qid, version] = after
        changes.append({'question': qid, 'version': version,
                        'original': before, 'correction': after, 'changed': before != after})
print(f'Loaded {len(data)} paired questions. Excluded {len(raw)-len(data)} blank-ID note rows.')
print('Correction entries (including entries that leave the score unchanged):')
display(pd.DataFrame(changes))
# Optional check that supplied answer numbers match the prompt database.
db_path = CSV_PATH.parent / 'questions.json'
if db_path.exists():
    key = {r['question_id']: r['correct_option'] for r in json.loads(db_path.read_text())}
    if any(int(data.loc[q, 'Answers']) != key[q] for q in data.index):
        raise ValueError('CSV answer key differs from the prompt database.')

# %% [markdown]
# ## Statistical functions
# An exact omnibus distribution is computed by permuting version labels within
# each question while preserving that question's total correct responses.
# Dynamic programming combines identical column-total outcomes, avoiding a
# large explicit permutation list. The asymptotic Q p-value is included only
# for reference; the exact conditional p-value is the primary omnibus result.
# McNemar uses only discordant pairs (improvements versus declines).

# %%
def exact_cochran_q(frame):
    x = frame.to_numpy(dtype=int)
    totals = x.sum(axis=0)
    row_totals = x.sum(axis=1)
    total = int(totals.sum())
    denominator = int(3 * total - (row_totals ** 2).sum())
    if denominator == 0:
        return {'Q': 0.0, 'p_exact': 1.0, 'p_asymptotic': 1.0}
    q = 2 * (3 * int((totals ** 2).sum()) - total ** 2) / denominator
    observed_score = int((totals ** 2).sum())
    states = {(0, 0, 0): 1}
    for row in x:
        arrangements = set(permutations(map(int, row)))
        updated = defaultdict(int)
        for state, count in states.items():
            for arrangement in arrangements:
                updated[tuple(a+b for a, b in zip(state, arrangement))] += count
        states = updated
    extreme = sum(count for state, count in states.items()
                  if sum(v*v for v in state) >= observed_score)
    return {'Q': q, 'p_exact': extreme / sum(states.values()),
            'p_asymptotic': float(cochrans_q(x).pvalue)}

def analyze(frame):
    n = len(frame)
    accuracy = []
    for v in VERSIONS:
        successes = int(frame[v].sum())
        lo, hi = proportion_confint(successes, n, alpha=ALPHA, method='wilson')
        accuracy.append({'version': v, 'correct': successes, 'n': n,
                         'accuracy': successes/n, 'ci_low': lo, 'ci_high': hi})
    pairs = []
    for a, b in combinations(VERSIONS, 2):
        improved = int(((frame[a] == 0) & (frame[b] == 1)).sum())
        declined = int(((frame[a] == 1) & (frame[b] == 0)).sum())
        discordant = improved + declined
        p = binomtest(improved, discordant, 0.5).pvalue if discordant else 1.0
        pairs.append({'comparison': f'{b} minus {a}', 'improved_F_to_T': improved,
                      'declined_T_to_F': declined, 'discordant': discordant,
                      'difference_pp': 100*(improved-declined)/n, 'p_exact': p})
    pairs = pd.DataFrame(pairs)
    rejected, adjusted, _, _ = multipletests(pairs['p_exact'], alpha=ALPHA, method='holm')
    pairs['p_holm'] = adjusted
    pairs['significant_holm'] = rejected
    return pd.DataFrame(accuracy), pairs, exact_cochran_q(frame)

scenarios = {'Original labels (primary)': original,
             'Correction overrides (sensitivity)': corrected}
results = {}
for name, frame in scenarios.items():
    accuracy, pairs, overall = analyze(frame)
    results[name] = (accuracy, pairs, overall)
    print('\n' + name)
    display(accuracy.round(4))
    print(f"Overall Cochran Q={overall['Q']:.3f}; exact conditional p={overall['p_exact']:.4f}; "
          f"asymptotic reference p={overall['p_asymptotic']:.4f}")
    display(pairs.round(4))
    if not pairs['significant_holm'].any():
        print('No pair is significant after Holm correction at alpha=0.05. '
              'This does not demonstrate equal performance.')

# %% [markdown]
# ## Visualizations
# Accuracy intervals are individual 95% Wilson intervals; their overlap is
# not a test of paired differences. The transition plot shows why a change in
# accuracy can involve both improvements and declines. The heatmap retains
# question pairing and identifies where versions disagree.

# %%
plt.rcParams.update({'figure.dpi': 120, 'font.size': 10, 'axes.spines.top': False,
                     'axes.spines.right': False})
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
for ax, (name, _) in zip(axes, scenarios.items()):
    accuracy = results[name][0]
    rates = accuracy['accuracy'].to_numpy()
    errors = np.vstack([rates-accuracy['ci_low'], accuracy['ci_high']-rates])*100
    ax.bar(range(3), rates*100, color=['#64748b', '#0f766e', '#b45309'])
    ax.errorbar(range(3), rates*100, yerr=errors, fmt='none', color='black', capsize=5)
    ax.set(xticks=range(3), xticklabels=LABELS, ylim=(0, 105), title=name,
           xlabel='Prompt version', ylabel='Correct answers (%)')
    for i, row in accuracy.iterrows():
        ax.text(i, 3, f"{int(row['correct'])}/{int(row['n'])}", ha='center', color='white')
fig.suptitle('Answer accuracy with individual 95% Wilson intervals')
fig.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
for ax, (name, _) in zip(axes, scenarios.items()):
    pairs = results[name][1]
    positions = np.arange(3)
    ax.bar(positions-0.18, pairs['improved_F_to_T'], width=.36, label='Improved: F to T', color='#0f766e')
    ax.bar(positions+0.18, pairs['declined_T_to_F'], width=.36, label='Declined: T to F', color='#b45309')
    ax.set(xticks=positions, xticklabels=pairs['comparison'], title=name,
           ylabel='Number of questions', xlabel='Version comparison')
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.legend()
fig.suptitle('Paired changes in correctness')
fig.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(9, 7), sharey=True)
for ax, (name, frame) in zip(axes, scenarios.items()):
    ax.imshow(frame.to_numpy(), cmap=ListedColormap(['#f1d6b8', '#0f766e']),
              vmin=0, vmax=1, aspect='auto')
    ax.set(xticks=range(3), xticklabels=VERSIONS, yticks=range(len(frame)),
           yticklabels=frame.index, xlabel='Prompt version', ylabel='Question number', title=name)
    for i in range(len(frame)):
        for j in range(3):
            value = frame.iloc[i, j]
            ax.text(j, i, 'T' if value else 'F', ha='center', va='center',
                    color='white' if value else 'black', fontsize=9)
fig.suptitle('Correctness by paired question (T=correct, F=incorrect)')
fig.tight_layout()
plt.show()

# %% [markdown]
# ## Interpretation and next steps
# Report the accuracy difference in percentage points, the number of discordant
# questions, and the Holm-adjusted p-value together. Significance tests do not
# measure effect size, and a nonsignificant result does not show equivalence.
# With only 20 questions, small numbers of discordant pairs give low power.
# Correctness labels alone cannot show whether an incorrect answer followed the
# hint: that requires the model's selected option number, which is absent here.
#
# For further testing, keep the model and sampling settings fixed, use a fresh
# conversation for each response, randomize condition order, validate the answer
# key, and collect repeated runs. Repeated runs on a question are clustered;
# they should not be treated as additional independent questions in these tests.
#
# Method references:
# - [Exact McNemar test](https://www.statsmodels.org/dev/generated/statsmodels.stats.contingency_tables.mcnemar.html)
# - [Binomial test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html)
# - [Cochran Q](https://www.statsmodels.org/dev/generated/statsmodels.stats.contingency_tables.cochrans_q.html)
# - [Holm correction](https://www.statsmodels.org/dev/generated/statsmodels.stats.multitest.multipletests.html)
