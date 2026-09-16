"""CJK-friendly tokenizer: ASCII → alnum tokens, CJK → unigram + bigram.

No external dependencies. Ported from notion-kb-agent. Splitting CJK into both
single chars (unigram) and adjacent pairs (bigram) improves match precision for
Chinese/Japanese/Korean text, which has no spaces between words.
"""

import re

_ASCII = re.compile(r"[a-z0-9]+")
_CJK_RUN = re.compile(r"[㐀-䶿一-鿿]+")


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    text = text.lower()
    tokens = _ASCII.findall(text)
    for run in _CJK_RUN.findall(text):
        tokens.extend(run)  # unigram
        for i in range(len(run) - 1):
            tokens.append(run[i : i + 2])  # bigram
    return tokens
