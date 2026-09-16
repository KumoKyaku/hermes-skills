# Windows QQ Bot Gateway Session Transcript

This transcript captures a real diagnostic session: QQ Bot was set up successfully (gateway connected) but user messages were rejected. The env var fix (`GATEWAY_ALLOW_ALL_USERS=true`) was already in `.env` but the gateway didn't pick it up because it was set AFTER the process started.

## Timeline

| Time | Event |
|------|-------|
| 20:32 | First `hermes gateway restart` attempt → "No gateway was running" + "Gateway service is not installed" → interactive install prompt |
| 20:33 | Second `hermes gateway restart` → same result |
| 20:35 | Manual start via `hermes gateway run` → QQ Bot connects successfully |
| 20:37 | User sends "测试" → **"Unauthorized user: CA8F4A9F59F6F80DAAF5DE4F674EB2C5 (None) on qqbot"** |
| 20:38 | Attempt to install as service → blocked by UAC/Scheduled Task prompts |

## Key Observations

### Start sequence (gateway.log)
```
20:35:05  INFO  Starting Hermes Gateway...
20:35:05  WARNING  No user allowlists configured. All unauthorized users will be denied.
20:35:06  INFO  Connecting to qqbot...
20:35:06  INFO  Access token refreshed, expires in 6302s
20:35:06  INFO  Gateway URL: wss://api.sgroup.qq.com/websocket
20:35:06  INFO  WebSocket connected
20:35:06  INFO  Connected
20:35:06  INFO  Identify sent
20:35:06  INFO  ✓ qqbot connected
20:35:06  INFO  Gateway running with 1 platform(s)
20:35:06  INFO  Ready, session_id=27ec3ea3-76d5-4b0f-b665-018b3ed557b3
```

### Rejection (gateway.log)
```
20:37:02  WARNING  Unauthorized user: CA8F4A9F59F6F80DAAF5DE4F674EB2C5 (None) on qqbot
```

### .env state
`GATEWAY_ALLOW_ALL_USERS=true` was at line 368 of `.env` — but the gateway had already started without it.

### gateway-exit-diag.log
```
{"ts": "2026-06-20T12:35:03.708552+00:00", "tag": "gateway.start", "pid": 12816,
 "python": "3.11.15", "platform": "win32", "argv": [
   "C:\\Users\\Sun47\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts\\hermes",
   "gateway", "run"
 ]}
```

### gateway_state.json
```json
{
  "pid": 12816,
  "gateway_state": "running",
  "platforms": {
    "qqbot": {
      "state": "connected",
      "error_code": null,
      "error_message": null
    }
  }
}
```

### gateway-restart.log (shows both attempts)
```
=== gateway-restart started 2026-06-20 20:32:34 ===
✗ No gateway was running
✗ Gateway service is not installed
  Install it now so the gateway starts on login? [Y/n]:

=== gateway-restart started 2026-06-20 20:33:45 ===
✗ No gateway was running
✗ Gateway service is not installed
  Install it now so the gateway starts on login? [Y/n]:
```

## Resolution

The fix for the "Unauthorized user" error was:
1. Add `GATEWAY_ALLOW_ALL_USERS=true` to `.env` (already done, but after gateway start)
2. Stop the running gateway: `hermes gateway stop`
3. Start fresh: `hermes gateway run`
4. The .env is read at process start, so the new var takes effect

## Diagnostic Commands Used

```bash
# Gateway status
hermes gateway status

# Read gateway log
cat "$HERMES_HOME/logs/gateway.log"

# Read errors log
cat "$HERMES_HOME/logs/errors.log"

# Read restart log
cat "$HERMES_HOME/logs/gateway-restart.log"

# Read gateway state
cat "$HERMES_HOME/gateway_state.json"

# Check env vars
grep -n "^GATEWAY\|^QQBOT" "$HERMES_HOME/.env"

# Check windows paths
echo $HERMES_HOME
hermes config path
```
