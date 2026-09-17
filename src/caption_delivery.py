"""Divide legendas longas sem descartar jogadores ou scouts."""


def split_caption(text: str, max_chars: int = 3500) -> list[str]:
    if max_chars < 1:
        raise ValueError("max_chars precisa ser positivo")
    parts, current = [], ""
    for line in text.splitlines(keepends=True):
        if current and len(current) + len(line) > max_chars:
            parts.append(current)
            current = ""
        while len(line) > max_chars:
            parts.append(line[:max_chars])
            line = line[max_chars:]
        current += line
    if current:
        parts.append(current)
    return parts or [""]
