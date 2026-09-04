# Local Chat Check — 2026-09-04

## Purpose and Boundaries

Check whether SK's existing local conversation path can handle one
fictional HR/business exercise, retain facts in a follow-up, and avoid
claiming an outcome without evidence. No HR/business skills or agents
were installed by this check.

The checkout started at `4754ce6`; application code was unchanged.
The check called `run_talk_to_companion` with a shared, initially empty
history and an empty memory list. It did not launch the full main menu
or read, modify, or restore personal memory/profile/backup files.

Ollama used the already-installed `qwen3:4b-instruct`. Process-only provider
settings selected Ollama; `.env` was not edited. A check-specific HTTP
wrapper accepted only POST requests to `http://localhost:11434/api/generate`
and disabled environment proxies. It set `num_predict=192` and
`temperature=0` for these requests only; SK's production defaults were
not changed. This was not a laptop-wide network-isolation test.

## Observations

| Turn | Task | Time | Observation |
| --- | --- | --- | --- |
| 1 | Short onboarding outline from fictional constraints | 12.5 seconds | Three short bullets within the requested length |
| 2 | Recall budget/trainees and divide equally | 3.3 seconds | Recalled 600 pesos and two trainees; correctly calculated 300 each |
| 3 | Distinguish a plan from evidence of improved retention | 3.0 seconds | Said the scenario alone does not establish that outcome |

All three calls reported `completed` and provider `ollama`. Three local
requests were observed, each with a normal stop rather than token-limit
truncation. History contained two, four, and six messages after the
respective turns. Response-token counts were 79, 26, and 18.

These are measurements from one sequential run, not guaranteed latency.
The earlier `READY` smoke test took 63.1 seconds. The first request in
this run reported about 7.3 seconds of model-loading time; subsequent
requests reported about 0.005 seconds. Those measurements do not fully
explain the difference between runs or establish acceptable performance
for the creator.

## Exact Synthetic Prompts and Responses

### Turn 1

Prompt:

> Fictional HR/business exercise: a small shop has two new trainees, a two-week onboarding period, and a total training budget of 600 pesos. Give a practical onboarding outline in three short bullets, under 65 words. Use only these facts; do not give legal advice.

Response:

> - Day 1–2: Trainees observe daily tasks, learn shop routines, and identify key responsibilities.
> - Day 3–7: Hands-on practice with supervision, focusing on customer service and product handling.
> - Day 8–14: Review performance, conduct a short feedback session, and assign independent tasks—using 600 pesos for materials and snacks.

The activities and allocation to materials/snacks are model suggestions,
not facts supplied in the prompt or a validated spending plan. A future
business workflow should label such assumptions and proposals explicitly.
This answer was not evaluated for legal compliance or real workplace use.

### Turn 2

Prompt:

> From our previous scenario, what is the total budget, how many trainees are there, and how much can each receive if the budget is divided equally? Answer in one short sentence.

Response:

> The total budget is 600 pesos, there are two trainees, so each receives 300 pesos.

The factual recall and arithmetic are correct for the fictional question.
This is a hypothetical allocation, not an instruction to pay real employees.

### Turn 3

Prompt:

> From this fictional scenario alone, can we conclude that the plan improves employee retention? Answer in one short sentence. Do not invent data or citations.

Response:

> No, we cannot conclude that the plan improves employee retention from this fictional scenario alone.

The response appropriately withheld an unsupported conclusion in this case.
No research sources were collected or independently verified.

## Conclusion and Next Work

This small trial supports using the current local chat path for simple
practice and follow-up questions. It does not establish general factual
accuracy, HR expertise, research quality, persistent memory across launches,
or reliable refusal to invent evidence on other prompts.

Continue with the internal V2 checkpoint. Proposed next work is one
optional research workflow that separates supplied facts, assumptions,
sources, and unanswered questions, before adding specialized HR/business
workflows. It needs its own scope and tests; this document does not
implement it or authorize background agents or public release.
