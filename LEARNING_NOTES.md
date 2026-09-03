# Solitude-Kaizen Learning Notes

## Purpose

This document records important software-engineering concepts learned while building Solitude-Kaizen.

It focuses on understanding rather than merely remembering commands.

The goal is to make it possible to return to the project later and understand not only what was built, but why particular engineering decisions were made.

## Core Learning Principle

> Build it, understand it, test it, then improve it.

AI assistance can accelerate development, but the project should gradually increase the developer's ability to understand, diagnose, and modify the system independently.

## Small Changes Are Easier to Understand

One of the most useful development habits is making one focused change at a time.

A good cycle is:

```text
Inspect
  |
  v
Understand
  |
  v
Change one thing
  |
  v
Test
  |
  v
Inspect result
  |
  v
Commit
```

When many unrelated changes are made simultaneously, a failure becomes harder to diagnose because several possible causes exist.

Small changes reduce uncertainty.

## Git Is More Than Backup

Git records project history.

A clean checkpoint means:

```text
The current state is understood
The intended change works
Tests pass when relevant
The change is committed
The remote copy is updated
The working tree is clean
```

Useful commands:

```powershell
git status
git diff
git add <file>
git diff --cached
git commit -m "Meaningful message"
git push
git status
```

## `git status` Shows State

`git status` answers questions such as:

```text
What changed?
What is staged?
What is untracked?
Is the local branch ahead of GitHub?
Is the working tree clean?
```

Do not assume a file has been saved correctly just because it appears in VS Code.

Git only sees files that actually exist inside the repository.

## `git diff` Shows Content Changes

Before committing:

```powershell
git diff
```

shows unstaged changes.

After staging:

```powershell
git diff --cached
```

shows what will enter the next commit.

This makes Git useful as an inspection tool, not merely a storage system.

## A Successful Commit Does Not Mean Every Check Passed

Commands such as:

```powershell
git diff --cached --check
```

report problems but do not automatically prevent a later `git commit`.

If a diagnostic command prints a warning, stop and resolve it before continuing.

The developer must still interpret command output.

## Files Have Real Locations

A file visible in an editor is not necessarily located in the expected project directory.

This became clear when `ARCHITECTURE.md` appeared open in VS Code but:

```powershell
Test-Path .\ARCHITECTURE.md
```

returned:

```text
False
```

The file had been saved outside the repository.

General lesson:

> Always verify filesystem state when the behavior of Git and the editor disagree.

Useful commands:

```powershell
Test-Path .\FILENAME
Get-ChildItem -Recurse -Filter FILENAME
```

## Python Functions Separate Responsibilities

Functions allow behavior to be named and reused.

Instead of placing every operation directly inside the CLI, Solitude-Kaizen uses functions such as:

```text
create_memory()
rank_memories()
build_memory_context()
prepare_user_turn()
build_system_prompt()
generate_response()
```

A function should ideally have a clear responsibility.

This makes behavior easier to understand and test.

## Modules Create Larger Boundaries

Functions are grouped into modules according to responsibility.

Current examples:

```text
memory.py
conversation.py
prompt.py
ai_service.py
main.py
```

This provides a larger separation than individual functions.

For example:

```text
memory.py
```

should not need to understand Groq API details.

Likewise:

```text
ai_service.py
```

should not own the structure of persistent memory.

## Separation of Concerns

A useful architecture gives different parts of the program different jobs.

For Solitude-Kaizen:

```text
main.py
    -> orchestration and CLI

memory.py
    -> persistent memory logic

conversation.py
    -> short-term conversation state

prompt.py
    -> prompt construction

ai_service.py
    -> provider infrastructure
```

This principle is called separation of concerns.

It reduces the number of things each part of the program must understand.

## State Means Information That Changes

Examples of state in Solitude-Kaizen include:

```text
memories
conversation_history
current_goal
last_provider_used
```

State can exist in different places and for different lengths of time.

## Persistent State vs Runtime State

Persistent state survives program restart.

Current persistent examples:

```text
profile.json
memories.json
```

Runtime state exists only while the process is running.

Current examples:

```text
conversation_history
last_provider_used
```

Understanding this distinction explains why memories survive restarts while conversation history currently does not.

## JSON Is a Simple Persistence Format

Solitude-Kaizen currently stores structured data in JSON.

Example memory:

```json
{
  "text": "Practice Python",
  "category": "learning",
  "importance": 4,
  "created_at": "2026-08-27T18:00:00"
}
```

JSON is appropriate for the current V1 scale because it is:

```text
simple
human-readable
easy to inspect
easy to load with Python
easy to back up
```

A database is not automatically better simply because it is more advanced.

## Data Schemas Matter

Once data is persisted, its structure becomes part of the application design.

Current memory fields are:

```text
text
category
importance
created_at
```

Changing persistent structure requires thinking about older data.

That is why `normalize_memory()` exists.

## Backward Compatibility

Older memories may not contain fields added later.

Instead of discarding them, the program normalizes legacy formats into the current structure.

General lesson:

> Stored data often lives longer than the code version that created it.

Applications should consider how old data behaves after software changes.

## Ranking Is Different From Relevance

Current memory selection prioritizes:

```text
importance
then recency
```

This is ranking.

It is not semantic relevance.

A highly important memory can rank highly even if it is unrelated to the user's current question.

Future semantic retrieval would solve a different problem.

Understanding this distinction prevents calling a current design limitation a bug.

## Conversation Context Is State Selection

The application does not send unlimited conversation history to the model.

Instead, it selects recent messages.

Current values:

```text
Stored short-term history: 20 messages
Prompt conversation context: 6 recent messages
```

This demonstrates an important concept:

> Stored state and supplied context do not need to be identical.

## Order of Operations Matters

The conversation duplication bug demonstrated that correct functions can still create incorrect behavior when called in the wrong order.

Correct user-turn sequence:

```text
Build context from previous history
        |
        v
Add current user message to history
        |
        v
Send current message separately
```

If the current message is added before the context is built, it can be included twice.

Program correctness depends on both individual functions and their orchestration.

## Helpers Should Own Their Responsibility

A previous bug occurred because:

```text
prepare_user_turn()
```

already added the user message, while `main.py` also added it manually.

Similarly:

```text
record_assistant_response()
```

already added the assistant response.

This produced duplicate history entries.

Lesson:

> If a helper owns an operation, callers should not silently repeat that operation.

Function names and contracts should make ownership clear.

## Failed Operations Should Not Corrupt State

A user turn is temporarily added before inference occurs.

If the provider request ultimately fails, that unanswered turn should not remain in history.

The CLI therefore removes it.

This is similar to a small transaction:

```text
prepare state
    |
attempt operation
    |
success -> keep state
failure -> undo temporary state
```

The general principle is:

> Failed operations should leave the system in a coherent state.

## Exceptions Separate Failure From Normal Results

A provider response is normal program data.

A provider failure is not a valid AI response.

Instead of returning strings such as:

```text
"Groq failed."
```

as if they were normal responses, provider adapters raise:

```python
ProviderError
```

This separates successful values from exceptional control flow.

## Structured Errors Are Better Than Error Strings

`ProviderError` stores fields such as:

```text
provider
kind
retryable
fallback_allowed
```

That means code can reason about the failure structurally.

For example:

```python
if error.fallback_allowed:
```

is much stronger than:

```python
if str(error) == "Groq failed":
```

Human-readable wording can change.

Structured fields represent stable machine-readable meaning.

## User Messages Should Not Control Internal Routing

One important rule learned during provider reliability work is:

> Never use a user-visible sentence as an internal error signal.

For example, this would be fragile:

```python
if response == "All available AI providers are currently unavailable.":
```

The sentence is presentation.

It should not become part of the routing protocol.

Internal decisions should use structured program state.

## Retry and Fallback Are Different Concepts

A failure can be temporary without meaning another provider should be used.

Likewise, a failure can be permanent for the current provider while another provider can still answer.

Therefore:

```text
retryable
```

and:

```text
fallback_allowed
```

are separate fields.

Example:

```text
Missing Groq API key

retryable = False
fallback_allowed = True
```

Retrying Groq with the same missing key is not useful.

Trying Ollama may still succeed.

## Safe Defaults Matter

`fallback_allowed` defaults to:

```text
False
```

This means an unknown new error type does not automatically trigger another provider.

Safety-oriented defaults are useful because new failures may have behavior that has not been considered yet.

## Fallback Should Be Bounded

Current fallback direction:

```text
Groq -> Ollama
OpenAI -> Ollama
```

Ollama does not automatically route back into another cloud provider.

This prevents circular logic such as:

```text
A -> B -> C -> A -> B -> ...
```

Simple bounded routing is easier to understand and debug.

## Provider Independence Is Architectural

Solitude-Kaizen should own:

```text
identity
memory
conversation state
behavior
provider routing
```

Providers should supply inference.

This creates the principle:

> One companion, many replaceable brains.

If a provider changes or disappears, the companion architecture should remain understandable and replaceable.

## Adapter Functions Isolate Provider APIs

Groq, OpenAI, and Ollama expose different interfaces.

The application isolates those differences inside provider-specific functions.

Conceptually:

```text
Solitude-Kaizen
      |
      v
common router
      |
  +---+---+
  |   |   |
Groq Ollama OpenAI
```

The rest of the system should not need to know every provider SDK detail.

## Local and Cloud Models Have Different Trade-Offs

Cloud inference can provide:

```text
lower local hardware usage
large models
fast responses when service is healthy
```

but depends on:

```text
internet
provider availability
quotas
credentials
external services
```

Local inference can provide:

```text
provider independence
offline potential
no per-request cloud charge
local control
```

but consumes:

```text
RAM
GPU resources
storage
local compute time
```

Neither is universally better.

The architecture can use both according to their strengths.

## Model Choice Is an Engineering Decision

The original local Qwen3 thinking variant produced long reasoning behavior and slow fallback responses.

The instruct variant:

```text
qwen3:4b-instruct
```

was better suited to the fallback role.

General lesson:

> The most capable-looking model is not automatically the best model for a specific system role.

Latency, resource usage, predictability, and task fit all matter.

## Configuration Should Have One Source of Truth

A bug existed because:

```python
OLLAMA_TIMEOUT_SECONDS = 120.0
```

was defined, while the actual HTTP call separately used:

```python
timeout=120
```

Both values happened to agree.

The implementation was corrected to:

```python
timeout=OLLAMA_TIMEOUT_SECONDS
```

General lesson:

> Configuration values should have an authoritative definition.

Duplicated configuration values can silently drift apart.

## Tests Can Pass for the Wrong Reason

The original timeout test checked:

```text
actual timeout == OLLAMA_TIMEOUT_SECONDS
```

But production code used literal `120`, while the constant was `120.0`.

The test still passed because:

```text
120 == 120.0
```

This revealed an important testing lesson:

> A passing assertion is useful only if the test actually proves the intended relationship.

## Test Relationships, Not Coincidences

The stronger timeout test temporarily changes:

```text
OLLAMA_TIMEOUT_SECONDS
```

to a distinctive value such as:

```text
37.0
```

and verifies that the HTTP request receives `37.0`.

This proves that production code references the configuration value.

That is stronger than proving two current values happen to match.

## `monkeypatch` Enables Controlled Tests

Pytest's `monkeypatch` can temporarily replace:

```text
environment variables
functions
constants
network calls
```

Example purposes:

```text
simulate missing API key
simulate provider failure
capture timeout value
replace real network request
control active provider
```

After the test finishes, pytest restores the original state.

This allows deterministic testing without damaging the real environment.

## Unit Tests and Live Tests Serve Different Purposes

Mocked tests can verify precise logic quickly.

Examples:

```text
error classification
fallback routing
provider tracking
timeout wiring
memory ranking
conversation trimming
```

Live tests verify integration with real systems.

Examples:

```text
actual Groq response
actual Ollama response
real CLI menu behavior
real fallback from cloud failure to local inference
```

A strong project uses both where appropriate.

## A Mock Can Hide Integration Problems

A mocked provider may always return exactly what the test expects.

The real provider may have:

```text
network behavior
SDK retries
authentication
model availability
latency
format differences
```

Therefore, important integrations should eventually receive controlled live testing.

## Tests Need Unique Names

Python module definitions follow normal name-binding rules.

If two test functions have the same name:

```python
def test_example():
    ...

def test_example():
    ...
```

the later definition replaces the earlier one when the module loads.

A green test suite can therefore contain fewer executed tests than expected.

Monitoring test count can reveal this kind of mistake.

## Test Count Is a Useful Signal

The current V1 baseline is:

```text
63 passed
```

The number itself is not a quality score.

However, unexpected changes in the number can signal:

```text
duplicate test names
test discovery problems
deleted tests
renamed files
collection errors
```

The meaning of tests matters more than raw quantity.

## Error Boundaries Improve User Experience

Provider SDKs may raise technical exceptions.

Normal CLI users should not receive raw stack traces for expected provider failures.

Architecture layers can handle this progressively:

```text
provider adapter
    -> classify technical error

provider router
    -> decide fallback

CLI
    -> display final readable result
```

Each layer owns a different responsibility.

## Diagnostics and User Messages Can Coexist

A CLI can provide a readable explanation and also include a compact technical diagnostic such as:

```text
Diagnostic: config/invalid_provider
```

This helps debugging without exposing a raw traceback.

## Environment Variables Separate Configuration From Code

Values such as:

```text
AI_PROVIDER
GROQ_API_KEY
OPENAI_API_KEY
```

are configuration, not application logic.

They should not be hard-coded into Python source.

This allows the same program to behave differently across environments without editing code.

## `.env` and `.env.example` Have Different Roles

`.env` contains real local configuration and may contain secrets.

It should not be committed.

`.env.example` documents the expected variable names using safe placeholders.

This lets other developers understand configuration without receiving private credentials.

## Secrets in Git History Are Different From Local Secrets

Deleting a secret from the current file does not necessarily remove it from previous Git commits.

If a real credential enters Git history, it should be treated as exposed.

The correct response usually includes credential rotation.

General lesson:

> Version-control history matters when evaluating secret exposure.

## Dependency Count Has a Cost

Every dependency adds potential:

```text
updates
compatibility issues
security risk
API changes
installation complexity
```

A library should be added because it solves a real problem, not simply because it is popular.

Current decision rule:

```text
Does it reduce complexity?
Does it improve reliability?
Does it provide genuinely required capability?
```

## More Infrastructure Is Not Automatically More Professional

Solitude-Kaizen currently uses:

```text
JSON rather than a database
explicit provider routing rather than a gateway
a CLI rather than a GUI
direct Ollama HTTP rather than a large local stack
```

These are intentional V1 trade-offs.

Professional engineering includes choosing the simplest design that satisfies current requirements.

## Documentation Has Different Audiences

Different documentation files now have different responsibilities.

```text
README.md
    -> users and repository visitors

PROJECT_CONTEXT.md
    -> development continuity

ARCHITECTURE.md
    -> structural design

ROADMAP.md
    -> scope and release direction

TROUBLESHOOTING.md
    -> failure diagnosis

LEARNING_NOTES.md
    -> engineering understanding
```

Separating these purposes reduces duplication and makes information easier to find.

## Documentation Should Match Reality

Documentation can become incorrect even when the code still works.

The original README still described the repository as a first VS Code and Git project long after Solitude-Kaizen had become a multi-provider AI assistant.

General lesson:

> Documentation is part of the system and should evolve with the implementation.

## Linting Is a Tool, Not the Goal

Markdownlint found useful issues such as missing final newlines.

It also produced noisy warnings for legitimate repeated troubleshooting headings and long documentation lines.

Instead of disabling linting completely, configuration was adjusted:

```json
{
  "MD013": false,
  "MD024": {
    "siblings_only": true
  }
}
```

General lesson:

> Configure development tools to support useful standards rather than blindly satisfying every default rule.

## Diagnose Before Changing

When unexpected behavior appears, avoid making several speculative fixes.

A better sequence is:

```text
Observe
  |
  v
Collect evidence
  |
  v
Identify the smallest likely cause
  |
  v
Test the hypothesis
  |
  v
Make one correction
```

Examples include:

```text
checking git diff before restoring a file
checking Test-Path before recreating a document
checking active provider before editing .env
checking Ollama model list before changing model configuration
```

## Reversible Changes Reduce Risk

Safe debugging prefers actions that are easy to undo.

Examples:

```text
temporary environment variables
monkeypatch in tests
small Git commits
configuration inspection
focused code edits
```

Riskier actions include:

```text
deleting repositories
rewriting Git history
removing security controls
mass-upgrading dependencies
large untested refactors
```

## Reliability Before Variety

Supporting many providers is not valuable if provider failures are unpredictable.

Therefore the project prioritized:

```text
error classification
fallback rules
timeouts
provider tracking
CLI error handling
```

before adding more AI providers.

This produced the reliability principle:

> Reliability before variety.

## Classification Before Retry

Before deciding what to do with a failure, identify what type of failure occurred.

Examples:

```text
timeout
connection
authentication
rate limit
bad request
server error
configuration error
```

Different failures should not automatically receive identical treatment.

This produces:

> Classification before retry.

## Fallback Before Failure

When the primary cloud provider cannot answer and another valid provider can safely handle the request, controlled fallback is preferable to immediately failing the whole user interaction.

This produces:

> Fallback before failure.

Fallback still needs boundaries and error classification.

## Independence Before Convenience

Using one provider's proprietary memory or conversation system might initially be convenient.

However, keeping identity and state inside Solitude-Kaizen improves provider independence.

This produces:

> Independence before convenience.

## Simplicity Before Infrastructure

Complexity should be earned by a real requirement.

Do not add:

```text
gateways
queues
agents
databases
circuit breakers
frameworks
containers
```

simply because mature production systems sometimes use them.

First identify the problem that requires the infrastructure.

This produces:

> Simplicity before infrastructure.

## Current Engineering Principles

The most important principles learned so far are:

```text
One companion, many replaceable brains.

Reliability before variety.

Classification before retry.

Fallback before failure.

Independence before convenience.

Simplicity before infrastructure.

Never use a user-visible sentence as an internal error signal.

Configuration should have one authoritative source.

Test relationships, not coincidences.

Failed operations should leave state coherent.

Diagnose before changing.

Small understandable changes are easier to maintain.
```

## Skills to Deepen After V1

After the V1 release, useful areas for deeper study include:

```text
Python classes and object-oriented design
type hints
dataclasses
exceptions
HTTP and REST APIs
JSON serialization
environment configuration
pytest fixtures
mocking and monkeypatching
software architecture
dependency management
logging
CLI design
Git branching
GitHub workflows
security fundamentals
async programming
databases
semantic search
embeddings
RAG
local model inference
API design
```

These topics do not all need to be added to Solitude-Kaizen immediately.

They can be studied independently and introduced only when they improve the system.

## Long-Term Learning Goal

The project should gradually change the developer's relationship with AI assistance.

Early stage:

```text
AI explains
Developer follows carefully
```

Intermediate stage:

```text
Developer predicts
AI reviews and assists
```

Advanced stage:

```text
Developer designs
AI accelerates implementation and research
```

The objective is not to stop using AI.

The objective is to become capable of understanding, evaluating, and directing the engineering work.

## Controlled Continuous Learning V1

Continuous improvement does not require continuous self-modification.
A safer first design is a small orchestrator around independently
bounded steps: collect evidence when explicitly allowed, prepare one
offline lesson, wait for reflection, and leave every proposal under
human review.

Separate configuration switches prevent a local learning preference
from silently enabling network access. A daily creation limit also
prevents repeated application restarts from producing an uncontrolled
lesson backlog.

## Safe Restore V1

A backup is useful only when recovery is both possible and controlled.
A safe restore is not a simple copy operation because several files
represent one companion state. A failure after replacing only some of
them could mix old and new identity, profile, memories, and database
records.

The first restore design therefore behaves like a small transaction:

```text
verify -> preview -> confirm -> emergency backup
       -> staged replacement -> verify -> rollback on failure
```

The preview is read-only and names every fixed target. Confirmation must
match the displayed phrase exactly. Temporary files are written and
flushed before replacement, and the emergency backup remains available
even after success.

SQLite also teaches an important distinction between bytes and meaning.
Two consistent snapshots may have different header bytes while storing
the same schema and records. File hashes remain correct for verifying a
bundle against its manifest, while restore planning compares logical
SQLite contents to avoid unnecessary database replacement.

The first version refuses to restore over an already invalid live state.
That limitation is deliberate: automatic rollback is only honest when
the system can first create and verify a recovery point for what exists
now. Damaged-state recovery needs a separate guided procedure.
