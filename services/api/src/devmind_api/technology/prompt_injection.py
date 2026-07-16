import re

from devmind_api.technology.models import PromptInjectionFlags

SIGNALS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("instruction_override", re.compile(r"ignore (all )?(previous|system) instructions", re.I)),
    ("secret_request", re.compile(r"(reveal|print|exfiltrate).*(secret|token|password|key)", re.I)),
    ("policy_change", re.compile(r"(change|disable|override).*(policy|safety|rules)", re.I)),
    ("tool_request", re.compile(r"(run|execute).*(shell|command|tool)", re.I)),
)


def mark_prompt_injection(text: str) -> PromptInjectionFlags:
    matches = [name for name, pattern in SIGNALS if pattern.search(text)]
    return PromptInjectionFlags(
        has_instruction_override="instruction_override" in matches,
        asks_for_secrets="secret_request" in matches,
        asks_for_policy_change="policy_change" in matches,
        risk_score=min(1.0, len(matches) / 3),
        signals=matches,
    )
