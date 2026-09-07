# SK Context Previews

Verified with synthetic data on 2026-09-08. These are optional controls,
not new requirements for ordinary chat.

## Which option should I use?

| Option | Purpose | Sends a request? |
| --- | --- | --- |
| 12 | Ordinary companion chat | Yes, after a nonblank message |
| 31 | Understand which memories would be selected | No |
| 32 | Review application context before chatting | Only after `yes` |

## Memory Lens: option 31

Enter the question you are considering. SK shows the selected memories,
shared keywords, and selection count. It uses the same selector as chat:
distinct shared words first, importance and recency to break ties, at most
five memories. With no matches it falls back to importance and recency;
the screen explicitly warns that these memories may be unrelated.

It neither answers the question nor adds a conversation turn. Blank input,
`/cancel`, Ctrl+C, or end-of-input cancels. The question limit is 2000
characters. A later chat computes selection again from its current state.

## Review before sending: option 32

Enter a message. Inspect the application system prompt and message shown
on screen. The prompt can include up to five selected memories, six recent
messages, and an explicitly resumed session note. Merely having a saved
note does not activate it.

Type `yes` to send, or anything else to cancel. Ctrl+C or end-of-input at
confirmation also cancels. Cancellation makes no inference call and does
not add a turn or alter saved files. Successful replies join the current
session just like ordinary chat. This does not save a full transcript.

Hidden control characters and backslashes are displayed as escapes to
make them visible. The original application text is sent, not the escaped
display representation. Provider formatting and existing fallback still
apply. This is not a complete network-payload inspection or secret scanner.

If the context is not what you want, cancel first. Use the existing memory
controls, option 29 to dismiss a resumed note, or option 14 to clear session
context as appropriate. Each control retains its own confirmation rules.
Clearing or dismissing cannot erase anything already sent to a provider.

## Observed offline walkthrough

Two fictional memories were supplied directly to the local functions:
`Practice HR interviews` (importance 2) and `Prefer evening walks`
(importance 5). For `Help with HR interviews`, Memory Lens selected only
the interview memory and reported the shared words `hr, interviews`.

The same question was passed to reviewed chat with a fake provider
configuration. Answering `no` produced `cancelled`, zero response-function
calls, and an empty conversation history. No personal files or real model
were involved. This verifies the interaction, not HR advice quality.

## Boundaries

- Local preview means no inference request; displayed personal text can
  still be seen by someone looking at your screen or terminal history.
- Cloud chat can transmit the previewed context and may incur provider costs.
- A match explains retrieval, not factual truth or a model's reasoning.
- Interrupting an in-flight request cannot undo transmission or guarantee
  remote cancellation. SK removes the unanswered local turn.
- Existing memories and backups are not rewritten by either preview.

Full regression suite at this checkpoint: 611 passing tests. Additional
coverage-percentage tooling was not installed; no coverage percentage is claimed.
