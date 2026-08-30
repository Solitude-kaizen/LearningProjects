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
