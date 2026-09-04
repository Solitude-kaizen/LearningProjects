# Solitude-Kaizen - Project Context

## Purpose

Solitude-Kaizen is the flagship AI project inside the LearningProjects repository.

It is being built as both:

1. A usable personal AI assistant.
2. A long-term software engineering learning project.

The goal is to understand the technologies behind the system rather than simply assembling tools without understanding them.

## Current Direction — 2026-09-04

Earlier exploratory ideas are brainstorming, not permanent requirements.
Prioritize useful conversation, dependable memory, affordable replaceable
providers, and source-linked AI research. New features need a concrete
benefit and a small, testable plan.

The former "Learning Brain" is now honestly labelled an optional
Learning Guide: template-based study support for the creator, not model
training or autonomous self-improvement. Normal startup does not prepare
lessons or request reflections. Chat and research never require homework.
Existing study records, memories, and proposal history are preserved.

## Core Principle

> One companion, many replaceable brains.

Solitude-Kaizen owns:

- Identity
- Memory
- Conversation context
- Behavior
- Provider routing

AI providers supply replaceable inference.

The system should not become permanently dependent on one AI provider.

## Current Status

Solitude-Kaizen V1.0.0 has been released.

V2 development has started with eight incremental foundations:

- SQLite database initialization, memory schema, and safe insertion.
- An opt-in daily Kaizen discovery loop that performs at most one
  read-only public research attempt per day, stores the proposal in
  SQLite, and never changes code automatically.
- A zero-cost public research collector for GitHub, Hacker News, arXiv,
  and a curated YouTube feed. It stores deduplicated public metadata in
  SQLite, tolerates partial source failures, and makes no paid AI call.
- The optional Learning Guide, an offline tool that ranks unstudied
  metadata, suggests one short lesson, stores the creator's reflection, and
  keeps every improvement proposal pending for human review.
- Proposal Control V1, which lets the creator approve, reject, or
  postpone completed-lesson proposals while keeping a timestamped,
  append-only application history. Approval does not execute code.
- Lifetime Continuity V1, which creates and verifies an allowlisted local
  bundle containing SK's identity, profile, memories, and a consistent
  SQLite snapshot. It excludes `.env` and arbitrary project files.
- Companion startup, which checks only the existing opt-in research and
  Kaizen steps. The old controlled-learning helper is retained for
  explicit callers but is no longer used by the main CLI.
- Safe Restore V1, which previews exact continuity changes, requires an
  exact confirmation phrase, protects the current state with a verified
  emergency backup, verifies restored data, and automatically rolls
  back after a failed restore attempt.

The daily Kaizen feature is disabled by default until Groq tool billing
has been reviewed.

Automatic public research collection is also disabled by default to
avoid surprise network access. Manual collection remains available in
the CLI.

The Learning Guide is on-demand in the normal CLI. The legacy
`SK_CONTINUOUS_LEARNING_ENABLED` flag no longer prepares lessons at
startup. No study record or legacy data field was deleted or migrated.

Current verified state:

- Command-line interface working
- Persistent local memory working
- Short-term conversation history working
- Memory ranking and keyword-based, topic-aware context selection working
- Groq cloud provider working
- OpenAI provider supported
- Ollama local provider working
- Automatic cloud-to-local fallback working
- Structured provider error handling working
- CLI provider errors handled without raw tracebacks
- Provider tracking working
- Configuration validation working
- Explicit provider timeouts configured
- Dependencies pinned
- Secret exposure checks completed
- Public README updated
- Architecture documentation completed
- Roadmap documentation completed
- Troubleshooting documentation completed
- Learning notes completed
- Guarded continuity restoration and rollback working
- Preview and explicit confirmation before forgetting a memory; cancellation
  and invalid selections do not delete or save
- 174 automated tests passing, including the current V2 foundations

## Development Environment

Current development environment:

- Windows
- VS Code
- Git
- GitHub
- Python 3.14.7
- Ollama

Local repository:

```text
C:\Dev\Projects\LearniningProjects

```

GitHub repository:

```text
https://github.com/Solitude-Kaizen/LearningProjects
```

Primary package:

```text
src/solitude_kaizen/
```

## Current AI Providers

### Groq

Role:

- Default cloud provider

Current model:

```text
openai/gpt-oss-20b
```

Configured timeout:

```text
20 seconds
```

### Ollama

Role:

- Local provider
- Local fallback when an eligible cloud-provider failure occurs

Current model:

```text
qwen3:4b-instruct
```

Configured timeout:

```text
120 seconds
```

The instruct model is used instead of the Qwen3 thinking variant because it provides faster and more predictable fallback responses.

### OpenAI

Role:

- Optional cloud provider

Current model:

```text
gpt-5.6
```

Configured timeout:

```text
60 seconds
```

OpenAI is optional and should not be required for Solitude-Kaizen to function.

## Provider Reliability Architecture

Provider-specific functions raise structured:

```text
ProviderError
```

Current fields:

```text
provider
kind
message
retryable
fallback_allowed
```

Important rule:

> Never use a user-visible sentence as an internal error signal.

The router decides whether fallback is allowed.

Current cloud fallback paths:

```text
Groq
  -> eligible failure
  -> Ollama
```

```text
OpenAI
  -> eligible failure
  -> Ollama
```

Fallback is bounded and intentionally one-way.

Direct Ollama failures do not automatically route back to cloud providers.

## Provider Tracking

`last_provider_used` means:

> The provider that successfully produced the response for the most recent request attempt.

Every new request begins with:

```text
last_provider_used = None
```

A provider is recorded only after successful inference.

Failed requests must not retain stale provider state from previous turns.

## Configuration

Valid provider values:

```text
groq
ollama
openai
```

Default provider:

```text
groq
```

Invalid provider configuration raises:

```text
provider = config
kind = invalid_provider
```

Configuration is loaded from environment variables and `.env`.

## Security

Important security rules:

- `.env` must never be committed.
- `.env.example` contains placeholders only.
- API keys must never be stored in the memory system.
- Real secrets must never be included in tracked documentation.
- Dependencies are pinned to tested versions.
- Git history has been checked for API-key exposure.

Dependency files:

```text
requirements.txt
requirements-dev.txt
```

## Memory Architecture

Long-term memory is stored locally.

Current capabilities include:

- Creation
- Loading
- Saving
- Legacy normalization
- Categories
- Importance
- Timestamps
- Search
- Forgetting
- Category filtering
- Importance sorting
- Recency sorting
- Ranking
- Topic-aware context selection using the current chat question
- Prompt context construction

Chat compares distinct keywords with memory text and categories. When
there are matches, it includes only those records, ordered by overlap
then importance and recency, with the existing five-memory limit. Missing
or unmatched queries retain the old ranking. Selection does not modify
saved records; it does not understand synonyms, negation, or meaning.

Current memory schema:

```json
{
  "text": "...",
  "category": "...",
  "importance": 3,
  "created_at": "..."
}
```

Never store passwords, API keys, or other secrets as memories.

## Conversation Architecture

Conversation history is currently short-term and exists only while the application is running.

Important behavior:

1. Previous conversation context is built before adding the current user message.
2. The current user message is recorded once.
3. The current message is separately sent to the AI provider.
4. The assistant response is recorded once.
5. Conversation history is trimmed to a bounded size.
6. A failed AI turn removes the unanswered user entry.

Current limits:

```text
Prompt conversation context: 6 recent messages
Stored short-term history: 20 messages
```

## Important Modules

### `main.py`

Responsibilities:

- CLI menu
- User interaction
- Memory commands
- Creation of shared short-term conversation state
- Delegation of conversation, research, learning, and continuity
  commands to separate CLI boundaries
- Delegation of the forget-memory interaction to `memory_cli.py`

### `memory_cli.py`

Owns only the forget-memory interaction: list, select, preview, and
confirm or cancel. Only an explicit `yes` permits deletion and saving.
The low-level `forget_memory` and storage functions remain unchanged in
`memory.py`; other memory and profile menu actions remain in `main.py`.
Temporary-file tests cover both the interaction and main-menu wiring,
including cancellation with no extra save and confirmed persistence.

### `conversation_cli.py`

Responsibilities:

- Talk interaction and prompt-context assembly
- Completed-turn recording
- Failed-turn cleanup
- Provider-used and provider-configuration display
- Short-term conversation clearing and status

Provider selection and fallback remain in `ai_service.py`; message
construction and history trimming remain in `conversation.py`.

### `research_cli.py`

Responsibilities:

- Latest Daily Kaizen result display
- Explicit manual research-collection interaction
- Public research inbox display
- Collection status and partial-source diagnostics

Automatic scheduling, network-source behavior, validation,
deduplication, and storage remain outside this interface module.
Retrieved metadata is displayed as untrusted text.

### `learning_cli.py`

Responsibilities:

- Lesson display and reflection interaction
- Learning-progress display
- Pending proposal selection
- Approve, reject, and postpone interaction
- Proposal review-history display
- User-facing learning validation messages

The module has no ability to implement an approved proposal. It records
the creator's decision through `learning.py` only.

### `continuity_cli.py`

Responsibilities:

- Continuity backup, verification, and restore interaction
- Fixed continuity path grouping
- Restore preview display and confirmation input
- User-facing continuity diagnostics
- Returning a status to the main application after restore

### `continuity.py`

Responsibilities:

- Allowlisted continuity bundle creation and verification
- Logical SQLite comparison
- Read-only restore planning
- Staged replacement and post-restore verification
- Emergency backup and automatic rollback

### `ai_service.py`

Responsibilities:

- Provider configuration
- Groq adapter
- OpenAI adapter
- Ollama adapter
- Provider errors
- Provider routing
- Cloud-to-local fallback
- Provider tracking
- Timeout configuration

### `memory.py`

Responsibilities:

- Persistent memory storage
- Validation
- Normalization
- Search
- Filtering
- Ranking
- Context selection

### `conversation.py`

Responsibilities:

- Conversation message creation
- Conversation history management
- Context construction
- History trimming
- User-turn preparation
- Assistant-response recording

### `prompt.py`

Responsibilities:

- Constructing the Solitude-Kaizen system prompt
- Combining memory context and recent conversation context

## Testing

Run:

```powershell
python -m pytest -q
```

Current verified baseline:

```text
174 passed
```

Tests cover:

- Memory
- Conversation handling
- Prompt construction
- Provider configuration
- Provider errors
- Provider fallback
- Provider tracking
- Timeouts
- Ollama requests
- Groq behavior
- OpenAI behavior
- Failure handling
- Public research collection and deduplication
- Learning lesson selection, reflection, and proposal safety
- Proposal approval, rejection, postponement, and review history
- Continuity bundle allowlisting, tamper detection, previewed restore,
  confirmation, emergency backup, and rollback

The number of collected tests should be monitored because duplicate Python test-function names can silently replace earlier definitions.

## Development Workflow

Normal workflow:

```text
Inspect
  -> understand
  -> make one focused change
  -> test
  -> live-test when appropriate
  -> inspect Git diff
  -> commit
  -> push
  -> verify clean
```

Common Git commands:

```powershell
git status
git diff
git add <intended-files>
git diff --cached
git commit -m "Meaningful message"
git push
git status
```

Use:

```powershell
python -m pytest -q
```

for the test suite.

## Development Rules

1. Understand changes before adding them.
2. Prefer small changes over large rewrites.
3. Test after meaningful code changes.
4. Use live integration tests when mocks are insufficient.
5. Diagnose failures before changing configuration.
6. Prefer safe and reversible changes.
7. Do not disable security controls to bypass errors.
8. Avoid unnecessary dependencies.
9. Do not multiply retry systems.
10. Keep provider-specific behavior inside provider adapters.
11. Keep identity and memory independent from providers.
12. Reliability is more important than provider variety.
13. Keep Git commits logically focused.
14. Verify the working tree is clean after checkpoints.

## Reliability Philosophy

> Reliability before variety.
>
> Classification before retry.
>
> Fallback before failure.
>
> Independence before convenience.
>
> Simplicity before infrastructure.

## V1 Scope

V1 should remain focused on a reliable personal AI assistant foundation.

Included in V1:

- Persistent local memory
- Short-term conversation context
- Provider-independent AI routing
- Groq as the primary free cloud provider
- Ollama as the local fallback
- OpenAI as an optional provider
- Structured provider failures
- Safe configuration handling
- CLI interaction
- Tests
- Documentation
- Release-readiness checks

Explicitly postponed beyond V1:

- Voice interaction
- GUI
- Discord integration
- Web search
- Autonomous agents
- Computer control
- Large provider catalogs
- Complex tool ecosystems
- Heavy infrastructure
- Docker-based orchestration

These ideas may be revisited after the V1 foundation is stable.

## Dependency Policy

A new dependency should be added only when it:

- Reduces meaningful implementation complexity
- Improves reliability
- Provides a capability that is genuinely needed

A dependency should not be added merely because it is popular or convenient.

Prefer the standard library or existing dependencies when they are sufficient.

## Current V1 Priorities

The remaining V1 work should focus on release readiness rather than feature expansion.

Current priorities:

1. Finish documentation consistency checks.
2. Verify live memory persistence.
3. Verify conversation continuity, status, and clearing.
4. Verify normal Groq operation.
5. Verify direct Ollama operation.
6. Verify eligible cloud failure falls back to Ollama.
7. Verify invalid provider configuration remains safely handled.
8. Run the complete automated test suite.
9. Run dependency integrity checks.
10. Perform a final repository and secret audit.
11. Confirm the Git working tree is clean.
12. Create the V1 release checkpoint when the repository is ready.

OpenAI does not require a paid live test for V1 because it is optional and already covered through mocked tests.

## Documentation Structure

Current project documentation includes:

```text
README.md
PROJECT_CONTEXT.md
ARCHITECTURE.md
ROADMAP.md
LEARNING_NOTES.md
TROUBLESHOOTING.md
CLAUDE.md
```

Each document has a different responsibility:

- `README.md` explains the project to repository visitors.
- `PROJECT_CONTEXT.md` gives another AI or developer the current working context.
- `ARCHITECTURE.md` explains how the system is structured.
- `ROADMAP.md` tracks scope and future direction.
- `LEARNING_NOTES.md` records engineering lessons learned during development.
- `TROUBLESHOOTING.md` records known problems, diagnostics, and fixes.
- `CLAUDE.md` provides project-specific guidance for compatible AI coding assistants.

## Learning Approach

Solitude-Kaizen is also a learning system for understanding software engineering through direct practice.

The preferred development rhythm is:

```text
Inspect
  -> understand
  -> change one thing
  -> test
  -> explain what happened
  -> checkpoint
```

The goal is not to copy code blindly.

Each meaningful change should improve understanding of concepts such as:

- Functions
- Modules
- State
- Persistence
- APIs
- Exceptions
- Testing
- Git
- Configuration
- Security
- Reliability
- Architecture

## Long-Term Direction

Solitude-Kaizen is intended to evolve gradually beyond V1.

Possible future capabilities include:

- Richer long-term memory
- Better context relevance
- More local inference options
- Voice
- Graphical interfaces
- Tools
- Web capabilities
- Personal productivity features
- Health and routine support
- Controlled automation
- More advanced assistant behavior

These capabilities should be added only when the existing foundation is reliable enough to support them.

The system should remain understandable, maintainable, and provider-independent as it grows.

## Project Philosophy

Solitude-Kaizen is not intended to become a collection of every available AI technology.

It should become one coherent companion whose internal identity, memory, behavior, and architecture remain under the project's control.

Models and providers may change.

The companion should remain.
