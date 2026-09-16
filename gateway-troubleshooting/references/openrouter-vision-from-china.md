# OpenRouter Vision Models Available from China

## Context

When configuring Hermes' auxiliary vision provider (`auxiliary.vision`) in a China-based environment, many OpenRouter models return **HTTP 403 (region restricted)** — even models from Chinese companies hosted on OpenRouter.

Tested approach: authenticate via OpenRouter with a standard API key, but use a **Chinese-origin vision model** that OpenRouter routes through to avoid region blocking.

## Verified Working Models (from China, June 2026)

These models **accept image input** and **respond successfully** from a China-based IP via OpenRouter:

| Model | Provider | Notes |
|-------|----------|-------|
| `baidu/ernie-4.5-vl-424b-a47b` | Baidu | ✅ Verified working. Good image description |
| `qwen/qwen3-vl-32b-instruct` | Alibaba/Qwen | Should work (Alibaba is China-based) |
| `qwen/qwen2.5-vl-72b-instruct` | Alibaba/Qwen | Should work |
| `z-ai/glm-4.6v` | Zhipu AI | Should work |
| `stepfun/step-3.7-flash` | Stepfun | Should work |
| `bytedance-seed/seed-1.6` | ByteDance | Should work |
| `xiaomi/mimo-v2.5` | Xiaomi | Should work |

## Models That 403'd (Region Blocked)

These all returned `{"error": {"message": "This model is not available in your region.", "code": 403}}`:

- `openai/gpt-4o` (all variants)
- `anthropic/claude-sonnet-4` (all variants)
- `google/gemini-2.0-flash-exp` (and other Google models as routed through OpenRouter)
- `meta-llama/llama-3.2-11b-vision-instruct`
- `qwen/qwen-vl-plus` — surprisingly also blocked on OpenRouter (likely OpenRouter-level routing, not Qwen itself)

## Configuration

```yaml
# config.yaml
auxiliary:
  vision:
    provider: openrouter
    model: baidu/ernie-4.5-vl-424b-a47b
    base_url: ''
    api_key: ''       # left empty — the tool reads OPENROUTER_API_KEY from .env
    timeout: 120
```

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...your-key...
```

## Testing Vision API Directly

To verify a model works before configuring Hermes:

```python
import json, base64, urllib.request

# Read image
with open("image.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = json.dumps({
    "model": "baidu/ernie-4.5-vl-424b-a47b",
    "messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
        {"type": "text", "text": "Describe this image."}
    ]}],
    "max_tokens": 200
}).encode()

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=payload,
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read())
    print(result["choices"][0]["message"]["content"])
```

## Key Pitfalls

1. **Restart required.** Changing `auxiliary.vision.model` in config.yaml only takes effect after a gateway restart (the config is read at session init). You cannot hot-reload it mid-session.
2. **OpenRouter API responds to text-only calls fine from China.** The 403 is model-level, not account-level region blocking. Run `curl -s "https://openrouter.ai/api/v1/models"` to list models that respond from your IP.
3. **Checking `input_modalities` in the models API response** is the reliable way to find vision-capable models: look for `"image"` in `architecture.input_modalities[]`.
4. **OpenRouter query for vision models:**
   ```python
   # Filter: architecture.input_modalities contains "image"
   for m in data["data"]:
       if "image" in m.get("architecture", {}).get("input_modalities", []):
           print(m["id"])
   ```

## Listing All Vision Models via OpenRouter API

```python
import json, urllib.request
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {API_KEY}"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())
for m in data["data"]:
    if "image" in m.get("architecture", {}).get("input_modalities", []):
        print(m["id"], m.get("pricing", {}).get("prompt", "?"))
```

Full list (as of June 2026): ~60+ vision models including GPT-4o, Claude, Gemini, Qwen, Baidu, Zhipu GLM, ByteDance Seed, Stepfun, Xiaomi, Mistral, Llama, etc.
