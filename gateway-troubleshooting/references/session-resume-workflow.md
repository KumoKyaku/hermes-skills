# Session Resume Workflow (QQ Bot → Desktop CLI)

Real example from a QQ Bot session resumed on a Windows desktop CLI.

## The Problem

User chatting via QQ Bot DM asks: *"QQ 会话为什么没有同步到 PC？"*
(Why isn't the current QQ Bot session showing on my PC's Hermes GUI?)

## Architecture

```
Gateway (Windows PC, background service)
├── qqbot:dm:USER_ID  ← session active, user chatting via QQ
└── local (CLI)       ← no active session, user hasn't opened desktop
```

Sessions are **platform-scoped**. The `qqbot:dm:...` session is invisible to a `local` CLI session.

## Step-by-Step Resume

### 1. Check what sessions exist

```bash
hermes sessions list
```

Output:
```
Preview                                            Last Active   Src    ID
───────────────────────────────────────────────────────────────────────────────────────────────
我想让当前qqbot的会话记录在pc 的gui也能同步看到                      1m ago        unknown 20260620_204135_bf20d558
```

### 2. Export as JSONL (for viewing)

```bash
hermes sessions export --session-id 20260620_204135_bf20d558 ~/qq-chat-history.jsonl
# → "Exported 1 session to C:/Users/Sun47/qq-chat-history.jsonl"
```

### 3. Resume from desktop CLI

```bash
hermes --resume 20260620_204135_bf20d558
```

This loads the full QQ Bot conversation context into a new desktop CLI session. The user continues the same topic on PC.

## What Doesn't Work

- ❌ `hermes` alone — starts a fresh local session, no history
- ❌ `hermes --continue` — resumes the most recent *local* session (not gateway sessions)
- ❌ Opening the desktop GUI — also starts a fresh local session
- No built-in "mirror session across platforms" feature exists

## Key Takeaway

`hermes --resume <session_id>` is the bridge between gateway platforms and the desktop CLI. Use it when a user wants to move their conversation from QQ/Telegram/Discord to the local terminal.
