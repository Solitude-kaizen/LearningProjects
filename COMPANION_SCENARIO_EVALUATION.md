# Fictional Companion Scenarios — 2026-09-09

## Scope

Starting checkpoint: `273a85e`. We tested HR interview practice, a snack
business plan, and AI learning through `run_talk_to_companion`. Each scenario
started with empty history, one relevant importance-2 memory, and an unrelated
importance-5 memory about evening walks. Each had an initial task and a
follow-up checking whether SK admits missing evidence.

The reproducible manual harness is `tests/manual_companion_scenarios.py`.
It contains the exact synthetic memories and questions. Run explicitly from
the project root with `python -m tests.manual_companion_scenarios`, optionally
adding `--case "AI learning"`. It is not automatically run by pytest.

Only the existing local `qwen3:4b-instruct` model was used. The harness calls
the fixed loopback Ollama endpoint directly, disables environment proxies,
and does not use the provider router or cloud fallback. It uses temperature
0 and a 256-token response limit for evaluation only. Production model
settings and `.env` were not changed. No personal profile, memory, or backup
files were read or modified. This is not laptop-wide network isolation.

## Baseline: six turns

| Scenario | Memory selection | Task following | Missing-information response |
| --- | --- | --- | --- |
| HR | Relevant memory only, both turns | Labeled a fictional school teamwork example; stayed within the requested length | Said hiring outcome was unknown |
| Business | Relevant memory only, both turns | Correctly calculated 600 / 20 = 30 pesos; two steps, though the first repeated the calculation | Asked for selling price and material costs; did not promise profit |
| AI learning | Relevant memory only, both turns | Distinguished retrieval and weight changes, but described training vaguely as repeated list use | Denied self-training; did not claim an accuracy increase |

Baseline times, first/follow-up: HR 14.11/1.30 seconds; business 3.98/2.92;
AI learning 4.28/1.51. All responses stopped normally rather than reaching
the output-token limit. Timings are single-run observations, not benchmarks.

Baseline AI wording that motivated the fix:

> Training would involve learning from repeated use of such lists to improve predictions.

That description can confuse ordinary repeated program use with training.
The business and AI replies also appended incorrect word-count labels such
as `(60 words)` and `(68 words)`. The HR example invented a first-place win,
but it was explicitly requested and labeled as fictional, not asserted as
the user's real history. Such examples should not be passed off as real
interview accomplishments.

## Change and rechecks

The small change is in `prompt.py`, not memory ranking or a provider:

- Distinguish supplied facts, examples, and unobserved outcomes.
- Explain that training requires parameter updates through optimization;
  storing notes and using lists do not perform training.
- Distinguish possible benefits of relevant context from measured accuracy.
- Follow length limits without appending guessed word counts.

The first revision repeated all six turns. Selection stayed correct, HR
still withheld a hiring conclusion, and business still calculated 30 pesos.
The unnecessary word-count labels disappeared. The AI explanation improved,
but its follow-up overcorrected to claiming retrieval does not improve
accuracy. The business follow-up listed expenses but omitted selling price;
its refusal to calculate profit was correct, but its explanation incomplete.

First-revision times: HR 7.46/1.13 seconds; business 3.21/1.84; AI 4.37/1.63.

A second revision added that relevant context can help answer quality. The
two AI turns were repeated (10.32/2.36 seconds), but the follow-up still said:

> Saving and retrieving notes does not update model weights or improve accuracy.

That overbroad accuracy claim was not accepted as fixed. A final revision
explicitly separated the training question from the unmeasured accuracy
question. The two AI turns were repeated again (7.11/1.29 seconds).

Final explanation:

> Keyword memory matching retrieves stored data (like notes) based on keywords—no model training occurs. Training updates a model’s weights using data, requiring optimization and evaluation. Example: A Python list `['a', 'b', 'c']` is stored; querying "list" returns it. This is retrieval, not learning. Accuracy changes require measurement, not assumption.

Final follow-up:

> No model training occurred. Any accuracy improvement is unmeasured and unobserved.

The final tested AI case satisfies the intended distinction. HR/business
were tested under the first revision, not repeated under the final two
AI-specific wording changes. In total, 16 local inference calls were made;
all ended with `done_reason=stop`. Memories stayed unchanged in the harness.

## What this establishes—and does not

The observed priority issue was a misleading explanation of training versus
retrieval. The final local replay improves that exact case. Unit tests check
the presence of the guidance; they do not prove model compliance. The full
automated regression suite passes 624 tests using synthetic data/fake inference.

Remaining limitations: the business explanation omitted an essential input
on the recheck; planning steps were shallow; lexical selection was tested
with overlapping words rather than difficult paraphrases. The AI example is
an illustration, not executable training code. No real hiring, financial,
or educational outcome was measured. No external facts were browsed or
verified, and no professional-domain capability is established by this trial.

Future evaluation should use unseen paraphrases and business questions with
explicitly separated revenue, variable costs, and fixed costs. Do not treat
these prompt changes as a guarantee against hallucination or as self-training.
