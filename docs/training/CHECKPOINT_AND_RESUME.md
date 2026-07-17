# Checkpoint And Resume

Training runs record checkpoint path, hash, step, compatibility, and timestamp. Resume is never automatic. Operators must explicitly select a recorded compatible checkpoint and validate base-model, dataset, split, and configuration compatibility.

Unknown, corrupted, or mismatched checkpoints are rejected.
