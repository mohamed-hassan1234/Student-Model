# LoRA Guide

LoRA is the default real Phase 3 training method. The implemented command surface validates configuration and optional dependencies but does not download models. Operators must provide local approved model assets and run training explicitly.

Manual command surface:

```powershell
uv run devmind-training validate-base-model-manifest --manifest manifest.json
uv run devmind-training validate-dataset --dataset-version dsv_...
uv run devmind-training create-dataset-splits --dataset-version dsv_... --seed 7
uv run devmind-training start-lora-training --training-config config.json --acknowledge-manual
```

Generated adapters must be saved separately from base models and hashed before candidate registration.
