# Hardware Guide

Use `uv run devmind-training inspect-hardware` while the API is running, or call `POST /api/v1/technology/training/hardware/inspect` with the local admin placeholder header.

The report records OS, Python version, CPU, RAM, GPU/CUDA availability, GPU memory, disk space, supported precision, recommended training mode, and limitations. CPU-only machines are reported as suitable for smoke tests only unless explicitly capable.
