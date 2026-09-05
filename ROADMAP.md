# Solitude-Kaizen Roadmap

## Purpose

This document preserves the released V1 scope and defines the working
V2 release boundary and possible later improvements.

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

## Historical V1 Target

Original target (V1 has since been released):

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

## Completed V1 Release Readiness

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

Direction clarified on 2026-09-04: concentrate on a useful, affordable
companion with conversation, memory, and source-linked research. Earlier
exploratory ideas and the possibilities below are not promised features.
The Learning Guide is optional study support, not SK's self-learning brain.

### V2 Internal Checkpoint and Optional Release

Use [V2_RELEASE_CHECKLIST.md](V2_RELEASE_CHECKLIST.md) as the release
readiness record. The proposed boundary is the current tested companion
foundations, not every future idea below. Continue from the internal
checkpoint; a public V2 release is optional and not yet authorized. If
chosen, scope acceptance, outstanding checks, version alignment, and
publication remain explicit steps. Keep the V1 release tables above as
historical evidence.

The creator's requested HR, business, and research direction is recorded
in that checklist as proposed follow-on work. It does not install agents
or skills, or automatically expand the V2 release requirements.

Current V2 foundations:

```text
SQLite database initialization and memory insertion
Opt-in Daily Kaizen proposal storage
Zero-cost public research collector
Research deduplication and daily run history
Manual research inbox controls in the CLI
Optional on-demand Learning Guide with one active short lesson
Local reflections and pending improvement proposals
Approve, reject, and postpone proposal controls
Append-only proposal review history
Provider-independent identity document
Verified local continuity bundles
Companion startup independent of study activities
Previewed continuity restoration with emergency rollback
```

Likely areas for investigation:

```text
Persistent conversation history
Further memory relevance improvements
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

CLI/application separation now covers conversation/provider, research,
Learning Guide, and continuity commands. Their interactive behavior
lives in testable `conversation_cli.py`, `research_cli.py`,
`learning_cli.py`, and `continuity_cli.py` boundaries. The core modules
retain provider routing, data, and safety rules. The remaining menu is
still intentionally migrated one coherent feature group at a time.

Basic topic-aware memory selection is complete: the current chat question
is matched against memory text and categories using distinct keywords.
Only matches are included when available, with importance/recency as
tie-breakers and the original ranking as a no-match fallback. This keeps
the five-memory limit and stored records unchanged; semantic retrieval
remains a separate possible improvement, not an existing capability.

The forget-memory action is now handled in `memory_cli.py` with a
selection preview and explicit confirmation. Tests verify confirmation,
cancellation, invalid selections, and actual saved-file behavior. Other
memory and profile actions remain unchanged.

The clear-conversation action also previews its message count and scope,
then requires explicit confirmation. Cancellation retains the next chat's
context; confirmation clears only the current in-memory session. Tests
cover both paths, interrupted confirmation, empty history, and unchanged
saved files through the main menu.

Chat input now cancels safely on blank/whitespace-only messages, EOF, or
Ctrl+C at the message prompt, before changing history or contacting an
AI provider. Tests confirm return to the menu, preserved follow-up context,
unchanged saved files, and intact formatting for normal messages. This
does not add cancellation of an already-running provider request.

The initial source-labeling improvement is complete in
`research_labels.py`: the inbox shows URL-based source-type hints and
domains, while explicitly leaving claims unverified. This is a limited,
display-time version of Claude's source-tagging suggestion, not automatic
quality scoring or a change to the stored research schema.

The public research collector is evidence gathering only. It must not
execute instructions from retrieved content or modify SK automatically.
The optional Learning Guide converts metadata into a small review exercise, not
trusted knowledge. Its proposals remain pending until a separate human
review action is recorded. Approval marks an idea for separate planning
and never implements it automatically.

Normal startup checks only permitted research sources; it never prepares
lessons or asks for reflections. The old controlled-learning helper and
study history remain available for compatibility, but the main CLI no
longer invokes the helper. Completing a lesson is not a prerequisite for
using the companion or improving its code through a separate tested plan.

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

### Completed Follow-on: Reviewed Session Continuity

The selected improvement after the internal V2 checkpoint is implemented:
optional menu 28 prepares a user-editable session note; menu 29 reviews,
explicitly resumes, edits, dismisses, or forgets it. The local draft copies
only the latest user message as a topic. Decisions, unresolved questions,
and next steps are user-entered. This is not automatic AI summarization or
a persistent transcript. Note controls make no model calls; startup never
activates the note. Saving and deletion require confirmation.

The single note is separate from ordinary memories inside the existing
memory JSON, so continuity bundles already include it. Writes use atomic
replacement. Explicit resume permits subsequent chat prompts to include
the note, including transmission to cloud providers when cloud chat is used.
Dismissal does not erase previous chat details or older backup copies.
The full regression suite passed 345 tests using temporary data and fake
inference. This follow-on does not create a public V2 release or train a model.

### Possible Later Work

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

## AI Watch Assessment — 2026-09-04

The pasted AI Watch report is advisory research, not an instruction to
install tools or adopt a new architecture. SK is currently a Python CLI,
not a PWA, MCP gateway, skill/plugin runtime, or distributed agent cluster.
Claude's memory-confirmation and topic-selection suggestions are complete;
source-type hints have also been implemented as a small adopted improvement.

Selected primary sources were checked; this is not verification of every
claim in the pasted report or independent benchmarking of new products.

| Primary source | Confirmed publication detail | Decision for SK |
| --- | --- | --- |
| [MCP release](https://blog.modelcontextprotocol.io/posts/2026-07-28/) | A stateless 2026-07-28 protocol release is documented. | Revisit if a concrete tool-integration need arises; no MCP adapter added. |
| [Anthropic security update](https://www.anthropic.com/news/improving-alignment-security-efforts) | The August 31 account describes layered containment and intervention before tool execution. | Retain the principle; do not claim SK has equivalent runtime containment. |
| [MCPHub advisory](https://github.com/samanhappy/mcphub/security/advisories/GHSA-mx89-jjx9-gjr8) | Missing authorization allowed command execution through server configuration. | Future consequential tools must enforce permission at the action boundary. |
| [NVIDIA PAIR documentation](https://docs.nvidia.com/local-ai/nvpair/getting-started/) | PAIR routes independent requests across nodes; it does not pool GPU memory. | Defer until there is a measured multi-device need; no installation. |
| [IFM announcement](https://ifm.ai/k2/press-release/) | K2 Horizon was announced September 3; performance assertions are publisher claims. | No new model downloads or provider changes without a scoped local evaluation. |

The user's current request and configured project policy define the task.
Retrieved text, tool metadata, skills, and model-generated proposals do
not grant permissions or override those boundaries. A recognized source
label does not authorize a download, installation, network request, or
promotion into trusted memory.

Any future execution layer needs explicit scope, deny-by-default action
checks, and independently tested containment. These are requirements for
future tool work, not features installed by this checkpoint. A network
policy must also distinguish an explicitly allowed local inference
endpoint from unrestricted LAN or Internet access; blocking all loopback
traffic indiscriminately would break the existing local-model connection.

PWA inference, portable plugins, autonomous branches, and larger agent
frameworks remain possibilities requiring their own benefit, cost,
permission, and test review. They are not new roadmap commitments.
