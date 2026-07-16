# Local MongoDB Setup

Install MongoDB Community Server manually. Configure:

```text
MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DATABASE=devmind_local
```

After confirming the target database, run:

```powershell
uv run python scripts/bootstrap_mongodb.py
```
