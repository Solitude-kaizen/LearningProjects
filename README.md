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

The current version is a command-line application with:

- Persistent local memory
- Short-term conversation history
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

The project currently has **174 passing tests** covering memory,
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

Solitude-Kaizen V1 is currently tested with:

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

Create your local `.env` file from `.env.example`.

PowerShell:

```powershell
Copy-Item .env.example .env
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
- Clearing conversation history
- Viewing conversation status
- Collecting zero-cost public research
- Viewing the public research inbox
- Viewing the latest Daily Kaizen proposal
- Optionally starting a short, metadata-based study activity
- Recording a local reflection and viewing learning progress
- Approving, rejecting, or postponing completed lesson proposals
- Viewing proposal review history
- Creating and verifying a local continuity backup
- Rechecking the latest continuity backup
- Previewing and safely restoring the latest continuity backup

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

## Running Tests

Run the automated test suite with:

```powershell
python -m pytest -q
```

The project currently has **174 passing tests** covering memory,
conversation handling, provider routing, fallback behavior, error
handling, configuration, SQLite storage, public research collection,
the offline learning loop, proposal controls, continuity backups, and
safe restoration rollback.

## Memory

Long-term memories are stored locally.

Menu option 6 previews the selected memory before asking for confirmation.
Only `yes` (ignoring capitalization and surrounding spaces) permits
deletion and saving. Any other answer cancels without changing the list
or writing the memory file. Invalid selections also make no changes.

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

## Reliability

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

## Current V1 Limitations

V1 intentionally remains focused.

Not currently included:

- GUI
- Voice interaction
- Web search
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
