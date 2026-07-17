# Artifact Storage

Generated artifacts are ignored local files under `storage/generated/`, including adapters, checkpoints, metrics, logs, evaluation output, manifests, and configuration snapshots. MongoDB stores paths, hashes, sizes, and metadata, not large model weights.

Existing artifact directories are not overwritten silently. Safetensors is preferred for adapter artifacts. GridFS is reserved for small reports/manifests only when justified.
