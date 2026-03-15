def normalize_prompt(raw_prompt: str) -> str:
    return " ".join((raw_prompt or "").strip().split())
