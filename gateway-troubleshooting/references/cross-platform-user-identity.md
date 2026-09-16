# Cross-Platform User Identity

How to make Hermes know you're the same person across different messaging platforms (QQ Bot, Feishu, Telegram, Discord, etc.).

## The Problem

By default, each platform adapter has its own user identity namespace:

```
Gateway
├── feishu:oc_xxx          ← session for Feishu user
└── qqbot:CA8F4A9F...      ← session for QQ user (treated as different person)
```

Hermes does **not** have a built-in "this Feishu user = this QQ user" configuration for the default memory provider. Sessions are per-platform. Each platform's `user_id` is independent.

## How to Find Your Platform User IDs

The gateway stores platform user IDs in several places under `$HERMES_HOME`:

| File | What it contains |
|------|-----------------|
| `channel_directory.json` | All known chat channels per platform, with `id` = user/group ID |
| `pairing/{platform}-approved.json` | Approved (paired) users per platform with raw user IDs |
| `pairing/_rate_limits.json` | Rate-limit tracking keys in `platform:user_id` format |

**Quick check:**
```bash
cat "$HERMES_HOME/channel_directory.json" | python -m json.tool
cat "$HERMES_HOME/pairing/"*-approved.json
```

**Typical ID formats observed on Chinese platforms:**
- **QQ Bot**: 32-char uppercase hex hash (e.g. `CA8F4A9F59F6F80DAAF5DE4F674EB2C5`)
- **Feishu**: starts with `oc_` (e.g. `oc_24926d13d00822cf91659c5f72ab5ed6`)
- **Telegram**: numeric string (e.g. `123456789`)

**Note:** The gateway passes the **raw** platform user ID (not the `platform:user_id` prefixed form) as `user_id` to memory providers. The `channel_directory.json` stores the raw ID. The pairing system uses the `platform:user_id` format internally for rate-limit tracking keys.

## Solution A — Built-in Memory (No Config Needed)

The built-in memory provider stores **user profile** and **memory** data globally — across all platforms. When the agent saves a fact with the `memory` tool, it is accessible from any platform's session.

**Workflow:**

1. On Platform A (e.g. QQ Bot), the user says: "我是云却，QQ 479813005"
2. The agent saves this via the `memory` tool → user profile "姓名: 云却, QQ: 479813005"
3. On Platform B (e.g. Feishu), the agent loads the same memory → already knows who the user is
4. The agent explicitly says: "你是云却对吧？我记得你 QQ 是 479813005"

**Limitations:**
- The agent **can** read memories across platforms but doesn't automatically know "this new platform user = the same person". The user must either:
  - Tell the agent on the new platform (e.g. "我是云却")
  - Or the agent proactively asks: "我看到你有 QQ 账号关联，请问你是同一个人吗？"

**Pitfall:** The `memory` and user-profile stores are per-profile (`~/.hermes/`). If you run multiple Hermes profiles, memories do NOT cross profiles.

## Solution B — Honcho Memory Provider (Explicit Identity Mapping)

The optional Honcho memory plugin supports `userPeerAliases` — a map from platform-specific runtime user IDs to a stable Honcho peer identity.

### Setup

Create `~/.hermes/honcho.json`:

```json
{
  "userPeerAliases": {
    "CA8F4A9F59F6F80DAAF5DE4F674EB2C5": "yun_que",
    "oc_24926d13d00822cf91659c5f72ab5ed6": "yun_que"
  },
  "peerName": "yun_que",
  "pinPeerName": true
}
```

**Key format:** The `userPeerAliases` keys are the **raw** user IDs passed by the gateway — NOT the `platform:user_id` form. For QQ the key is the hex hash (e.g. `CA8F4A9F59F6F80DAAF5DE4F674EB2C5`), for Feishu it's the `oc_` string. Do NOT prefix with platform name.

Then configure the memory provider:

```bash
hermes memory setup
```

**Prerequisite:** Honcho requires its own backend server — the `honcho` package on PyPI is a process-manager (Foreman clone), **not** the Honcho memory backend. You need a running Honcho API server and `HONCHO_API_KEY` configured in `~/.hermes/.env` or `honcho.json`.

Then configure the memory provider:

```bash
hermes memory setup
```

### How it works

```
HonchoClientConfig._resolve_user_peer_id():
  1. Check runtime user_ids (e.g. ["CA8F4A9F59F6F80DAAF5DE4F674EB2C5"])
  2. Look up userPeerAliases map → finds "yun_que"
  3. Both platforms resolve to the SAME Honcho peer "yun_que"
  4. Memory, sessions, and context are FULLY shared
```

The mapping is defined in `honcho.json` under `userPeerAliases`. Each key is a **raw** gateway runtime user ID — NOT prefixed with platform name. The raw ID format is platform-specific (QQ = hex hash, Feishu = `oc_` string, Telegram = numeric). Find your IDs in `channel_directory.json` or `pairing/` files.

The `_runtime_user_ids()` method in `HonchoSessionManager` returns the `user_id` and `user_id_alt` kwargs as passed by the gateway. Sources:
- `plugins/memory/honcho/__init__.py` line 427-428: reads from `kwargs.get("user_id")` and `kwargs.get("user_id_alt")`
- `gateway/run.py` passes these from the platform adapter when creating agent sessions

### Additional Knobs

- **`runtimePeerPrefix`** — For unknown (unmapped) users, prefix their runtime ID with a string (e.g. `"telegram_"`) instead of using the raw ID.
- **`pinPeerName`** — When true, pin all sessions to `peerName` regardless of runtime identity. Useful when only one user interacts with the Hermes instance.

### Per-Profile Isolation

Host-level (`honcho.json`) config replaces the root map as a whole so profiles can intentionally own their identity mappings. Profile-level `honcho.json` under `~/.hermes/profiles/<name>/honcho.json` takes precedence over the root one.

## Solution C — Agent-Mediated Linking (For Any Memory Provider)

The most flexible approach: the agent itself bridges the identity gap.

1. User sends message from Feishu
2. Agent sees: `platform=feishu, user_id=ou_abc123`
3. Agent checks memory: "是谁的 Feishu 账号是 ou_abc123？"
4. If not found, agent says: "你好！请问你是云却吗？(QQ 479813005 那位)"
5. User confirms → agent saves `feishu:ou_abc123 = 云却` to memory
6. Future Feishu sessions: agent immediately knows who the user is

This works with **any** memory provider (built-in, Honcho, Mem0, etc.) because the identity link is stored as a simple memory fact.

### Practical workflow (what the agent does)

When a user asks about cross-platform identity linking, the agent should:

1. **Find user IDs:** Read `$HERMES_HOME/channel_directory.json` to get the per-platform user IDs
2. **Save to both memory stores:**
   - `memory(target='user')` — so future sessions see the user profile
   - `memory(target='memory')` — so the agent's operational notes include the mapping
3. **Confirm to the user** that the link is established
4. **Proactively bridge:** When a message arrives from an unknown platform user ID, check memory for a matching identity record and ask the user to confirm they're the same person

**Pitfall:** The user needs to tell the agent on each new platform who they are — the agent knows the mapping but doesn't auto-login from memory alone. If the user connects from a third platform, the agent should say: "我看到你有 QQ (xxx) 和飞书 (xxx) 的记录，请问你是同一个人吗？"

## Key Difference: Session vs Identity

| Concept | What it means |
|---------|-------------|
| **Session** | Per-conversation message history. Each platform = separate session. |
| **User identity** | "Who is this person". Cross-platform by default for memory, but the agent needs a hint to connect the dots. |

Even without explicit identity mapping, a user's memory facts are visible across platforms — the agent just doesn't automatically know "Feishu user ABC = QQ user 479813005" without being told.
