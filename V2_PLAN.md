# Solitude-Kaizen V2 Plan

## Vision

Solitude-Kaizen is a local-first personal AI runtime designed to evolve
alongside AI technology.

SK owns its identity, memory, knowledge, permissions, and learning process
while using replaceable models, agents, skills, tools, and interfaces.

## Core Principles

1. Local-first, cloud-capable.
2. One companion, many replaceable brains.
3. Stable identity, evolving capabilities.
4. Human authority over sensitive actions.
5. Continuous improvement through measurement and evaluation.
6. Learn new AI technologies without blindly adopting them.
7. Protect laptop resources and user data.
8. Prefer standards and replaceable interfaces over vendor lock-in.
9. Reliability before complexity.
10. Understand before implementing.

## V2 Candidate Systems

- Core orchestration
- SQLite memory
- Model router
- Skills / SKILL.md
- Agent foundation
- Permission system
- Tool layer
- MCP compatibility
- Web API
- Web/PWA interface
- Resource manager
- Evaluation system
- Kaizen improvement engine

## Current Rule

Do not implement all V2 systems at once.

Each capability must be designed, understood, tested, and integrated
incrementally.

## Daily Kaizen Foundation

The first Kaizen capability is intentionally bounded.

When explicitly enabled, Solitude-Kaizen can perform one read-only
public web discovery per calendar day when the application starts.
The discovery:

- Uses a fixed public description of the project.
- Does not send private memories, files, credentials, or system data.
- Produces an evidence-based improvement proposal with sources.
- Stores the result in SQLite for human review.
- Records controlled provider failures without breaking the CLI.
- Does not edit code, install software, or perform external actions.

Configuration:

```text
KAIZEN_DISCOVERY_ENABLED=false
```

The default remains disabled because Groq web-search tools may be
billable. Account limits and billing must be checked before enabling
the daily discovery.

Future Kaizen work should add evaluation and approval workflows before
any generated proposal can become an implementation change.

## Zero-Cost Research Collector

The next V2 foundation is a public research inbox that does not require
a paid AI or search service.

The collector:

- Reads public metadata from GitHub, Hacker News, arXiv, and one
  curated YouTube channel feed.
- Uses existing HTTP and standard-library XML support.
- Stores titles, links, short summaries, source identifiers, and dates
  in SQLite.
- Deduplicates items by source and public identifier.
- Isolates individual source failures so one unavailable platform does
  not discard successful results from the others.
- Runs at most once per local calendar day.
- Treats all retrieved content as untrusted data, never as instructions.
- Does not execute code, install packages, modify project files, or call
  a paid AI model.

Automatic startup collection is opt-in:

```text
SK_RESEARCH_ENABLED=false
```

Manual collection and inbox viewing are available in the CLI. The
collector is evidence gathering only.

## Learning Brain V1

The first local reflection layer works without an AI provider after
research has been collected.

It:

- Ranks unstudied items using small, understandable relevance rules.
- Prefers topics related to memory, retrieval, local AI, safety,
  evaluation, and assistant behavior.
- Creates only one active lesson at a time.
- Labels public metadata as unreviewed until the creator completes a
  reflection.
- Gives the creator one source-specific step designed for about ten
  minutes of study.
- Stores the creator's reflection locally in SQLite.
- Creates a bounded improvement proposal that remains pending for
  human review.

The learning loop does not call a model, access the network, execute
retrieved instructions, approve proposals, or change code. Completing a
lesson means the source was reviewed; it does not prove that every claim
in the source is true.
