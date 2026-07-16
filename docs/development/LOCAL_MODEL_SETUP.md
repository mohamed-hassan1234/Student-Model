# Local Model Setup

The default Phase 1 test provider is `mock`. To use a local provider, configure:

```text
LOCAL_MODEL_PROVIDER=ollama
LOCAL_MODEL_BASE_URL=http://127.0.0.1:11434
LOCAL_MODEL_NAME=<local-model-name>
MODEL_PROVIDER_TIMEOUT_SECONDS=20
```

Models are not downloaded automatically. Install and review local models manually.
