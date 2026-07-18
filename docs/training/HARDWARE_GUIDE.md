# Hardware Guide

Use `uv run devmind-training --access-token <token> inspect-hardware` while the API is running, or call `POST /api/v1/technology/training/hardware/inspect` with a bearer token that has `training.configure`.

The report records OS, Python version, CPU, RAM, GPU/CUDA availability, GPU memory, disk space, supported precision, recommended training mode, and limitations. CPU-only machines are reported as suitable for smoke tests only unless explicitly capable.
