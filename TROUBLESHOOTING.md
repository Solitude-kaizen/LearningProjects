# Solitude-Kaizen Troubleshooting

## Purpose

This document records common development, configuration, provider, Ollama, testing, Git, and documentation problems encountered while building Solitude-Kaizen.

The normal troubleshooting principle is:

> Diagnose the cause before changing the system.

Do not disable security controls, delete files, reinstall software, or introduce new dependencies until the actual failure has been identified.

## First Diagnostic Checks

When something unexpected happens, start with the smallest useful checks.

### Check Git State

```powershell
git status
```

This shows whether files are:

- Modified
- Staged
- Untracked
- Already committed

Do not assume a file was saved correctly just because it is visible in VS Code.

### Run the Test Suite

```powershell
python -m pytest -q
```

Current V1 baseline:

```text
61 passed
```

If the number unexpectedly decreases, investigate before continuing.

### Check the Active AI Provider

From PowerShell:

```powershell
python -c "from src.solitude_kaizen.ai_service import get_active_provider; print(get_active_provider())"
```

Expected default:

```text
groq
```

### Check Provider Environment Override

PowerShell:

```powershell
$env:AI_PROVIDER
```

If it contains a temporary test value, it may override `.env`.

To remove the PowerShell-session override:

```powershell
$env:AI_PROVIDER=$null
```

Then verify again:

```powershell
python -c "from src.solitude_kaizen.ai_service import get_active_provider; print(get_active_provider())"
```

## Invalid AI Provider

### Symptom

The application may display:

```text
Invalid AI provider configuration.
```

or:

```text
Diagnostic: config/invalid_provider
```

Option 13 may display:

```text
Could not read AI provider configuration.
Diagnostic: config/invalid_provider
```

### Cause

`AI_PROVIDER` contains a value outside the supported provider set.

Valid values are:

```text
groq
ollama
openai
```

### Check

```powershell
$env:AI_PROVIDER
```

Also inspect the local `.env` file without sharing its secrets publicly.

### Fix

Set a valid provider temporarily:

```powershell
$env:AI_PROVIDER="groq"
```

or remove the temporary override:

```powershell
$env:AI_PROVIDER=$null
```

Do not add arbitrary provider names to `VALID_PROVIDERS` merely to silence the error.

A provider should be added only when a real adapter exists.

## Groq API Key Missing

### Symptom

Internally, Groq raises:

```text
provider = groq
kind = missing_api_key
```

### Expected V1 Behavior

A missing Groq API key allows fallback to Ollama.

If Ollama is available, the request may still succeed locally.

### Check

Do not print the real API key.

Instead check whether the variable exists:

```powershell
if ($env:GROQ_API_KEY) {
    "GROQ_API_KEY is set"
} else {
    "GROQ_API_KEY is not set"
}
```

Remember that `python-dotenv` may also load the key from `.env`.

### Fix

Place the real key only in the local `.env` file.

Example structure:

```env
AI_PROVIDER=groq
GROQ_API_KEY=your_real_key_here
```

Never commit the real `.env` file.

## OpenAI API Key Missing

### Symptom

Internally:

```text
provider = openai
kind = missing_api_key
```

### Expected V1 Behavior

OpenAI is optional.

A missing OpenAI key may fall back to Ollama when OpenAI is the selected provider.

Solitude-Kaizen should not require OpenAI credentials when another provider is being used.

### Security Rule

Never paste a real OpenAI API key into:

```text
README.md
PROJECT_CONTEXT.md
ARCHITECTURE.md
ROADMAP.md
TROUBLESHOOTING.md
memory data
source code
Git commits
```

## Ollama Connection Failure

### Symptom

The application may report:

```text
Could not connect to Ollama.
```

Diagnostic classification:

```text
provider = ollama
kind = connection
```

### Likely Causes

- Ollama is not running
- Ollama is not installed
- The local service is unavailable
- The expected port is unavailable

Solitude-Kaizen currently expects Ollama at:

```text
http://localhost:11434
```

### Check Ollama

```powershell
ollama list
```

If the command itself is not recognized, Ollama may not be installed correctly or may not be available on PATH.

### Check Running Models

```powershell
ollama ps
```

### Verify the Local Service

PowerShell:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

If Ollama is available, this should return local model information.

## Ollama Model Missing

Current V1 local model:

```text
qwen3:4b-instruct
```

### Check

```powershell
ollama list
```

Look for:

```text
qwen3:4b-instruct
```

### Install If Missing

```powershell
ollama pull qwen3:4b-instruct
```

Do not silently change the application to another model merely because a different model happens to be installed.

The configured model and documentation should remain consistent.

## Ollama Is Very Slow

### Context

The original Qwen3 thinking model produced unnecessarily long reasoning behavior for the local fallback use case.

The current fallback model is:

```text
qwen3:4b-instruct
```

It was selected because it gives much faster and more predictable responses for this system.

### Check

```powershell
ollama ps
```

Also verify that the configured model in `ai_service.py` is:

```python
OLLAMA_MODEL = "qwen3:4b-instruct"
```

### Hardware Consideration

Local inference consumes system RAM and GPU resources.

Avoid running many heavy local AI applications at the same time when diagnosing performance problems.

Cloud-first operation keeps the local machine lighter during normal use.

## Ollama Timeout

Current configured timeout:

```text
120 seconds
```

The authoritative configuration is:

```python
OLLAMA_TIMEOUT_SECONDS = 120.0
```

The request should use:

```python
timeout=OLLAMA_TIMEOUT_SECONDS
```

rather than a duplicated literal value.

### Diagnostic

```text
provider = ollama
kind = timeout
```

Do not immediately increase the timeout.

First determine whether the problem is:

- Model loading
- Excessive generation
- Hardware pressure
- Wrong local model
- Ollama service problems

## Groq Timeout

Current configured timeout:

```text
20 seconds
```

Diagnostic classification:

```text
provider = groq
kind = timeout
```

A Groq timeout is considered eligible for local fallback.

The configured timeout belongs in:

```python
GROQ_TIMEOUT_SECONDS
```

## OpenAI Timeout

Current configured timeout:

```text
60 seconds
```

Diagnostic classification:

```text
provider = openai
kind = timeout
```

The configured timeout belongs in:

```python
OPENAI_TIMEOUT_SECONDS
```

## All Available Providers Are Unavailable

### Symptom

Solitude-Kaizen may return:

```text
All available AI providers are currently unavailable.
```

### Meaning

This is a user-facing final outcome.

It is not used internally as an error signal.

The router makes its decision using structured `ProviderError` fields before this sentence is returned.

### Important Rule

Do not add logic such as:

```python
if response == "All available AI providers are currently unavailable.":
```

Internal routing must continue to use structured state.

## Cloud Provider Fails but Ollama Works

This is expected fallback behavior.

Current fallback paths:

```text
Groq -> Ollama
OpenAI -> Ollama
```

If Ollama successfully answers after a cloud-provider failure:

```text
last_provider_used = ollama
```

The system should report Ollama as the provider that actually produced the response.

## Direct Ollama Failure

When:

```env
AI_PROVIDER=ollama
```

Ollama failures do not automatically switch to Groq or OpenAI.

This is intentional.

Current fallback is bounded and one-way.

Do not create provider loops such as:

```text
Groq -> Ollama -> OpenAI -> Groq
```

without an intentional architecture redesign.

## Wrong Provider Displayed

`last_provider_used` means:

```text
The provider that successfully generated the response
for the most recent request attempt.
```

Every request should begin with:

```python
last_provider_used = None
```

A provider must be recorded only after successful inference.

If provider information from an older request appears after a new failed request, inspect provider-tracking logic.

## Talk Failure Leaves Extra Conversation Message

A final provider failure should not leave the unanswered current user message in short-term history.

The CLI currently removes that temporary turn when a final `ProviderError` reaches the CLI boundary.

After one successful user-and-assistant exchange, conversation status should increase by:

```text
2 messages
```

not four.

If counts increase unexpectedly, inspect whether messages are being added in both `main.py` and conversation helpers.

## Current Message Appears Twice in Prompt

The correct order is:

```text
Build context from previous conversation
        |
        v
Add current user message to history
        |
        v
Send current user message separately to provider
```

`prepare_user_turn()` must build conversation context before appending the current user message.

Do not add the current message to recent context and also send it separately.

## Conversation History Too Large

Current stored short-term history limit:

```text
20 messages
```

Current prompt conversation-context limit:

```text
6 recent messages
```

These are separate concepts.

The application may retain more short-term messages than it sends as recent context.

## Conversation History Disappears After Restart

This is expected in V1.

Current short-term conversation history exists only in RAM.

It is not persisted between application launches.

Persistent conversation history is a future capability.

## Memory Is Missing After Restart

Long-term memories should persist.

If they do not:

1. Verify the memory file exists.
2. Verify the expected path.
3. Inspect the JSON structure.
4. Check whether the program saved after the memory operation.
5. Do not manually rewrite the entire file until the failure is understood.

Current memory path:

```text
src/solitude_kaizen/data/memories.json
```

## Legacy Memory Looks Different

Older memories may not contain all current fields.

`normalize_memory()` converts legacy values into the current schema.

Current schema:

```json
{
  "text": "...",
  "category": "personal",
  "importance": 3,
  "created_at": "unknown"
}
```

This allows old memory data to remain usable.

## Memory Selection Seems Unrelated

Current V1 context selection is based primarily on ranking:

```text
importance
then recency
```

It is not yet semantic retrieval.

Therefore, the top-ranked memories are not guaranteed to be the most semantically relevant to every user question.

This is a known V1 trade-off, not necessarily a bug.

## Tests Fail

Start with:

```powershell
python -m pytest -q
```

Then read the first failure carefully.

Do not make several unrelated changes at once.

Normal process:

```text
Read failure
    |
    v
Identify expected behavior
    |
    v
Inspect smallest relevant code path
    |
    v
Make one focused correction
    |
    v
Run tests again
```

## Test Count Unexpectedly Decreases

Python test functions must have unique names.

If two tests use the same function name, the later definition may replace the earlier one during module loading.

If the suite unexpectedly reports fewer tests:

1. Search for duplicate `def test_...` names.
2. Confirm the intended test was actually collected.
3. Do not assume a green suite means every written test executed.

Current expected baseline:

```text
61 passed
```

## A Test Passes but Does Not Prove the Behavior

A test can accidentally compare two values that happen to be equal without proving that one controls the other.

Example:

```python
OLLAMA_TIMEOUT_SECONDS = 120.0
```

and production code:

```python
timeout=120
```

A weak test may still pass because:

```text
120 == 120.0
```

A stronger configuration-wiring test temporarily changes the constant and verifies that the request follows the changed value.

General lesson:

> Test the relationship, not merely the current values.

## Python Command Not Found

Check:

```powershell
python --version
```

The current development environment is tested with:

```text
Python 3.14.7
```

If `python` is not recognized, diagnose PATH or installation before modifying project code.

## Dependency Problems

Check installed dependency consistency:

```powershell
python -m pip check
```

Install project dependencies from the pinned files:

```powershell
python -m pip install -r requirements-dev.txt
```

Do not casually upgrade every dependency while troubleshooting an unrelated failure.

Dependency changes should be deliberate and tested.

## `.env` Was Accidentally Staged

Check:

```powershell
git status
```

The real `.env` file should be ignored.

Verify:

```powershell
git check-ignore .env
```

Do not commit it.

If a real secret was already committed, simply deleting the local file is not enough because the secret may remain in Git history.

Treat committed credentials as exposed and rotate them.

## File Does Not Appear in `git status`

A file visible in VS Code may have been saved outside the repository.

Check from the repository root:

```powershell
Test-Path .\FILENAME.md
```

Example:

```powershell
Test-Path .\ARCHITECTURE.md
```

If it returns:

```text
False
```

the file is not at that location.

Search for it:

```powershell
Get-ChildItem C:\Dev -Recurse -Filter FILENAME.md -ErrorAction SilentlyContinue
```

Then move it into the intended project directory.

Do not stage a different file just because the expected file is missing.

## New Documentation File Saved to the Wrong Folder

The project root is:

```text
C:\Dev\Projects\LearniningProjects
```

A root documentation file should therefore look like:

```text
C:\Dev\Projects\LearniningProjects\ARCHITECTURE.md
```

not:

```text
C:\Dev\ARCHITECTURE.md
```

To avoid this, create new files directly from the project terminal:

```powershell
New-Item -ItemType File -Path .\DOCUMENT.md
code .\DOCUMENT.md
```

Then verify:

```powershell
Test-Path .\DOCUMENT.md
```

## Markdownlint MD047

### Symptom

VS Code reports:

```text
MD047/single-trailing-newline
Files should end with a single newline character
```

### Fix

Move to the end of the file:

```text
Ctrl + End
```

Press Enter once and save:

```text
Ctrl + S
```

Then verify the warning disappears.

## Git Shows README Changed but Text Looks Identical

Git may be detecting only the final newline.

Check:

```powershell
git diff -- README.md
```

A diff such as:

```text
\ No newline at end of file
```

followed by the same visible sentence normally means only the newline changed.

Inspect the diff before staging.

## Check Whitespace Before Committing

For a new Markdown file:

```powershell
git diff --check --no-index NUL DOCUMENT.md
```

For staged changes:

```powershell
git diff --cached --check
```

No output is normally the desired result.

## Safe Git Checkpoint Workflow

Before a commit:

```powershell
git status
git diff
```

Stage only intended files:

```powershell
git add <file>
```

Inspect staged changes:

```powershell
git diff --cached
```

Commit:

```powershell
git commit -m "Meaningful message"
```

Push:

```powershell
git push
```

Verify:

```powershell
git status
```

Target:

```text
nothing to commit, working tree clean
```

## When Not to Add a New Dependency

Do not solve every inconvenience by installing a package.

Before adding a dependency, ask:

```text
Does it reduce complexity?
Does it improve reliability?
Does it provide a genuinely required capability?
Can we test it?
Can we remove or replace it later?
```

If not, the dependency probably does not belong in V1.

## When to Stop Troubleshooting and Reassess

Stop making changes if:

- Each fix creates a new unrelated problem
- Several configuration values are being changed simultaneously
- The original failure is no longer understood
- Security controls are being disabled
- Large refactors are being proposed for a small bug
- New dependencies are being introduced without clear need

Return to the last known-good Git checkpoint and diagnose from there.

## Troubleshooting Philosophy

Solitude-Kaizen development follows these principles:

> Reliability before variety.
>
> Classification before retry.
>
> Fallback before failure.
>
> Independence before convenience.
>
> Simplicity before infrastructure.

Troubleshooting should preserve those principles.
