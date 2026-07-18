# Role Permission Matrix

| Role | Primary Permissions |
| --- | --- |
| `super_admin` | All permissions. |
| `ai_engineer` | Source review, training configuration/start/cancel/resume, evaluation start/read, candidate creation/review. |
| `data_reviewer` | Source review, dataset review/approval/export, evaluation read. |
| `security_reviewer` | Candidate security approval, candidate review, evaluation read, audit read. |
| `model_approver` | Candidate stage approval, candidate review, evaluation read. |
| `operator` | Training start/cancel/resume, manual staging execution/rollback, evaluation read. |
| `viewer` | Role and evaluation read-only visibility. |

Permissions are enforced in FastAPI dependencies and are not inferred from frontend state.
Emergency override uses `emergency.revoke`, which is available only through `super_admin` in the Phase 4 default matrix.
