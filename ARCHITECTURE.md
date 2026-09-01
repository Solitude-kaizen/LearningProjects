# Solitude-Kaizen Architecture

## Purpose

This document describes how Solitude-Kaizen V1 is currently structured.

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

The main application code lives in:

```text
src/solitude_kaizen/
```

Important modules:

```text
src/solitude_kaizen/
├── main.py
├── memory.py
├── conversation.py
├── prompt.py
├── ai_service.py
└── data/
    ├── profile.json
    └── memories.json
```

Tests currently live in:

```text
tests/test_memory.py
```

Despite the filename, the current test file covers multiple modules.

Splitting tests into module-specific files may be considered later, but it is not required for V1.

## `main.py`

`main.py` is currently the application entry point and orchestration layer.

Responsibilities include:

- Loading profile data
- Loading and normalizing memories
- Creating short-term conversation state
- Displaying the CLI menu
- Handling user commands
- Calling memory functions
- Building conversation turns
- Building prompts
- Requesting AI responses
- Handling provider errors at the CLI boundary
- Displaying provider diagnostics

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

`build_memory_context()` selects a bounded number of ranked memories.

Current Talk flow uses:

```text
limit = 5
```

Important limitation:

The current memory selector ranks memories globally by importance and recency.

It does not yet perform semantic relevance search against the current user message.

That may be considered in a future version.

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

`prepare_user_turn()` builds conversation context **before** adding the current message to history.

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

## V2 Learning Brain Boundary

`learning.py` turns stored research into one bounded learning session.

Its flow is:

```text
Unstudied research metadata
  -> transparent relevance score
  -> one active baby-step lesson
  -> creator reflection
  -> reviewed lesson with a pending proposal
```

The module works offline and does not require an AI provider. It treats
titles and summaries as unreviewed public metadata, uses source-specific
review steps, and prevents a backlog of unfinished lessons. A completed
lesson records that the creator reviewed the source; it does not certify
the source's claims.

Improvement proposals are stored with `pending` status. The Learning
Brain cannot approve a proposal, edit source code, install software, or
execute instructions retrieved from the internet.

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
