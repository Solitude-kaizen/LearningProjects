# SK V2 Release Checklist

Status: internal V2 checkpoint; no public V2 release has been authorized.

Latest follow-on regression result: 563 passed (2026-09-08), including the
read-only Memory Lens (option 31) and unchanged existing selection behavior.
The preceding safeguard checks include safe
read-only search/category, restore-confirmation, reflection, and proposal-review
cancellation. Canceling any review prompt leaves the temporary database
unchanged and never calls the decision-recording function. Invalid numeric
proposal IDs are rejected without a conversion traceback.
Reflection cancellation preserves the temporary database unchanged and
does not complete the lesson or create a pending review.
Temporary live files and the existing backup remain unchanged when the
confirmation is canceled, including Ctrl+C or end-of-input; no emergency
backup or restoration starts. This does not cover interruption mid-restore.
Goal changes save before
updating live state and handle cancellation or write failure without losing
the prior goal. The historical results below remain evidence for their own
checkpoints. No public release or push was performed in this development run.

Working scope proposed on 2026-09-04. Following the review, the recommended
path is to continue from the internal checkpoint without requiring a
public tag. The creator would still need to approve any future public
release boundary and publication. This checklist does not authorize
publishing, installing tools, changing provider settings, or restoring
personal data.

## Release Boundary

V2 should deliver the existing companion foundations as a documented,
tested release. It does not need every future idea in the roadmap.

| Included capability | Evidence available |
| --- | --- |
| Conversation with swappable providers and bounded fallback | Provider regression tests and conversation workflow tests |
| Persistent memories with keyword-based context selection | Memory, relevance, and temporary-file persistence tests |
| Preview and confirmation for memory deletion and clearing chat | Confirm/cancel tests, including main-menu workflows |
| Blank or interrupted chat-input cancellation | No-provider-call tests and preserved follow-up context |
| Public AI research inbox with source links and type hints | Collector, storage, deduplication, and display tests |
| Optional Learning Guide and human-reviewed proposals | Startup independence, proposal decision, and review-history tests |
| Private local continuity bundles and guarded restore | Temporary-data verification, cancellation, emergency backup, and rollback tests |

Finish release checks and fix demonstrated blockers within this boundary.
Further CLI refactoring, extra providers, and new skills are not automatic
release requirements.

## Evidence Recorded on 2026-09-04

The application code checked was `874b235`; this readiness checkpoint adds
one first-run regression test without changing application code. These
observations describe this checkout and machine, not a clean dependency
installation or every provider.

- [x] Full automated suite: `python -m pytest -q` — 231 passed, including
  the new first-run regression.
- [x] Installed dependency consistency: `python -m pip check` — no broken requirements.
- [x] Ollama lists the required `qwen3:4b-instruct` model locally (2.5 GB).
- [x] Git ignores `.env`, the configured private JSON files, SQLite
  database, and continuity-backup directory.
- [x] The tracked SK data directory contains only the two example JSON
  files; their contents were checked as examples, not personal runtime data.
- [x] A content-pattern scan of the tracked working tree, configured to
  report filenames only, found no matches for selected common API-token/
  private-key formats. This is a limited check, not a complete secret
  scan or a fresh history audit.
- [x] Short live local-only chat check through SK's conversation/provider path:
  one synthetic request returned `READY`, reported `ollama`, and recorded
  two history messages. The request was limited to 32 generated tokens;
  the check rejected non-loopback requests and did not use saved memories.
  It took 63.1 seconds. This proves basic local inference, not speed,
  complex-task quality, a disconnected-network test, or full offline CLI coverage.
- [x] Fresh-directory first-run check using synthetic data, no API keys,
  and blocked socket connections: `tests/test_release_readiness.py`.
  Profile, empty memories, provider/status, empty research, missing-backup
  display, and exit all worked. This uses installed dependencies and does
  not claim a fresh installation, real chat, or live restore was tested.

Follow-up: a three-turn fictional local conversation also completed
successfully. See [LOCAL_CHAT_EVALUATION.md](LOCAL_CHAT_EVALUATION.md) for
exact prompts, responses, timings, and limits of that evidence. This does
not replace the creator's day-to-day usability judgment below.

## Optional Future Public Release Gates

Follow-on session-continuity work (after the recorded 231-test checkpoint)
adds a separately stored, reviewed note through menu 28 and explicit resume,
edit, dismissal, and forgetting through menu 29. Full regression suite:
345 passed. Checks used temporary data and fake inference, including restart
privacy, cancellation, failed atomic writes, and new/legacy backup restoration.
No personal backup was restored and no live model call was made. This is a
further internal change, not authorization for a public release.

A later [bounded local session-note check](SESSION_NOTE_EVALUATION.md)
completed three fictional requests through the existing Ollama adapter.
It covered absent context, resumed context, and a changed plan, without
personal data or cloud calls. This does not expand the automated-test
claim into a general live-model quality guarantee.

These remain necessary if a public V2 release is chosen. They do not
prevent using the internal checkpoint or making further reviewed changes.

- [ ] Final documentation/version consistency and release-note review.
- [ ] Final staged-file privacy review at the actual release commit.
- [ ] Creator approves the V2 scope and known limitations below.
- [ ] Creator authorizes publication; reviewed commits are pushed, the
  release version is set consistently, and `v2.0.0` is created and verified
  on the intended remote. No V2 tag was created by this checklist.

Fallback, provider errors, and public-source behavior are covered by
automated fakes. This audit has not made fresh cloud-provider calls or
live research requests. Do not label those integrations newly live-tested.

At the start of the initial readiness check, Git's tracking comparison showed two
commits ahead of `origin/main`; the only local release tag was `v1.0.0`.
The remote was not queried. Untracked `src/output/` belongs to the user
and remains untouched and excluded from this work.

## Personal Continuity Checks

Further reliability checkpoint: 478 tests passed after adding preview and
confirmation to new-memory creation. Cancellation and injected save failures
preserve existing temporary test data. No public release or personal backup
operation was performed.

Follow-on reliability check: 457 tests passed after atomic JSON saving,
failure-safe memory deletion, and clean main-menu/deletion interruptions.
Failure injection used temporary files. No personal recovery operation was
performed, and atomic saving does not replace continuity backups.

These protect the creator's setup; automated tests cannot establish that
the creator has a usable personal backup.

- [x] Creator reported menu 24 completed successfully with four verified
  files, followed by menu 25 reporting `Status: valid`. This is the
  creator's reported local verification, not an independent inspection
  of the archive. The earlier missing-folder observation preceded this
  report and is no longer a reason to request the same backup step again.
- [ ] Keep a private copy outside the laptop if a suitable destination is
  available. Never publish the bundle or commit it to GitHub.
- [x] Record process-only local-session instructions in the README. The
  synthetic local chat check left the saved provider preference unchanged.
- [ ] Creator tries the documented local session and confirms its response
  time is acceptable for their day-to-day use.

Do not use menu 26 as a casual test on personal files. Restore behavior
is tested with temporary data. Live restoration needs a real recovery
need, a preview, and the exact confirmation.

## Known Limitations to Accept or Fix Before Release

- Chat history is session-only, with six recent messages used as context
  and at most twenty stored in memory. An optional reviewed session note
  persists separately and enters chat only after explicit resume; it is not
  a persistent transcript or an AI-generated summary. Forgetting/dismissal
  does not erase earlier chat details or older backup copies.
- Memory retrieval uses keywords, not semantic understanding. Replies can
  be wrong, and relevant context can be missed.
- Cloud chat sends the selected memory and recent conversation context to
  the selected provider. Local storage does not make cloud chat private.
- Research collects public AI-related metadata, not full-source verification
  or a general HR/business research service. Source labels do not establish truth.
- Local chat does not fetch current information from the internet. Automatic
  research remains opt-in; manual collection still needs network access.
- The Learning Guide uses templates; neither it nor proposal approval
  trains a model or implements changes automatically.
- Continuity ZIP files are unencrypted and contain personal data. They
  exclude `.env`, source code, dependencies, and local model downloads.
  They do not scrub secrets accidentally saved inside memories or other
  included files; never store credentials there.
- Guarded restore currently requires valid live files to protect first;
  recovering an already missing/corrupted live state needs separate guidance.
- Chat-input cancellation does not cancel a provider request already running.
  Other prompts do not yet uniformly handle keyboard interruption/EOF.
- SK does not load Codex skills, run subagents, or provide model-controlled
  general tool execution. Prompt instructions are not a security sandbox.

## Requested Next Direction: HR, Business, and Research

Follow-on: menu 30 now provides a single supplied-source review with explicit
request confirmation, no personal context or persistence, and exact-quotation
validation. The full suite passed 431 tests. A bounded local-model trial is
documented in `SOURCE_REVIEW_EVALUATION.md`; this does not establish fact
verification or a general HR/business research service. Multi-source comparison
remains future work. No public release is authorized by this addition.

The creator has named these areas of interest. Proposed sequencing is to
complete this release boundary first, then scope one optional workflow
at a time. These are not installed capabilities or mandatory V2 gates.

- Research: begin with read-only source comparison; show citations,
  uncertainty, and missing evidence. Do not invent verified claims.
- HR: support concept explanations and fictional practice cases; exclude
  real employee data from examples and leave consequential decisions to people.
- Business: support plans and case analysis with assumptions separated
  from evidence; use reviewed sources for time-sensitive claims.

Start with one companion and selectable workflows. A multi-agent runtime,
new paid service, or always-running background process needs its own
benefit, resource, permission, and test review.
