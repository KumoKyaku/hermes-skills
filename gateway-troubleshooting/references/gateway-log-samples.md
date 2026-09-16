# Gateway Log Pattern Matching

Quick reference for recognizing common gateway issues from log output.

## Authorization

### "Unauthorized user" (allowlist issue)
```
WARNING gateway.run: Unauthorized user: <HASH> (None) on qqbot
```
or at startup:
```
WARNING gateway.run: No user allowlists configured. All unauthorized users will be denied.
```
**Fix:** Set `GATEWAY_ALLOW_ALL_USERS=true` or per-platform `<_PLATFORM_>_ALLOWED_USERS` in `.env`, then stop + restart gateway.

## Connection

### QQ Bot connecting successfully
```
INFO  Connecting to qqbot...
INFO  [QQBot:<app_id>] Access token refreshed
INFO  [QQBot:<app_id>] Gateway URL: wss://api.sgroup.qq.com/websocket
INFO  [QQBot:<app_id>] WebSocket connected
INFO  [QQBot:<app_id>] Connected
INFO  [QQBot:<app_id>] Identify sent
INFO  ✓ qqbot connected
INFO  [QQBot:<app_id>] Ready, session_id=<uuid>
```

### QQ Bot auth failure (bad credentials)
```
ERROR [QQBot:<app_id>] Access token refresh failed: ...
```
**Fix:** Check `QQBOT_APP_ID` and `QQBOT_CLIENT_SECRET` or `QQBOT_BOT_TOKEN` in `.env`.

## Restart / Service

### Restart when no service installed
```
=== gateway-restart started <timestamp> ===
✗ No gateway was running
✗ Gateway service is not installed
  Install it now so the gateway starts on login? [Y/n]:
```
**Fix:** Start manually: `hermes gateway stop && hermes gateway run`

## Env

### Env var not taking effect
The gateway logs the env var ability at startup. If `GATEWAY_ALLOW_ALL_USERS=true` is in `.env` but the startup log still says:
```
WARNING gateway.run: No user allowlists configured
```
→ the gateway was started before the var was added. Stop + restart.

## Config

### Empty config sections
```
WARNING [session_id] config.yaml has empty section(s): `key1`, `key2`.
Remove the line(s) or set them to `{}`
```
**Fix:** Either delete the empty key lines from `config.yaml` or set them to `{}`.

## Process health

### Gateway state (gateway_state.json)
```json
{
  "pid": 12816,
  "gateway_state": "running",
  "platforms": { "qqbot": { "state": "connected" } }
}
```
**Healthy:** `"gateway_state": "running"`, each platform `"state": "connected"`.
**Unhealthy:** `"gateway_state": "stopped"` or platform with `"error_code"` set.
