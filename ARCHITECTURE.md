# Solitude-Kaizen Architecture

## Purpose

This document describes how Solitude-Kaizen is currently structured.

It focuses on:

- Module responsibilities
- Request flow
- Memory flow
- Conversation flow
- Prompt construction
- Provider routing
- Fallback behavior
- Error boundaries
- Configuration
- Architectural invariants

For project goals and development history, see `PROJECT_CONTEXT.md`.

For installation and usage instructions, see `README.md`.

## Core Architectural Principle

> One companion, many replaceable brains.

Solitude-Kaizen owns:

- Identity
- Memory
- Conversation context
- Behavior
- Provider selection
- Provider fallback rules

AI providers are replaceable inference engines.

The rest of the application should not depend on one specific AI vendor.

## High-Level Architecture

```text
                         +----------------------+
                         |        User          |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |       main.py        |
                         |        CLI           |
                         +----------+-----------+
                                    |
                   +----------------+----------------+
                   |                                 |
                   v                                 v
        +----------------------+          +----------------------+
        |      memory.py       |          |   conversation.py    |
        |                      |          |                      |
        | Persistent memory    |          | Short-term history   |
        | Ranking              |          | Recent context       |
        | Search/filter        |          | History trimming     |
        +----------+-----------+          +----------+-----------+
                   |                                 |
                   +----------------+----------------+
                                    |
                                    v
                         +----------------------+
                         |      prompt.py       |
                         |                      |
                         | System prompt        |
                         | Memory context       |
                         | Conversation context |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |    ai_service.py     |
                         |                      |
                         | Provider routing     |
                         | Provider adapters    |
                         | Error classification |
                         | Fallback             |
                         +----------+-----------+
                                    |
                 +------------------+------------------+
                 |                  |                  |
                 v                  v                  v
              +------+          +--------+          +--------+
              | Groq |          | Ollama |          | OpenAI |
              |Cloud |          | Local  |          | Cloud  |
              +------+          +--------+          +--------+
```

## Package Structure

`json_storage.py` is the shared complete-write/flush/replace boundary for
profile, memory, and session-note JSON. `memory_cli.py` stages additions or
deletions in a copied list and updates shared state only after saving succeeds.
The writer does not supply process locking or general recovery guarantees;
continuity bundles remain a separate safeguard.

`source_review_cli.py` provides a separate one-shot, explicitly confirmed
review request in option 30. `source_review.py` validates supplied fields,
builds source-isolated prompts, checks structured responses and literal
quote membership, and formats interpretation separately from evidence.
It never uses memory/session/conversation state, fetches source URLs, or
persists results. It delegates inference to the existing provider interface;
prompt guidance is not proof of truth or a security sandbox.

The core flow also accepts an optional user-approved session note.
`session_note_cli.py` owns preview/edit/confirm/resume interaction;
`session_notes.py` owns bounded fields, schema validation, and atomic local
persistence. The single note is a top-level `session_note` in `memories.json`,
outside keyword ranking. Existing backups include it without a format change.
No full conversation transcript is persisted.

`main.py` starts with no active note and only an availability hint. Explicit
resume creates an independent active snapshot. `conversation_cli.py` passes
it to `prompt.py` as fallible past context, not instructions or verified facts.
Those labels are guidance, not a security sandbox. Saving edits detaches the
active note until fresh approval; cancellation preserves state. Clear-chat
also detaches active notes even with empty chat history. Old replies may
retain note details until cleared, and backups retain their own copies.

The main application code lives in:

```text
src/solitude_kaizen/
```

Important modules:

```text
src/solitude_kaizen/
├── main.py
├── conversation_cli.py
├── conversation.py
├── session_note_cli.py
├── session_notes.py
├── research_cli.py
├── research_labels.py
├── research.py
├── learning_cli.py
├── learning.py
├── continuity_cli.py
├── continuity.py
├── memory_cli.py
├── memory.py
├── json_storage.py
├── source_review.py
├── source_review_cli.py
├── prompt.py
├── ai_service.py
├── database.py
├── continuous_learning.py
└── data/
    ├── profile.json
    ├── memories.json
    └── solitude_kaizen.db
```

Tests live in module-focused files under:

```text
tests/
```

Core-module tests and CLI-boundary tests remain separate so data and
safety rules can be verified independently from user-facing behavior.

## `main.py`

`main.py` is currently the application entry point and orchestration layer.

Responsibilities include:

- Loading profile data
- Loading and normalizing memories
- Creating short-term conversation state
- Displaying the CLI menu
- Handling user commands
- Calling memory functions
- Delegating conversation, research, learning, and continuity commands
  to focused CLI modules
- Delegating memory creation, forgetting, search, and category lookup to `memory_cli.py`

The conversation, research, learning, and continuity extractions form an
incremental CLI cleanup. Memory creation and forgetting have their own tested
interaction boundary; other memory views and profile commands remain in
`main.py`.

Search and category lookup now also delegate to `memory_cli.py`. Their
input boundary handles blank input, `/cancel`, EOF, and Ctrl+C before
performing a lookup. They return results without saving or model calls;
the low-level memory search/filter functions retain their existing behavior.

## `memory_cli.py`

`run_remember_memory` collects bounded text, category, and importance,
previews them with a cloud-context warning, and requires `yes` before saving.
Blank text, `/cancel`, Ctrl+C, and EOF cancel; failed saves do not add a live
memory. Both creation and forgetting preserve shared list identity and
commit in-memory changes only after the atomic write succeeds.

`run_forget_memory` lists memories, validates a selection, previews it,
and asks for an explicit `yes` before calling the existing deletion and
save functions. Any other answer cancels. Invalid selections and empty
lists also return without deleting or saving. Capitalization and
surrounding whitespace are ignored in the confirmation answer.

The confirmation belongs to the user interaction, not the low-level
`forget_memory` operation in `memory.py`, which remains unchanged.
Tests supply input/output functions and use temporary files to verify
preview order, unchanged cancellation data, and confirmed persistence.
Main-menu tests account separately for the existing startup normalization
save, so it cannot hide an unwanted write from the cancellation path.

## `conversation_cli.py`

Option 32 reuses the normal chat boundary with `review_before_send=True`.
Context is built without mutating history. Provider configuration and the
application system/user texts are displayed before an explicit `yes`.
Only then is the pending user turn appended and inference invoked with those
same texts. Canceling does not append, save, or contact inference. Option 12
does not request preview metadata or an extra confirmation. Provider wrappers
and fallback remain separate; the preview is not the complete wire payload.

Option 31 delegates to `memory_lens_cli.py`, a local-only explanation of the
same selector used by `build_memory_context`. Its shared-keyword evidence
and fallback label explain retrieval, not inference or truth.

`conversation_cli.py` owns the interactive talk and provider-status
workflow:

- Reading one user message
- Building memory and prior-conversation context
- Requesting a response through `ai_service.py`
- Recording one completed user-and-assistant turn
- Removing the unanswered user entry after a final provider error
- Displaying the provider that actually answered
- Previewing and confirming a clear, and reporting short-term conversation state

`run_talk_to_companion` rejects blank or whitespace-only input before
context construction, history mutation, or provider calls. EOF or a
keyboard interruption while reading the message follows the same
`cancelled` return path, with no response, error, or provider. Nonblank
messages are passed through unchanged, preserving code indentation.
The input guard runs before a request. A separate `KeyboardInterrupt`
boundary around the response call removes the pending user turn and reports
`interrupted`, with an explicit warning that transmission may have occurred.
The unavailable-provider sentinel also removes the pending turn and returns
`failed` rather than recording a diagnostic as an assistant answer. Neither
path retries or guarantees remote cancellation; prior history is preserved.
Main-menu tests verify cancellation returns to the menu and the next
valid chat retains its earlier context, with no extra file saves.

`run_clear_conversation` previews the message count and session-only scope
before accepting `yes` (case-insensitive, surrounding whitespace ignored).
Other answers, EOF, or a keyboard interruption at confirmation return
`cancelled` without changing history. An empty history returns `empty`
without prompting. Confirmation clears the shared list in place and
returns `cleared`; it never saves or deletes files. Main-menu tests verify
the next chat receives retained context after cancellation and no prior
context after a confirmed clear, using temporary data and fake responses.

Provider routing, fallback classification, and model configuration stay
in `ai_service.py`. Conversation storage and trimming stay in
`conversation.py`. Tests provide fake response and provider functions,
so this interface can be verified without cloud or local model calls.

## `research_cli.py`

`research_cli.py` owns the interaction for viewing Daily Kaizen results,
manually starting public research, and displaying the research inbox.
It delegates collection limits, source access, deduplication, and storage
to `research.py` and `database.py`.

This boundary does not enable automatic network access or interpret
retrieved text as instructions. Manual collection runs only when its CLI
command is selected. Public titles and summaries are displayed as
untrusted metadata for later human review.

## `research_labels.py`

`describe_research_source` derives a link domain and a source-type hint
from a small exact-host mapping. It does not classify content by titles
or feed labels, follow links, query DNS, or assign a trust score. For
example, a Hacker News item pointing at documentation is labeled from
the destination URL, not assumed to be a forum page.

Unknown hosts stay unknown. Unsupported schemes, embedded credentials,
unexpected ports, control/whitespace characters, and malformed URLs
receive no recognized source hint. This conservative parsing is only
for labeling; it is not a network authorization or SSRF defense.

The inbox displays these hints alongside an unverified-claims notice.
No schema or stored research item is changed, and a human review or a
recognized domain does not automatically turn a claim into verified
knowledge. Temporary-database tests verify that viewing adds no network
requests, memory promotion, or data writes.

## `learning_cli.py`

`learning_cli.py` owns the optional Learning Guide and its proposal-review
interaction. These commands are not prerequisites for chat or research:

- Displaying a lesson and its evidence status
- Asking for and storing the creator's reflection
- Displaying learning progress
- Selecting a pending proposal for review
- Reading the approve, reject, or postpone decision and its reason
- Displaying the append-only review history

The module delegates every state change to `learning.py`. An approval is
still a recorded decision for separate planning; this CLI boundary has
no code-editing, command-execution, provider, or network capability.
Tests supply predictable input and output functions without starting the
full application.

## `continuity_cli.py`

`continuity_cli.py` owns only the interactive continuity workflow:

- Grouping the five fixed continuity paths
- Printing backup and verification results
- Displaying the restore preview
- Reading the exact confirmation phrase
- Translating continuity errors into user-facing diagnostics
- Returning a restore status so `main.py` knows when to close

It does not implement archive validation, file replacement, or rollback.
Those safety rules remain in `continuity.py`. Input and output functions
can be supplied by tests, so this behavior is verified without starting
the full application loop.

The application is currently started with:

```powershell
python -m src.solitude_kaizen.main
```

### Startup Flow

At startup:

```text
Load profile.json
      |
      v
Load memories.json
      |
      v
Normalize each memory
      |
      v
Save normalized memory data
      |
      v
Create empty conversation history
      |
      v
Start CLI loop
```

Memory normalization allows older memory formats to be migrated into the current schema.

## `memory.py`

`memory.py` owns long-term memory operations.

Current responsibilities:

- Load profile data
- Save profile data
- Load memory data
- Save memory data
- Create memories
- Normalize legacy memories
- Validate memory categories
- Validate importance levels
- Search memories
- Forget memories
- Filter by category
- Sort by importance
- Sort by recency
- Rank memories
- Select memories for AI context
- Format memory context

### Memory Schema

Current normalized memory structure:

```json
{
  "text": "Example memory",
  "category": "project",
  "importance": 5,
  "created_at": "2026-08-27T18:00:00"
}
```

Valid categories are currently:

```text
learning
career
health
project
personal
test
```

Importance ranges from:

```text
1 to 5
```

### Memory Ranking

Memory ranking currently prioritizes:

```text
importance
    |
    v
known timestamp
    |
    v
recency
```

Higher-importance memories rank first.

When importance is equal, newer memories rank higher.

### Memory Context

`build_memory_context()` accepts an optional `query`; the Talk flow
passes the current user message, not the accumulated conversation.
`select_memories_for_context()` compares distinct keywords in that query
with each memory's text and category.

Current Talk flow uses:

```text
limit = 5
```

When matches exist, only matching memories are selected. More distinct
overlapping words rank first; ties preserve the existing importance,
known-timestamp, recency, and stable input ordering. If the query is
missing, has no usable keywords, or matches nothing, selection falls
back to the original global ranking. Existing callers that omit `query`
keep their previous behavior, and memory-list sorting is unchanged.

Keyword extraction ignores case, punctuation, a small English stop-word
list, single-character tokens, and purely numeric tokens. Repeating a
word does not increase its score. This is not semantic retrieval: it
does not interpret synonyms, word forms, negation, or topic ambiguity.
No records are changed or saved, and no external service or model
training is involved in selection.

## `conversation.py`

`conversation.py` owns short-term conversation state.

Conversation messages use this structure:

```python
{
    "role": "user",
    "content": "Hello"
}
```

or:

```python
{
    "role": "assistant",
    "content": "Hello."
}
```

Current responsibilities:

- Create conversation messages
- Add messages to history
- Build recent conversation context
- Trim history
- Prepare a user turn
- Record assistant responses

### Conversation Limits

Current prompt context limit:

```text
6 recent messages
```

Current stored short-term history limit:

```text
20 messages
```

Conversation history exists only in RAM.

It is cleared when the program exits.

## Conversation Turn Architecture

A successful Talk turn currently follows this sequence:

```text
User enters message
      |
      v
Build conversation context
from previous messages only
      |
      v
Add current user message
to short-term history
      |
      v
Build memory context
      |
      v
Build system prompt
      |
      v
Send:
- system prompt
- current user message
to provider router
      |
      v
Receive assistant response
      |
      v
Record assistant response
      |
      v
Trim conversation history
      |
      v
Display provider used
```

### Important Conversation Invariant

The current user message must appear only once in the model request flow.

The CLI uses `build_conversation_context()` before adding the current message.
It then builds memory/system context and, in reviewed mode, obtains `yes`.
Only after those steps does it append the user message and invoke inference.
The older `prepare_user_turn()` convenience helper remains available but is
not used by the current chat CLI.

The current message is then passed separately to the provider.

This prevents accidental duplication such as:

```text
Recent conversation:
User: What is a dictionary?

Current user message:
What is a dictionary?
```

when the first copy should not yet have been part of recent history.

## Failed Conversation Turns

When `generate_response()` raises a final `ProviderError`, the CLI removes the user message that was temporarily added to history.

Conceptually:

```text
Add user message
      |
      v
Provider request fails
      |
      v
ProviderError reaches CLI
      |
      v
Remove unanswered user turn
      |
      v
Display readable diagnostic
```

This prevents an unanswered turn from polluting short-term conversation history.

Previous successful conversation history remains intact.

## `prompt.py`

`prompt.py` owns system-prompt construction.

Its job is to combine:

```text
Solitude-Kaizen identity
        +
Memory context
        +
Recent conversation context
```

The current system prompt tells the model:

- It is Solitude-Kaizen
- Remembered information should be used when relevant
- Memories should not be forced into unrelated responses
- Recent conversation may be included when available

Provider-specific API details do not belong in `prompt.py`.

## `ai_service.py`

`ai_service.py` owns AI-provider infrastructure.

Responsibilities include:

- Loading environment configuration
- Validating provider selection
- Groq integration
- Ollama integration
- OpenAI integration
- Provider-specific error translation
- Fallback routing
- Provider tracking
- Timeout configuration

## Provider Configuration

Valid providers:

```text
groq
ollama
openai
```

Default:

```text
groq
```

Provider selection comes from:

```env
AI_PROVIDER
```

Environment variables are loaded with `python-dotenv`.

Invalid provider values produce a structured `ProviderError`.

## Provider Models

Current models:

```text
Groq:
openai/gpt-oss-20b

Ollama:
qwen3:4b-instruct

OpenAI:
gpt-5.6
```

## Provider Timeouts

Timeout configuration is centralized through constants:

```text
Groq   = 20 seconds
OpenAI = 60 seconds
Ollama = 120 seconds
```

Provider request implementations should reference these constants rather than duplicate literal timeout values.

This keeps configuration authoritative in one location.

## `ProviderError`

Provider failures are represented internally by:

```python
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

### `provider`

Identifies the source of the failure.

Examples:

```text
groq
openai
ollama
config
```

### `kind`

Classifies the failure.

Examples include:

```text
timeout
connection
rate_limit
server_error
authentication
permission_denied
bad_request
missing_api_key
invalid_provider
http_error
unknown
```

### `retryable`

Indicates whether the same provider failure may be temporary.

Examples:

```text
timeout        -> retryable
connection     -> retryable
server_error   -> retryable
bad_request    -> not retryable
```

### `fallback_allowed`

Controls whether another provider is permitted to answer the request.

This is separate from `retryable`.

A failure may be:

```text
retryable = False
fallback_allowed = True
```

For example, a missing cloud API key does not become valid by retrying the same provider, but another provider may still be able to answer.

## Critical Error-Handling Rule

> Never use a user-visible sentence as an internal error signal.

Routing decisions must use structured information such as:

```python
error.fallback_allowed
```

They must not use logic such as:

```python
if response == "Some error message":
```

Human-readable wording may change.

Structured state is the stable internal contract.

## Provider Routing

`generate_response()` is the provider router.

Every request begins by resetting:

```text
last_provider_used = None
```

It then validates the configured provider.

### Groq Path

```text
AI_PROVIDER=groq
      |
      v
Try Groq
      |
      +---- success --------------------+
      |                                 |
      |                                 v
      |                        mark provider = groq
      |                                 |
      |                                 v
      |                           return response
      |
      v
ProviderError
      |
      v
fallback_allowed?
   /       \
 no         yes
 |           |
 v           v
raise     Try Ollama
             |
        +----+----+
        |         |
     success    failure
        |         |
        v         v
 mark ollama   classify
        |         |
        v         +--> retryable
 return              return controlled
 response             unavailable message
                  |
                  +--> non-retryable
                       raise error
```

## OpenAI Path

OpenAI follows the same cloud-to-local fallback structure:

```text
OpenAI
   |
eligible ProviderError
   |
   v
Ollama
```

OpenAI is optional.

Solitude-Kaizen should not require OpenAI credentials in order to function with another configured provider.

## Ollama Path

When Ollama is directly selected:

```text
AI_PROVIDER=ollama
      |
      v
Try Ollama
      |
   success
      |
      v
mark provider = ollama
      |
      v
return response
```

Direct Ollama failures do not currently fall forward to another provider.

This prevents unexpected provider switching and circular fallback behavior.

## Fallback Direction

Current fallback direction is intentionally one-way:

```text
Groq --------+
             |
             +----> Ollama
             |
OpenAI ------+
```

There is currently no route such as:

```text
Ollama -> Groq -> OpenAI -> Ollama
```

This keeps fallback behavior bounded and understandable.

## Provider Tracking

`last_provider_used` represents:

> The provider that successfully generated the response for the most recent request attempt.

Important rules:

1. Reset it to `None` at the start of every request.
2. Do not mark a provider before the provider succeeds.
3. If Groq fails and Ollama succeeds, record `ollama`.
4. If a request fails before any provider succeeds, leave it as `None`.
5. Never allow provider information from a previous request to leak into a new failed request.

## CLI Error Boundary

Provider adapters classify technical failures.

The provider router decides fallback behavior.

The CLI decides how final failures are presented to the user.

This creates three separate responsibilities:

```text
Provider adapter
    |
    | classify
    v
Provider router
    |
    | fallback or propagate
    v
CLI boundary
    |
    | display safely
    v
User
```

This separation prevents provider SDK exceptions from leaking directly into normal CLI operation.

## Configuration Boundary

Secrets and provider configuration come from environment variables.

Examples:

```env
AI_PROVIDER=groq
GROQ_API_KEY=...
OPENAI_API_KEY=...
```

Real secrets belong only in local configuration.

They must not be stored in:

```text
source code
README files
PROJECT_CONTEXT.md
memory data
Git history
```

`.env.example` contains placeholders only.

## Persistence Boundaries

### Persistent

Currently persisted to disk:

```text
Profile
Long-term memories
SQLite memory foundation
Daily Kaizen proposals
Public research items
Public research collection history
Learning lessons and creator reflections
Pending improvement proposals
Proposal review history
Provider-independent identity document
Local continuity bundles
```

### Non-Persistent

Currently held only in memory:

```text
Conversation history
last_provider_used
```

These values reset when the application exits.

## V2 Public Research Boundary

`research.py` collects a small amount of public metadata from GitHub,
Hacker News, arXiv, and a curated YouTube feed.

Its responsibilities are:

- Read public metadata through bounded requests.
- Normalize and validate identifiers, titles, links, summaries, and
  dates.
- Isolate failures by source.
- Store only valid HTTP or HTTPS references.
- Leave deduplication and run history in SQLite.

Retrieved content is untrusted data. It is never interpreted as a tool
instruction, executed, installed, or allowed to change source code.
Automatic startup collection remains opt-in, and the collection loop
runs at most once per local calendar day.

## V2 Optional Learning Guide Boundary

`learning.py` turns saved research metadata into one optional study
activity using templates. It does not read the complete source or train
a model. "Learning Brain" was the earlier name, not a capability claim.

Its flow is:

```text
Unstudied research metadata
  -> transparent relevance score
  -> one optional short lesson
  -> creator reflection
  -> reviewed lesson with a pending proposal
```

The module works offline and does not require an AI provider. It treats
titles and summaries as unreviewed public metadata, uses source-specific
review steps, and prevents a backlog of unfinished lessons. A completed
lesson records that the creator reviewed the source; it does not certify
the source's claims.

Improvement proposals are stored with `pending` status. The guide does
not automatically approve a proposal, edit source code, install software, or
execute instructions retrieved from the internet.

The stored `baby_step` field and existing lesson/review APIs remain
compatible. The rename does not delete history or reinterpret old data.

## Companion Startup and Legacy Study Cycle

`run_companion_startup` in `continuous_learning.py` runs only the existing
permitted source checks:

```text
Optional daily public research
  -> optional Daily Kaizen discovery
  -> normal companion menu (no lesson preparation or reflection prompt)
```

`SK_RESEARCH_ENABLED` and `KAIZEN_DISCOVERY_ENABLED` remain independent
opt-ins, disabled by default. The guide is accessed manually from the
menu; an unfinished lesson cannot block startup, chat, or research.

For compatibility, explicit callers may still invoke
`run_controlled_learning_cycle`, whose optional study step respects the
legacy `SK_CONTINUOUS_LEARNING_ENABLED` flag and one-lesson-per-day
limit. The main CLI no longer calls that helper, even if the old flag is
enabled. Neither workflow runs while SK is closed, trains model weights,
approves proposals, changes source code, or executes retrieved text.

## V2 Proposal Control Boundary

Proposal Control separates learning from implementation:

```text
Completed lesson
  -> pending proposal
  -> creator chooses approve, reject, or postpone
  -> reason and timestamp are appended to review history
  -> no implementation action
```

Only proposals from completed lessons appear in the review queue.
Approving changes the proposal status to `approved`; rejecting changes
it to `rejected`; postponing records the review but leaves the proposal
`pending`. Approved and rejected proposals cannot be reviewed again in
V1.

`proposal_reviews` is append-only through the application workflow.
There are no application functions for editing or deleting review
records. Proposal review never calls an AI provider, the network, a
command runner, or a source-code editor.

## V2 Lifetime Continuity Boundary

`continuity.py` creates a portable backup through an exact allowlist:

```text
SK_IDENTITY.md
profile.json
memories.json
consistent SQLite snapshot
manifest with sizes and SHA-256 hashes
```

SQLite's online backup API creates a consistent snapshot even when the
application has an open database. Verification rejects missing, extra,
duplicated, altered, malformed, or unsupported bundle contents. It
parses the JSON files, validates the identity marker, and opens the
database snapshot in memory for `PRAGMA quick_check`.

The continuity module has no path that reads `.env`, credential files,
source directories, or arbitrary user-selected files. Bundles remain in
an ignored local directory and are not encrypted.

Safe Restore V1 follows a bounded transaction-like sequence:

```text
verify selected bundle
        |
        v
preview each exact live target and proposed action
        |
        v
require the displayed confirmation phrase
        |
        v
create and verify an emergency backup of current state
        |
        v
stage changed files beside their targets and replace them
        |
        v
verify restored identity, JSON, and logical SQLite contents
        |
        +-- failure --> restore and verify the emergency backup
        |
        v
close the CLI and reload cleanly on the next start
```

The restore allowlist maps the four archive paths to four fixed live
paths; bundle names cannot choose destinations. SQLite comparisons use
logical schema and record contents because two valid SQLite snapshots
can be byte-different while containing the same data. If either the
selected backup or current state changes after preview, execution is
stopped. Safe Restore V1 also refuses to proceed when any current live
continuity file is missing, malformed, or too large because it cannot
first guarantee a verified emergency rollback point. Guided disaster
recovery for an already damaged live state remains outside this first
restore boundary.

## Architectural Invariants

The following rules should remain true unless intentionally redesigned.

### Identity Independence

Solitude-Kaizen's identity must not belong to Groq, OpenAI, Ollama, or another provider.

### Memory Independence

Memory storage and ranking must remain outside provider SDKs.

### Conversation Independence

Conversation state must remain owned by Solitude-Kaizen rather than one vendor's conversation API.

### Structured Failures

Internal routing decisions must use structured errors.

### Bounded Fallback

Fallback must not create infinite provider loops.

### Successful Provider Tracking

A provider is recorded only after successful inference.

### No Duplicate Current Turn

The current user message must not be duplicated in recent conversation context.

### Failed Turn Cleanup

A final failed provider request must not leave an unanswered user turn in short-term conversation history.

### Centralized Configuration

Model names, timeout values, and valid provider choices should have clear authoritative definitions.

### Secret Isolation

Credentials must remain outside tracked source files and memory data.

## Current V1 Trade-Offs

The architecture intentionally favors simplicity over large abstractions.

For example:

- Provider routing is explicit Python rather than a gateway framework.
- Long-term memory uses local JSON rather than a database.
- Conversation history uses an in-memory list.
- The CLI is imperative rather than divided into many application layers.
- Tests currently share one test module.
- Local fallback uses direct Ollama HTTP calls.

These choices are acceptable for V1 because the system remains small enough to understand and test.

Abstractions should be introduced when they solve a real problem, not because larger projects use them.

## Possible Future Architecture

Future versions may introduce:

```text
Persistent conversation storage
Semantic memory retrieval
Tool execution
Local knowledge retrieval
File access
Additional provider adapters
Provider health tracking
Circuit breakers
More advanced routing
GUI or web interface
Voice interface
Automation
```

These should be added without moving core identity, memory, or behavior ownership into an external AI provider.

## Architectural Decision Principle

Before adding infrastructure, ask:

1. Does it reduce complexity?
2. Does it improve reliability?
3. Does it provide a genuinely required capability?
4. Can the behavior still be understood and tested?
5. Does it preserve Solitude-Kaizen's independence?

If the answer is no, the dependency or abstraction probably does not belong in the current architecture.
