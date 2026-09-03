# Solitude-Kaizen

Solitude-Kaizen is a personal AI assistant project built as a long-term learning project in Python.

The project focuses on building an AI companion whose identity, memory, context, and behavior remain independent from any single AI provider.

> One companion, many replaceable brains.

## Project Status

**V1.0.0 has been released.**

V2 development is now adding small, tested foundations without
changing the released V1 behavior. Current V2 work includes SQLite
storage, a human-reviewed Daily Kaizen proposal, and a zero-cost public
research inbox. Learning Brain V1 turns one inbox item at a time into
an offline baby-step lesson and a pending improvement proposal. Proposal
Control V1 lets the creator approve, reject, or postpone that proposal
without executing it. Lifetime Continuity V1 creates verified local
bundles of SK's identity and runtime data. Safe Restore V1 adds a
previewed recovery path with exact confirmation, an emergency backup,
post-restore verification, and automatic rollback. Controlled
Continuous Learning V1 connects the learning parts at startup and can
prepare at most one offline lesson per day when explicitly enabled.

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
- Offline Learning Brain with one active baby-step lesson at a time
- Opt-in controlled learning cycle with a one-lesson-per-day limit
- Local reflection history and human-reviewed improvement proposals
- Append-only proposal review history with reasons and timestamps
- Allowlisted continuity backups with hash and SQLite integrity checks
- Guarded continuity restoration with preview and automatic rollback
- Automated tests

The project currently has **133 passing tests** covering memory,
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

Automatic offline lesson preparation is also optional and disabled by
default:

```env
SK_CONTINUOUS_LEARNING_ENABLED=false
```

When enabled, SK checks the existing research and prepares at most one
baby-step lesson per local calendar day. This setting does not turn on
network access, retrain a model, approve a proposal, or change code.
For a zero-cost bounded cycle, keep `KAIZEN_DISCOVERY_ENABLED=false`,
and enable the public collector and continuous-learning settings only
after choosing automatic startup access.

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
- Starting one source-grounded baby-step lesson
- Preparing at most one daily lesson automatically when opted in
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

The project currently has **133 passing tests** covering memory,
conversation handling, provider routing, fallback behavior, error
handling, configuration, SQLite storage, public research collection,
the offline learning loop, proposal controls, continuity backups, and
safe restoration rollback.

## Memory

Long-term memories are stored locally.

Memories support:

- Categories
- Importance levels
- Timestamps
- Search
- Filtering
- Ranking
- Context selection

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
