# Solitude-Kaizen

Solitude-Kaizen is a personal AI assistant project built as a long-term learning project in Python.

The project focuses on building an AI companion whose identity, memory, context, and behavior remain independent from any single AI provider.

> One companion, many replaceable brains.

## Project Status

**V1.0.0 has been released.**

V2 development adds small, tested foundations. Current V2 work includes SQLite
storage, a human-reviewed Daily Kaizen proposal, and a zero-cost public
research inbox. The optional Learning Guide (formerly Learning Brain V1)
uses templates around saved metadata to suggest short study activities
and pending improvement proposals. It is not model training. Proposal
Control V1 lets the creator approve, reject, or postpone that proposal
without executing it. Lifetime Continuity V1 creates verified local
bundles of SK's identity and runtime data. Safe Restore V1 adds a
previewed recovery path with exact confirmation, an emergency backup,
post-restore verification, and automatic rollback. Normal startup checks
only permitted research sources; it does not create lessons or request
reflections.

The current focus is a useful companion: conversation, memory, and
source-linked AI research. Study activities are optional and never block
chat or research. Earlier brainstorming is not a feature commitment.

V2 work continues from an internal checkpoint, not a public V2 release.
A public release is optional and requires separate approval. The proposed
scope, verified checks, and any future public-release steps are recorded in
[V2_RELEASE_CHECKLIST.md](V2_RELEASE_CHECKLIST.md). HR, business, and research
workflows are a requested future direction, not installed agent skills.

The current version is a command-line application with:

- Persistent local memory
- Short-term conversation history
- Optional reviewed session note for continuity between launches
- Optional single-source review of pasted text, with checked literal quotations
- Context-aware prompting
- Multiple AI providers
- Automatic cloud-to-local fallback
- Structured provider error handling
- Provider status and diagnostics
- Local Ollama support
- Zero-cost public research collection from GitHub, Hacker News,
  arXiv, and a curated YouTube feed
- SQLite storage for research items and collection history
- Optional, on-demand Learning Guide with one active short lesson at a time
- Local reflection history and human-reviewed improvement proposals
- Append-only proposal review history with reasons and timestamps
- Allowlisted continuity backups with hash and SQLite integrity checks
- Guarded continuity restoration with preview and automatic rollback
- Automated tests

Latest local verification: **660 passed** (2026-09-15). The `codecs.decode`
test typo is corrected. The calculator's 35 tests also pass independently.
The suite covers memory,
conversation handling, provider routing, fallback behavior, error
handling, configuration, SQLite storage, public research collection,
the offline learning loop, proposal controls, continuity backups, and
safe restoration rollback.

## AI Providers

Solitude-Kaizen currently supports:

| Provider | Type | Purpose |
| --- | --- | --- |
| Groq | Cloud | Default AI provider |
| Ollama | Local | Local provider and fallback |
| OpenAI | Cloud | Optional provider |

The current local Ollama model is:

```text
qwen3:4b-instruct

```

When an eligible Groq or OpenAI failure occurs, Solitude-Kaizen can automatically fall back to Ollama.

## Core Design Principle

Solitude-Kaizen owns:

- Identity
- Memory
- Conversation context
- Behavior
- Provider routing

AI providers supply replaceable inference.

This keeps the project from becoming permanently dependent on one AI service.

> One companion, many replaceable brains.

## Requirements

The current development checkout is tested with:

```text
Python 3.14.7
```

Runtime dependencies are pinned in:

```text
requirements.txt
```

Development dependencies are stored in:

```text
requirements-dev.txt
```

## Installation

Clone the repository and enter the project directory.

Install the development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

## Environment Configuration

For a new installation only, create your local `.env` file from
`.env.example`. Keep an existing `.env`; do not overwrite its credentials
or preferences when updating SK.

PowerShell:

```powershell
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

Choose the AI provider:

```env
AI_PROVIDER=groq
```

Valid values are:

```text
groq
ollama
openai
```

For Groq:

```env
GROQ_API_KEY=your_groq_api_key_here
```

For OpenAI:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Ollama runs locally and does not require an API key.

Automatic public research collection is optional and disabled by
default:

```env
SK_RESEARCH_ENABLED=false
```

The CLI can still run the collector manually. It reads public metadata
and does not call a paid AI model.

The inbox shows each link's domain and a conservative URL-based source
type (for example, code hosting, preprint archive, or documentation site).
Unknown sites remain unknown. These hints are computed locally when
viewing the inbox; they do not fetch links, migrate stored records, or
certify claims. A source type is not a quality rating or a security check.

The Learning Guide is opened manually from the menu. Normal CLI startup
does not prepare lessons, even if an older `.env` contains
`SK_CONTINUOUS_LEARNING_ENABLED=true`. That flag is retained only for
explicit callers of the legacy `run_controlled_learning_cycle` helper;
it is no longer a normal startup setting. Existing study records remain
available. No configuration or data migration is required.

For a zero-cost research workflow, keep `KAIZEN_DISCOVERY_ENABLED=false`
and enable automatic public collection only if you want startup network
access. Chat-provider costs depend on the provider you select.

Never commit your real `.env` file or API keys.

## Local Ollama Setup

Install Ollama separately, then download the local model:

```powershell
ollama pull qwen3:4b-instruct
```

Verify the model is installed:

```powershell
ollama list
```

The Ollama service must be available at:

```text
http://localhost:11434
```

## Running Solitude-Kaizen

### One Local Session Without Changing Saved Settings

Open a new PowerShell window in the project root. With Ollama running and
the existing model installed, use these process-only settings:

```powershell
$env:AI_PROVIDER = "ollama"
$env:SK_RESEARCH_ENABLED = "false"
$env:KAIZEN_DISCOVERY_ENABLED = "false"
$env:SK_CONTINUOUS_LEARNING_ENABLED = "false"
python -m src.solitude_kaizen.main
```

Choose 13 to check that the provider is Ollama, then 12 to chat. Exit with
27 and close this new PowerShell window when finished. These settings do
not edit `.env` or change preferences in other terminal windows. Normal
startup still creates/normalizes local runtime files as usual.

This disables automatic research; it is not a network sandbox. Do not
choose manual research collection (17) during a local-only session.
Local chat does not retrieve current internet information.

### Normal Startup

From the project root:

```powershell
python -m src.solitude_kaizen.main
```

The CLI currently provides options for:

- Viewing and changing goals
- Managing memories
- Searching memories
- Filtering and ranking memories
- Talking with Solitude-Kaizen
- Viewing the active AI provider
- Clearing conversation history after preview and confirmation
- Viewing conversation status
- Collecting zero-cost public research
- Viewing the public research inbox
- Viewing the latest Daily Kaizen proposal
- Optionally starting a short, metadata-based study activity
- Recording a local reflection and viewing learning progress; `/cancel`,
  Ctrl+C, or end-of-input at the reflection prompt leaves the lesson
  unfinished without saving a reflection
- Approving, rejecting, or postponing completed lesson proposals; `/cancel`,
  Ctrl+C, or end-of-input at any review prompt exits without recording a decision
- Viewing proposal review history
- Creating and verifying a local continuity backup
- Rechecking the latest continuity backup
- Previewing and safely restoring the latest continuity backup

Option 31, Memory Lens, previews which saved memories chat would select for
a question. It shows shared keywords or the importance/recency fallback,
using the actual selector rather than a model-generated explanation.
It makes no network/model calls, saves nothing, and does not add a chat turn.
Blank input, `/cancel`, Ctrl+C, or end-of-input cancels; questions are limited
to 2000 characters. This is only a memory-selection preview, not a full
outgoing prompt preview or an explanation of a model's reasoning. Recent
chat and a resumed note can also enter chat context. Previewing does not
reserve a selection or authorize a later cloud request.

Option 32 offers reviewed chat: inspect the complete application system
prompt (selected memories, recent chat, and any resumed note) and your
message before typing `yes` to send. Anything else, Ctrl+C, or end-of-input
at confirmation cancels without changing history or making a model call.
The original application texts represented by the preview are passed to the response function;
provider wrappers may add formatting, and existing fallback rules apply.
This preview is displayed locally and may expose personal text on screen.
It is not a secret scanner or a guarantee about provider-side processing.
Ordinary chat (option 12) remains a one-prompt workflow without this preview.
See [the context preview guide](CONTEXT_PREVIEW_GUIDE.md) for a short
walkthrough, an offline verification example, and privacy boundaries.

Both new previews escape backslashes and hidden control/format characters
for display (for example, an escape character appears as `\u001b`). Original
text is not rewritten or cleaned before sending. This helps expose hidden
terminal controls; it does not verify content, remove secrets, or secure all
legacy screens. Normal Unicode and line breaks remain readable.

Continuity bundles are stored under the ignored local `data/backups`
directory. They contain SK's identity, profile, memories, and a
consistent SQLite snapshot. They never include `.env` or arbitrary
project files. The ZIP is not encrypted, so it must be kept private.

A restore first verifies the selected bundle and previews every affected
file. It requires the exact displayed confirmation phrase, creates and
verifies an emergency backup of the current state, restores through
temporary files, and verifies the result. If a write or verification
fails, SK automatically rolls back from the emergency backup. A
successful restore closes the CLI so the restored state is loaded
cleanly on the next start. Safe Restore V1 requires all current
continuity files to be valid enough to protect first; recovery from an
already missing or corrupted live file remains a guided future step.

At the confirmation prompt, Ctrl+C or end-of-input cancels without changing
live files or creating an emergency backup. This safeguard applies before
restoration starts, not to interruption during restoration.

## Exact Calculator

Option 33 calculates from two supplied decimal numbers and `+ - * /`.
For example, `1250.50 / 25` produces `50.02`. Inputs are limited to 50
characters without commas, units, or exponents. Repeating decimals remain
exact fractions; no currency rounding is applied. Blank input, `/cancel`,
Ctrl+C, or end-of-input cancels. Nothing is sent, saved, or added to chat.
This checks arithmetic, not real-world assumptions or numbers in AI replies.

## Running Tests

Run the automated test suite with:

```powershell
python -m pytest -q
```

Latest local verification: **660 passed**. The suite covers memory,
conversation handling, provider routing, fallback behavior, error
handling, configuration, SQLite storage, public research collection,
the offline learning loop, proposal controls, continuity backups, and
safe restoration rollback.

## Memory

Long-term memories are stored locally.

Option **4** previews a new memory's text, category, and importance before
saving. Only `yes` confirms. Blank text, `/cancel`, Ctrl+C, or EOF cancels
before saving; text is limited to 1000 characters. Invalid categories or
importance values can be corrected. New memories may be selected for later
cloud chat, so never store credentials. The shared list is updated only
after the atomic save succeeds; a failed save adds nothing.

Menu option 6 previews the selected memory before asking for confirmation.
Only `yes` (ignoring capitalization and surrounding spaces) permits
deletion and saving. Any other answer cancels without changing the list
or writing the memory file. Invalid selections also make no changes.
`/cancel` at selection, Ctrl+C, or EOF cancels deletion without a traceback.
The shared memory list changes only after saving succeeds; failed saves leave
the existing file and live list intact.

Options **7** (search) and **8** (category lookup) are read-only. Blank input,
`/cancel`, Ctrl+C, or EOF cancels and returns to the menu without displaying
memory contents. Nonblank input ignores surrounding spaces. A blank search
no longer implicitly shows every memory; use option **5** to view all memories.
These lookups do not save, call a model, or use the network.

Memories support:

- Categories
- Importance levels
- Timestamps
- Search
- Filtering
- Ranking
- Topic-aware context selection

During chat, SK matches words in the current question against saved
memory text and categories. When matches exist, only matching memories
are included, up to five, ordered by distinct keyword overlap and then
the existing importance/recency ranking. If there is no match, the
previous ranking is used. This is simple keyword retrieval, not semantic
understanding or model training, and it does not change stored memories.

Short-term conversation history currently exists only while the program is running.

In menu option 12, pressing Enter without a message (or entering only
whitespace) cancels that chat request and returns to the menu. Ctrl+C or
end-of-input at the `You:` prompt also cancels. No AI request is made and
the existing conversation is unchanged. Nonblank messages keep their
original formatting. This safeguard applies before sending a message;
it does not cancel a provider request already in progress.

Menu option 14 previews how many messages will be cleared. Only `yes`
(ignoring capitalization and surrounding spaces) clears the current
session's chat; saved memories and other files are untouched. Any other
answer, or an interruption at the confirmation prompt, cancels without
changing the conversation. Clearing also detaches a resumed session note,
without deleting its saved copy. Empty history needs no confirmation only
when no note is active. A confirmed clear cannot be undone within the session.

## Optional Session Continuity

Option **28** prepares a local session-note draft. It copies only the latest
user message into the topic (up to 600 characters, marked if truncated).
It does not summarize the whole conversation or infer decisions from model
replies. You can also prepare a note with no chat history. Review four fields:
topic, approved decisions, unresolved questions, and a possible next step.
Blank input keeps a field, `/clear` empties it, and `/cancel` cancels. Each
field is limited to 600 characters. At the final preview, `edit` revises the
draft and only `yes` saves it. Saving replaces the one existing note, after
showing that existing note. These controls make no AI or network request.

Option **29** displays the saved note and offers:

- `resume`: asks for `yes` before including the note in later option-12 chats
  for this session. A cloud provider receives it when cloud chat is used.
- `edit`: preview and explicitly save corrections; resume again to activate them.
- `dismiss`: detach the note from direct chat context while keeping its saved copy.
- `forget`: preview and require `yes` before deleting just the saved note.

Cancelling or interrupting an edit or confirmation preserves saved data and
active context. Startup shows only an availability hint; it does not display
the note's content or activate it. Saving never activates the note. Option
**27** remains exit and never saves a note automatically. Study activities
remain optional and independent of this feature.

The note is stored as a separate top-level `session_note` in the existing
private `memories.json`, outside automatic keyword memory selection. Writes
use a same-directory temporary file and atomic replacement. Ordinary memories
and other fields are preserved. Continuity bundles include the note without
a format change and remain unencrypted. Never put credentials in a note.
Forgetting a note does not remove copies in earlier backups or details in
existing chat; option **14** clears the current chat and detaches active context.
Unsupported or malformed notes remain stored but inactive, pending separate
recovery guidance. Full transcripts are still session-only.

A bounded [local session-note check](SESSION_NOTE_EVALUATION.md) exercised
missing context, resumed context, and a changed plan using a fictional note.
All three requests completed; this is limited evidence, not a general
model-quality guarantee or a test with personal data.

## Optional Source Review

Option **30** accepts one source title, an optional HTTP(S) link, a pasted
excerpt, and your question. Finish the excerpt with `/done` on its own line;
`/cancel`, Ctrl+C, or EOF before confirmation cancels without sending anything.
The excerpt is limited to 6000 characters / 100 lines; title and question
are bounded too. Source links cannot contain embedded credentials.

SK previews exactly this input and the configured provider. Only `yes` sends
the review request. Cloud use sends the supplied material to that provider
and may incur costs; existing fallback rules apply. Personal memories, session
notes, profile, and conversation history are excluded. No links are fetched,
no tools are executed, and neither the input nor review is saved by SK.

The model is asked for an interpretation, exact quoted evidence, and
uncertainties. SK checks response structure and requires each quote to appear
in the supplied excerpt. An unsupported quote or malformed response is rejected
without automatically retrying. Matching words does not prove the source is
true or that an interpretation follows from it. The source link is user-supplied
provenance, not a verified association. Review outputs remain fallible.

See [the bounded local evaluation](SOURCE_REVIEW_EVALUATION.md), including a
known tendency to list tangential caveats. Interrupting an already-sent request
cannot undo transmission; the CLI reports that distinction.

## Reliability

Changing the current goal (option 2) now also saves a candidate profile before
updating the live goal. Failed saves retain the previous goal. `/cancel`,
Ctrl+C, or EOF cancels the edit; blank input still clears the goal as before.

Profile, memory, and session-note JSON saves share an atomic writer: serialize
and flush a temporary file beside the destination, then replace the old file.
Failures before replacement preserve the old file; ordinary failure cleanup
removes the temporary file. This does not provide multi-process locking,
replace backups, or guarantee recovery from every power-loss scenario.

Ctrl+C or EOF at the main menu exits cleanly without automatically saving a
session note. Unknown choices display a short hint and menu choices tolerate
surrounding spaces. These safeguards do not imply that every older prompt
already handles interruptions or that an in-flight provider call can be undone.
Ctrl+C during the chat response call now removes the unanswered session turn
and returns control without SK resubmitting the turn. The request may already have
reached its provider; this does not guarantee server-side cancellation.
The all-providers-unavailable result likewise does not become a saved chat turn.
Blank or non-text replies are rejected without printing the malformed output
or retaining the unanswered turn, in ordinary and reviewed chat alike.

The current reliability philosophy is:

> Reliability before variety.  
> Classification before retry.  
> Fallback before failure.  
> Independence before convenience.  
> Simplicity before infrastructure.

Provider failures use structured internal errors rather than user-visible sentences as control signals.

Providers are recorded as successfully used only after they actually return a response.

## Security

- `.env` is ignored by Git.
- `.env.example` contains placeholders only.
- API keys should never be stored in the memory system.
- Dependencies are pinned to tested versions.
- Real secrets should never be committed to Git history.

## Current Limitations

The current V2 development checkout retains these boundaries.

Not currently included:

- GUI
- Voice interaction
- General web search (the public AI-metadata collector is available)
- Autonomous agents
- Computer control
- Discord integration
- Large provider frameworks
- Persistent conversation history between program launches

These may be considered in future versions after the core system is stable.

## Development Philosophy

Solitude-Kaizen is also a learning project.

Changes are developed incrementally:

1. Understand the problem.
2. Make a small change.
3. Test the behavior.
4. Verify it in the real application when appropriate.
5. Commit a clean Git checkpoint.
6. Continue improving.

The goal is not only to build an AI assistant, but to understand the engineering behind it.
