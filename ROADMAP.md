# Solitude-Kaizen Roadmap

## Purpose

This document defines what belongs in Solitude-Kaizen V1 and what should wait for later versions.

The roadmap exists to prevent uncontrolled scope expansion while preserving useful future ideas.

The guiding rule is:

> Finish the reliable core before expanding the system.

## V1 Goal

Solitude-Kaizen V1 should be a usable, understandable, tested personal AI assistant with:

| Area | V1 requirement |
| --- | --- |
| Interface | Working command-line interface |
| Identity | Solitude-Kaizen identity remains provider-independent |
| Memory | Persistent local memory |
| Conversation | Short-term conversational continuity |
| Context | Memory and recent conversation included in prompts |
| AI providers | Multiple replaceable providers |
| Cloud provider | Groq available as the default provider |
| Local provider | Ollama available locally |
| Optional provider | OpenAI supported without being required |
| Fallback | Eligible cloud failures can fall back to Ollama |
| Reliability | Structured provider errors and bounded fallback |
| Security | Secrets excluded from Git and memory |
| Testing | Automated test suite remains passing |
| Documentation | Setup, architecture, context, roadmap, and troubleshooting documented |
| Git | Clean version history and release checkpoint |

## V1 Target

Current target:

```text
September 16, 2026
```

The target is useful for maintaining focus, but reliability and understanding take priority over rushing unstable features into the release.

## V1 Completed Foundation

| Capability | Status |
| --- | --- |
| Repository and project structure | Complete |
| Python application structure | Complete |
| CLI menu | Complete |
| Profile loading and saving | Complete |
| Persistent memories | Complete |
| Memory normalization | Complete |
| Memory categories and importance | Complete |
| Memory search and filtering | Complete |
| Memory ranking | Complete |
| Memory context generation | Complete |
| Short-term conversation history | Complete |
| Conversation context | Complete |
| Conversation trimming | Complete |
| Duplicate-turn prevention | Complete |
| Failed-turn cleanup | Complete |
| System prompt builder | Complete |
| Groq integration | Complete |
| Ollama integration | Complete |
| OpenAI integration | Complete |
| Groq-to-Ollama fallback | Complete |
| OpenAI-to-Ollama fallback | Complete |
| Structured `ProviderError` | Complete |
| Invalid-provider validation | Complete |
| Provider tracking | Complete |
| Explicit provider timeouts | Complete |
| Ollama instruct fallback model | Complete |
| CLI provider-error boundary | Complete |
| `.env.example` configuration | Complete |
| Dependency pinning | Complete |
| Secret-safety review | Complete |
| Public README | Complete |
| Project context documentation | Complete |
| Architecture documentation | Complete |
| Automated tests | 63 passing |

## V1 Release Readiness

| Check | Status |
| --- | --- |
| Documentation consistency audit | Complete |
| Final memory-system live tests | Complete |
| Final conversation live tests | Complete |
| Final Groq live test | Complete |
| Final Ollama live test | Complete |
| Groq-to-Ollama fallback regression test | Complete |
| Invalid-provider configuration regression test | Complete |
| Repository structure review | Complete |
| Final automated test suite | Complete - 63 passing |
| Dependency integrity check | Complete |
| Final secret and configuration audit | Complete |
| Clean Git working tree verification | Complete |
| V1.0 release checkpoint | Complete |

## V1 Release Criteria

V1 is ready when all of the following are true:

```text
Core CLI works
Memory persists correctly
Conversation continuity works
Provider routing works
Local fallback works
Final provider errors are controlled
No known secret exposure exists
Setup instructions work
Documentation reflects the implementation
Automated tests pass
Important live tests pass
Git working tree is clean
No release-blocking bug is known
```

A feature is not required for V1 merely because it would be interesting or useful eventually.

## V1 Scope Freeze

The following are intentionally outside the current V1 scope:

```text
GUI
Web application
Voice input
Voice output
Discord integration
Autonomous agents
Computer control
Web search
Browser automation
Persistent conversation history
Vector databases
Semantic embeddings
Complex RAG systems
Massive provider integrations
AI gateway frameworks
Automatic model benchmarking
Circuit-breaker infrastructure
Multi-agent orchestration
Mobile application
Cloud deployment platform
```

These features should not be added before V1 unless one becomes necessary to fix a genuine reliability or security problem.

## V2 Direction

V2 began after the V1.0.0 release checkpoint.

Current V2 foundations:

```text
SQLite database initialization and memory insertion
Opt-in Daily Kaizen proposal storage
Zero-cost public research collector
Research deduplication and daily run history
Manual research inbox controls in the CLI
Offline Learning Brain with one active lesson
Local reflections and pending improvement proposals
Approve, reject, and postpone proposal controls
Append-only proposal review history
Provider-independent identity document
Verified local continuity bundles
Controlled startup learning cycle with one automatic lesson per day
Previewed continuity restoration with emergency rollback
```

Likely areas for investigation:

```text
Persistent conversation history
Improved memory relevance
Semantic memory retrieval
Local knowledge retrieval
File and note access
Tool execution
Provider health monitoring
More flexible provider routing
Improved companion behavior
Better configuration management
Test organization
CLI/application separation
```

CLI/application separation has begun with the research, Learning Brain,
and continuity commands. Their interactive wording, collection status,
reflection, proposal review, and restore confirmation flows now live in
testable `research_cli.py`, `learning_cli.py`, and `continuity_cli.py`
boundaries. The core modules retain the data and safety rules. The
remaining menu is still intentionally migrated one coherent feature
group at a time.

The public research collector is evidence gathering only. It must not
execute instructions from retrieved content or modify SK automatically.
The Learning Brain converts metadata into a small review exercise, not
trusted knowledge. Its proposals remain pending until a separate human
review action is recorded. Approval marks an idea for separate planning
and never implements it automatically.

Controlled Continuous Learning connects the existing components without
expanding their permissions. Automatic offline lesson preparation is
opt-in, limited to one lesson per local day, and does not silently turn
on either network collector.

Lifetime Continuity V1 preserves identity, profile, memories, and the
SQLite database through a verified local bundle. Safe Restore V1 can
apply the latest bundle only after a read-only preview, exact typed
confirmation, and a verified emergency backup. It verifies the result,
rolls back automatically after a failure, and restarts the companion
after success. Encrypted off-device copies and guided restoration when
the current live state is already damaged require later safety design.

V2 should still preserve the principle:

> One companion, many replaceable brains.

## Future Ideas

Longer-term possibilities include:

```text
Voice interaction
Desktop interface
Web interface
Mobile interface
Automation
Calendar and productivity tools
Health and routine support
Career and learning tools
Local-first operation
Additional local models
Additional cloud providers
Offline knowledge
Computer interaction
Agentic workflows
Personal knowledge system
Long-term adaptive companion behavior
```

Future ideas are not commitments.

They should be evaluated when the core system is stable enough to justify additional complexity.

## Technology Evaluation Rule

A new framework, provider, model, library, or infrastructure component should not enter the project simply because it is popular or new.

Before adding it, evaluate:

| Question | Requirement |
| --- | --- |
| Does it solve a real problem? | Required |
| Does it reduce complexity or provide necessary capability? | Preferred |
| Does it improve reliability? | Strong benefit |
| Can its behavior be tested? | Required |
| Can it be removed or replaced later? | Preferred |
| Does it preserve provider independence? | Required |
| Is the hardware cost reasonable? | Required for local components |
| Is the dependency trustworthy enough? | Required |

## Reliability Priority

Development priority remains:

```text
Reliability
    ↓
Correctness
    ↓
Understandability
    ↓
Security
    ↓
Maintainability
    ↓
New capabilities
    ↓
Provider variety
```

New features should not destabilize already-working core behavior.

## Development Rhythm

Normal development should continue using:

```text
Inspect
  ↓
Understand
  ↓
Make one focused change
  ↓
Run tests
  ↓
Live-test when necessary
  ↓
Inspect Git diff
  ↓
Commit
  ↓
Push
  ↓
Verify clean
```

## After V1

V1 is not the end of Solitude-Kaizen.

It establishes the first stable foundation.

After release, development can slow down and focus more deeply on learning the technologies already being used, improving architecture intentionally, and adding capabilities only when their value justifies their complexity.
