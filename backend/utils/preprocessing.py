import re


EMOJI_REPLACEMENTS = {
    "\U0001f60a": " good ",
    "\U0001f602": " good ",
    "\U0001f60d": " good ",
    "\u2764\ufe0f": " good ",
    "\U0001f44d": " good ",
    "\U0001f621": " bad ",
    "\U0001f622": " bad ",
    "\U0001f620": " bad ",
    "\U0001f44e": " bad ",
    "\U0001f494": " bad ",
}


def replace_emojis(text: str) -> str:
    text = str(text)
    for emoji, word in EMOJI_REPLACEMENTS.items():
        text = text.replace(emoji, word)
    return text


def clean_text(text: str) -> str:
    text = replace_emojis(str(text))
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#[\w-]+", " ", text)
    text = re.sub(r"[^a-z\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text(text: str) -> str:
    return clean_text(text)
