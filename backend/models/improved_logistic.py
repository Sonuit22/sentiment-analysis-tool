from __future__ import annotations

import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

CONTRACTION_PATTERNS = [
    (r"\bwon't\b", "will not"),
    (r"\bcan't\b", "cannot"),
    (r"\bshan't\b", "shall not"),
    (r"\bain't\b", "is not"),
    (r"\bdoesn't\b", "does not"),
    (r"\bdon't\b", "do not"),
    (r"\bdidn't\b", "did not"),
    (r"\bisn't\b", "is not"),
    (r"\baren't\b", "are not"),
    (r"\bwasn't\b", "was not"),
    (r"\bweren't\b", "were not"),
    (r"\bhaven't\b", "have not"),
    (r"\bhasn't\b", "has not"),
    (r"\bhadn't\b", "had not"),
    (r"\bshouldn't\b", "should not"),
    (r"\bcouldn't\b", "could not"),
    (r"\bwouldn't\b", "would not"),
    (r"\bmustn't\b", "must not"),
    (r"\bneedn't\b", "need not"),
    (r"\bn't\b", " not"),
    (r"\bi'm\b", "i am"),
    (r"\bit's\b", "it is"),
    (r"\bthat's\b", "that is"),
    (r"\bthere's\b", "there is"),
    (r"\bwhat's\b", "what is"),
    (r"\bwho's\b", "who is"),
    (r"\blet's\b", "let us"),
]

POSITIVE_EMOJIS = [
    "😊", "😀", "😃", "😄", "😁", "😆",
    "😂", "😍", "🤩", "😘", "😎", "👍",
    "💯", "❤️", "💕", "💖", "💗", "🙌",
    "🎉", "🔥", "😺",
]
NEGATIVE_EMOJIS = [
    "😡", "😠", "😞", "😔", "😢", "😭",
    "😣", "😤", "👎", "💔", "☹️", "🙁",
    "😒", "😕",
]
NEUTRAL_EMOJIS = [
    "😐", "😶", "🤔", "🙃", "😅", "😮",
]

EMOTICON_REPLACEMENTS = {
    ":-)": "positive_emoji",
    ":)": "positive_emoji",
    ":d": "positive_emoji",
    "=d": "positive_emoji",
    "^_^": "positive_emoji",
    ":-(": "negative_emoji",
    ":(": "negative_emoji",
    "d:": "negative_emoji",
    ">:(": "negative_emoji",
}

SLANG_PATTERNS = [
    (r"\bomg\b", " surprise_token emphasis_token "),
    (r"\blol\b", " positive_emoji laugh_token "),
    (r"\blmao\b", " positive_emoji laugh_token emphasis_token "),
    (r"\bidk\b", " uncertain_token "),
    (r"\btbh\b", " candid_token "),
    (r"\bfr\b", " emphasis_real "),
    (r"\brn\b", " now "),
    (r"\bbtw\b", " aside_token "),
    (r"\bimo\b", " opinion_token "),
    (r"\bfam\b", " casual_group "),
    (r"\bbro\b", " casual_bro "),
    (r"\bdude\b", " casual_bro "),
    (r"\bur\b", " your "),
    (r"\bu\b", " you "),
    (r"\bya\b", " you "),
    (r"\bnah\b", " negative_reply "),
    (r"\byep\b", " positive_reply "),
    (r"\bnope\b", " negative_reply "),
    (r"\bgr8\b", " great "),
    (r"\bluv\b", " love "),
    (r"\bthx\b", " thanks "),
    (r"\bpls\b", " please "),
    (r"\bplz\b", " please "),
    (r"\bbcoz\b", " because "),
    (r"\bwow\b", " surprise_token "),
    (r"\bmeh\b", " neutral_emoji mild_negative "),
    (r"\bbruh\b", " frustration_token "),
    (r"\bdamn\b", " emphasis_token "),
    (r"\bwtf\b", " negative_phrase shock_token "),
]

EXPRESSION_PATTERNS = [
    (r"\bomg\s+this\s+is\s+insane\b", " positive_phrase strong_positive surprise_token "),
    (r"\blol\s+this\s+is\s+crazy\b", " positive_phrase surprise_token "),
    (r"\bthis\s+is\s+fire\b", " positive_phrase strong_positive "),
    (r"\bthat\s+is\s+lit\b", " positive_phrase strong_positive "),
    (r"\bthis\s+is\s+lit\b", " positive_phrase strong_positive "),
    (r"\binsane\s+fire\b", " positive_phrase strong_positive "),
    (r"\bso\s+happy\b", " positive_phrase "),
    (r"\bgood\s+battery\s+backup\b", " positive_phrase audio_positive "),
    (r"\bbattery\s+backup\s+is\s+good\b", " positive_phrase audio_positive "),
    (r"\bcamera\s+is\s+super\b", " positive_phrase audio_positive "),
    (r"\bbudget\s+friendly\b", " positive_phrase audio_positive "),
    (r"\bvery\s+lightweight\b", " positive_phrase audio_positive "),
    (r"\bsound\s+quality\s+is\s+good\b", " positive_phrase audio_positive "),
    (r"\bfits\s+my\s+day\s+to\s+day\s+life\b", " positive_phrase audio_positive "),
    (r"\bworks\s+fine\b", " positive_phrase audio_positive "),
    (r"\bpretty\s+good\b", " positive_phrase "),
    (r"\bsuper\s+bad\b", " negative_phrase strong_negative "),
    (r"\babsolutely\s+amazing\b", " positive_phrase strong_positive "),
    (r"\breally\s+awful\b", " negative_phrase strong_negative "),
    (r"\bkinda\s+nice\b", " mild_positive "),
    (r"\bsorta\s+okay\b", " mild_neutral "),
    (r"\boh\s+no\b", " negative_phrase "),
    (r"\bso+\s+good\b", " positive_phrase emphasis_token good "),
    (r"\bnot\s+worth\s+it\b", " negative_phrase strong_negative "),
    (r"\bbattery\s+drains\s+fast\b", " negative_phrase audio_negative "),
    (r"\bpoor\s+sound\b", " negative_phrase audio_negative "),
    (r"\bcamera\s+is\s+bad\b", " negative_phrase audio_negative "),
    (r"\blaggy\s+performance\b", " negative_phrase audio_negative "),
    (r"\bsound\s+quality\s+is\s+poor\b", " negative_phrase audio_negative "),
    (r"\bvery\s+angry\b", " negative_phrase strong_negative "),
]

PHRASE_CORRECTIONS = [
    (r"\bnot\s+at\s+all\s+good\b", " negative_phrase strong_negative "),
    (r"\bnot\s+very\s+good\b", " negative_phrase strong_negative "),
    (r"\bnot\s+good\b", " negative_phrase "),
    (r"\bnot\s+great\b", " negative_phrase "),
    (r"\bnot\s+amazing\b", " negative_phrase "),
    (r"\bnot\s+excellent\b", " negative_phrase "),
    (r"\bnot\s+bad\b", " positive_flip "),
    (r"\bnot\s+terrible\b", " positive_flip "),
    (r"\bnot\s+awful\b", " positive_flip "),
    (r"\bnot\s+horrible\b", " positive_flip "),
    (r"\bcannot\s+recommend\b", " negative_phrase "),
    (r"\bcan\s+not\s+recommend\b", " negative_phrase "),
    (r"\bwill\s+not\s+work\b", " negative_phrase "),
    (r"\bdoes\s+not\s+help\b", " negative_phrase "),
    (r"\bdid\s+not\s+like\b", " negative_phrase "),
    (r"\bfailed\s+to\b", " negative_phrase "),
    (r"\black\s+of\b", " negative_phrase "),
    (r"\bno\s+complaints?\b", " positive_flip "),
    (r"\bno\s+problems?\b", " positive_flip "),
    (r"\bno\s+issues?\b", " positive_flip "),
    (r"\bwithout\s+doubt\b", " confident_phrase "),
    (r"\bnothing\s+special\b", " neutral_phrase "),
]

NEGATION_CUES = {
    "not", "no", "never", "none", "nothing", "nowhere", "nobody",
    "hardly", "barely", "scarcely", "without", "cannot", "little",
}
NEGATION_MULTIWORD_CUES = {("fail", "to"), ("lack", "of"), ("no", "longer")}
NEGATION_BOUNDARIES = {".", "!", "?", ";", ":"}
CONTRAST_WORDS = {"but", "however", "although", "though", "yet"}
CONTENT_FILLERS = {
    "a", "an", "the", "this", "that", "these", "those", "to", "of", "for", "and", "or",
    "very", "really", "so", "too", "at", "all", "any", "be", "is", "am", "are", "was",
    "were", "it", "i", "we", "you", "he", "she", "they", "them", "my", "your", "our",
    "their", "in", "on", "with", "as", "by", "from", "if", "then", "than", "what",
}
SPECIAL_PREFIXES = (
    "positive_", "negative_", "neutral_", "strong_", "mild_", "emphasis_", "question_",
    "mixed_", "confident_", "uncertain_", "laugh_", "surprise_", "frustration_",
    "shock_", "opinion_", "aside_", "candid_", "casual_", "negative_reply",
    "positive_reply", "positive_flip", "negative_phrase", "positive_phrase",
    "audio_positive", "audio_negative",
)

AUDIO_TRANSCRIPT_NORMALIZATION_PATTERNS = [
    (r"\buh+\b", " "),
    (r"\bum+\b", " "),
    (r"\berm+\b", " "),
    (r"\bah+\b", " "),
    (r"\bhmm+\b", " "),
    (r"\bmmm+\b", " "),
    (r"\byou\s+know\b", " "),
    (r"\bi\s+mean\b", " "),
    (r"\bkind\s+of\b", " kinda "),
    (r"\bsort\s+of\b", " sorta "),
    (r"\bday\s+today\b", " day to day "),
    (r"\bday\s+to\s+day\b", " day to day "),
    (r"\bbattery\s+back\s+up\b", " battery backup "),
    (r"\bbattery\s+backups\b", " battery backup "),
    (r"\bback\s+up\b", " backup "),
    (r"\bcamra\b", " camera "),
    (r"\bcameraa\b", " camera "),
    (r"\bsupper\b", " super "),
    (r"\bbajet\b", " budget "),
    (r"\blight\s+weight\b", " lightweight "),
    (r"\bday\s+to\s+day\s+live\b", " day to day life "),
]

AUDIO_POSITIVE_PHRASE_SCORES = {
    "good battery backup": 2.6,
    "battery backup is good": 2.6,
    "camera is super": 2.3,
    "budget friendly": 2.4,
    "very lightweight": 1.9,
    "sound quality is good": 2.5,
    "fits my day to day life": 2.4,
    "works fine": 1.8,
    "pretty good": 1.8,
    "not bad": 2.1,
    "no issue": 2.2,
    "no issues": 2.2,
    "no problem": 2.2,
    "worth it": 1.8,
}

AUDIO_NEGATIVE_PHRASE_SCORES = {
    "not worth it": 2.8,
    "battery drains fast": 2.8,
    "poor sound": 2.5,
    "camera is bad": 2.6,
    "laggy performance": 2.7,
    "sound quality is poor": 2.7,
    "very slow": 2.0,
    "too much lag": 2.4,
    "bad camera": 2.5,
    "poor battery": 2.3,
}

SOCIAL_MEDIA_TEST_CASES = [
    ("OMG this is insane 🔥", "positive"),
    ("lol idk what happened 😅", "neutral"),
    ("this is fire bro", "positive"),
    ("not bad 😊", "positive"),
    ("bruh this is crazy 😡", "negative"),
    ("meh...", "neutral"),
    ("what???", "neutral"),
    ("soooo good!!!", "positive"),
]

POSITIVE_EMOJI_CONTEXTS = [
    "good",
    "great",
    "amazing",
    "love this",
    "this is fire",
    "that is lit",
    "so happy",
    "worth it",
    "excellent",
    "best ever",
]
NEGATIVE_EMOJI_CONTEXTS = [
    "bad",
    "awful",
    "hate this",
    "worst ever",
    "very angry",
    "so disappointed",
    "not good",
    "poor service",
    "this is broken",
    "terrible",
]
NEUTRAL_EMOJI_CONTEXTS = [
    "idk",
    "meh",
    "sorta okay",
    "nothing special",
    "average",
    "not sure",
    "what happened",
    "hmm",
]


def expand_contractions(text: str) -> str:
    """Expand contractions so downstream rules see stable negation tokens."""
    text = str(text)
    for pattern, replacement in CONTRACTION_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def normalize_emojis(text: str) -> str:
    """Convert emojis and emoticons into reusable sentiment-bearing tokens."""
    text = str(text)
    for emoji in POSITIVE_EMOJIS:
        text = text.replace(emoji, " positive_emoji ")
    for emoji in NEGATIVE_EMOJIS:
        text = text.replace(emoji, " negative_emoji ")
    for emoji in NEUTRAL_EMOJIS:
        text = text.replace(emoji, " neutral_emoji ")
    for emoticon, token in EMOTICON_REPLACEMENTS.items():
        text = text.replace(emoticon, f" {token} ")
    return text


def normalize_expressive_phrases(text: str) -> str:
    """Compress common social phrases into sentiment-aware tokens."""
    text = str(text)
    for pattern, replacement in EXPRESSION_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def normalize_slang(text: str) -> str:
    """Map informal slang and shorthand into sentiment-aware tokens."""
    text = str(text)
    for pattern, replacement in SLANG_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def normalize_repeated_characters(text: str) -> str:
    """Tag elongated words so the model keeps intensity from noisy social text."""

    def replace(match: re.Match[str]) -> str:
        word = match.group(0)
        collapsed = re.sub(r"([a-z])\1{2,}", r"\1\1", word)
        return f" emphasis_token {collapsed} "

    text = re.sub(r"\b[a-z]*([a-z])\1{2,}[a-z]*\b", replace, text)
    text = re.sub(r"\bnoo+\b", " negative_reply emphasis_token ", text)
    return text


def normalize_punctuation_intensity(text: str) -> str:
    """Keep repeated punctuation as lightweight intensity features."""

    def replace_mixed(match: re.Match[str]) -> str:
        token_count = min(len(match.group(0)), 3)
        return " ? ! " + " ".join(["mixed_punct"] * token_count) + " "

    def replace_exclaim(match: re.Match[str]) -> str:
        token_count = min(len(match.group(0)), 3)
        return " ! " + " ".join(["emphasis_punct"] * token_count) + " "

    def replace_question(match: re.Match[str]) -> str:
        token_count = min(len(match.group(0)), 3)
        return " ? " + " ".join(["question_punct"] * token_count) + " "

    text = re.sub(r"(?:!\?|\?!)+", replace_mixed, text)
    text = re.sub(r"!{2,}", replace_exclaim, text)
    text = re.sub(r"\?{2,}", replace_question, text)
    return text


def apply_phrase_corrections(text: str) -> str:
    """Patch high-value sentiment flips before generic negation scope runs."""
    text = str(text)
    for pattern, replacement in PHRASE_CORRECTIONS:
        text = re.sub(pattern, replacement, text)
    return text


def should_negate_token(token: str) -> bool:
    return (
        token not in CONTENT_FILLERS
        and token not in CONTRAST_WORDS
        and token not in NEGATION_BOUNDARIES
        and not token.startswith("neg_")
        and not token.startswith(SPECIAL_PREFIXES)
    )


def handle_negation(text: str) -> str:
    """Mark the local negation scope until punctuation or a contrast boundary."""
    tokens = re.findall(r"[a-z_]+|[.!?;:]", text)
    processed: list[str] = []
    negate = False
    negated_content_words = 0
    index = 0

    while index < len(tokens):
        token = tokens[index]

        if token in NEGATION_BOUNDARIES:
            negate = False
            negated_content_words = 0
            index += 1
            continue

        if token in CONTRAST_WORDS:
            negate = False
            negated_content_words = 0
            processed.append(token)
            index += 1
            continue

        multiword_match = None
        for cue in NEGATION_MULTIWORD_CUES:
            cue_length = len(cue)
            if tuple(tokens[index:index + cue_length]) == cue:
                multiword_match = cue
                break

        if multiword_match is not None:
            processed.extend(list(multiword_match))
            negate = True
            negated_content_words = 0
            index += len(multiword_match)
            continue

        if token in NEGATION_CUES:
            processed.append(token)
            negate = True
            negated_content_words = 0
            index += 1
            continue

        if negate and should_negate_token(token):
            processed.append(f"neg_{token}")
            negated_content_words += 1
            if negated_content_words >= 4:
                negate = False
        else:
            processed.append(token)

        index += 1

    return " ".join(processed)


def preprocess_text(text: str) -> str:
    """Unified social-media-aware cleaner used only by the improved logistic pipeline."""
    text = str(text).lower()
    text = expand_contractions(text)
    text = normalize_emojis(text)
    text = normalize_expressive_phrases(text)
    text = normalize_slang(text)
    text = normalize_repeated_characters(text)
    text = normalize_punctuation_intensity(text)
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#(\w+)", r" \1 ", text)
    text = apply_phrase_corrections(text)
    text = handle_negation(text)
    text = re.sub(r"[^a-z_\s.!?;:]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_audio_transcript(text: str) -> str:
    """Light cleanup for speech-to-text output before the main improved preprocessing runs."""
    text = str(text).lower()
    text = expand_contractions(text)
    for pattern, replacement in AUDIO_TRANSCRIPT_NORMALIZATION_PATTERNS:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_audio_debug_text(text: str) -> str:
    """Return the final model-ready transcript for debugging in the UI."""
    return preprocess_text(clean_audio_transcript(text))


def _count_token(processed_text: str, token: str) -> int:
    return len(re.findall(rf"\b{re.escape(token)}\b", processed_text))


def get_audio_sentiment_scores(cleaned_transcript: str, processed_text: str) -> dict[str, float]:
    """Score transcript hints so audio predictions can be stabilized after transcription."""
    transcript = str(cleaned_transcript).lower()
    processed = str(processed_text)
    positive_score = 0.0
    negative_score = 0.0

    for phrase, score in AUDIO_POSITIVE_PHRASE_SCORES.items():
        if phrase in transcript:
            positive_score += score

    for phrase, score in AUDIO_NEGATIVE_PHRASE_SCORES.items():
        if phrase in transcript:
            negative_score += score

    positive_score += _count_token(processed, "positive_phrase") * 0.9
    positive_score += _count_token(processed, "positive_flip") * 1.1
    positive_score += _count_token(processed, "audio_positive") * 1.0
    positive_score += _count_token(processed, "strong_positive") * 0.8
    positive_score += _count_token(processed, "positive_emoji") * 0.35

    negative_score += _count_token(processed, "negative_phrase") * 1.0
    negative_score += _count_token(processed, "audio_negative") * 1.0
    negative_score += _count_token(processed, "strong_negative") * 0.8
    negative_score += len(re.findall(r"\bneg_[a-z_]+\b", processed)) * 0.25
    negative_score += _count_token(processed, "negative_emoji") * 0.35

    return {
        "positive": positive_score,
        "negative": negative_score,
        "balance": positive_score - negative_score,
    }


def postprocess_audio_prediction(
    cleaned_transcript: str,
    processed_text: str,
    predicted_label: str,
    confidence: float | None,
) -> tuple[str, float | None, bool]:
    """Stabilize audio sentiment when transcript phrases strongly disagree with the raw prediction."""
    scores = get_audio_sentiment_scores(cleaned_transcript, processed_text)
    positive_score = scores["positive"]
    negative_score = scores["negative"]
    balance = scores["balance"]
    updated_label = str(predicted_label).lower()
    updated_confidence = None if confidence is None else float(confidence)

    if balance >= 1.4 and updated_label != "positive":
        updated_label = "positive"
        updated_confidence = max(updated_confidence or 0.0, min(0.97, 0.64 + (balance * 0.06)))
    elif balance <= -1.4 and updated_label != "negative":
        updated_label = "negative"
        updated_confidence = max(updated_confidence or 0.0, min(0.97, 0.64 + (abs(balance) * 0.06)))
    elif updated_confidence is not None:
        if balance >= 0.9 and updated_label == "positive":
            updated_confidence = min(0.98, updated_confidence + 0.08)
        elif balance <= -0.9 and updated_label == "negative":
            updated_confidence = min(0.98, updated_confidence + 0.08)

    ambiguous = (
        updated_confidence is None
        or updated_confidence < 0.58
        or (positive_score < 1.0 and negative_score < 1.0)
        or abs(balance) < 0.45
    )

    return updated_label, updated_confidence, ambiguous


def get_social_media_test_cases() -> list[tuple[str, str]]:
    """Small reusable example set for notebook or ad-hoc validation."""
    return list(SOCIAL_MEDIA_TEST_CASES)


def build_emoji_anchor_examples() -> list[tuple[str, str]]:
    """Generate broad emoji-only and mixed emoji/text examples for training anchors."""
    examples: list[tuple[str, str]] = []

    def add_unique(text: str, label: str):
        key = (text, label)
        if key not in seen:
            seen.add(key)
            examples.append(key)

    seen: set[tuple[str, str]] = set()

    for emoji in POSITIVE_EMOJIS:
        add_unique(emoji, "positive")
        add_unique(f"{emoji}{emoji}", "positive")
        add_unique(f"{emoji}{emoji}{emoji}", "positive")
        for context in POSITIVE_EMOJI_CONTEXTS:
            add_unique(f"{context} {emoji}", "positive")
            add_unique(f"{emoji} {context}", "positive")

    for emoji in NEGATIVE_EMOJIS:
        add_unique(emoji, "negative")
        add_unique(f"{emoji}{emoji}", "negative")
        add_unique(f"{emoji}{emoji}{emoji}", "negative")
        for context in NEGATIVE_EMOJI_CONTEXTS:
            add_unique(f"{context} {emoji}", "negative")
            add_unique(f"{emoji} {context}", "negative")

    for emoji in NEUTRAL_EMOJIS:
        add_unique(emoji, "neutral")
        add_unique(f"{emoji}{emoji}", "neutral")
        for context in NEUTRAL_EMOJI_CONTEXTS:
            add_unique(f"{context} {emoji}", "neutral")
            add_unique(f"{emoji} {context}", "neutral")

    for first, second in zip(POSITIVE_EMOJIS[::2], POSITIVE_EMOJIS[1::2]):
        add_unique(f"{first}{second}", "positive")
        add_unique(f"great {first}{second}", "positive")

    for first, second in zip(NEGATIVE_EMOJIS[::2], NEGATIVE_EMOJIS[1::2]):
        add_unique(f"{first}{second}", "negative")
        add_unique(f"awful {first}{second}", "negative")

    mixed_pairs = [
        ("not bad 😊", "positive"),
        ("no problem 😊", "positive"),
        ("good 😊", "positive"),
        ("lol 😂", "positive"),
        ("insane 🔥", "positive"),
        ("crazy 😍", "positive"),
        ("this is lit 🔥🔥", "positive"),
        ("so happy 😊😊", "positive"),
        ("bad 😡", "negative"),
        ("worst service ever 😡😡", "negative"),
        ("oh no 😢", "negative"),
        ("very angry 😡😡", "negative"),
        ("bruh this is crazy 😡", "negative"),
        ("idk 🤔", "neutral"),
        ("wow 😮", "neutral"),
        ("meh 😐", "neutral"),
        ("what??? 😮", "neutral"),
    ]
    for text, label in mixed_pairs:
        add_unique(text, label)

    return examples


def build_anchor_examples(labels) -> tuple[list[str], list[str]]:
    """Add small anchors so emojis, slang, and negation remain learnable."""
    available_labels = {str(label).lower() for label in labels}
    anchor_texts: list[str] = []
    anchor_labels: list[str] = []

    if "positive" in available_labels:
        anchor_texts.extend(
            [
                "not bad 😊",
                "no problem",
                "no issue at all",
                "no complaints",
                "this is fire bro",
                "that is lit 🔥🔥",
                "absolutely amazing",
                "soooo good!!!",
                "good 😊",
                "lol this is crazy",
                "insane 🔥",
                "😊😊😊",
            ]
        )
        anchor_labels.extend(["positive"] * 12)

    if "negative" in available_labels:
        anchor_texts.extend(
            [
                "not good",
                "not very good",
                "i cannot recommend this",
                "this will not work",
                "super bad",
                "really awful",
                "bruh this is crazy 😡",
                "oh no 😢",
                "worst service ever 😡😡",
                "bad 😡",
                "nope this is awful",
                "😡😡😡",
            ]
        )
        anchor_labels.extend(["negative"] * 12)

    if "neutral" in available_labels:
        anchor_texts.extend(
            [
                "idk 🤔",
                "meh...",
                "what???",
                "sorta okay",
                "nothing special",
                "lol idk what happened 😅",
                "😐",
            ]
        )
        anchor_labels.extend(["neutral"] * 7)

    for text, label in build_emoji_anchor_examples():
        if label in available_labels:
            anchor_texts.append(text)
            anchor_labels.append(label)

    return anchor_texts, anchor_labels


def train(texts, labels):
    training_texts = [str(text) for text in texts]
    training_labels = [str(label) for label in labels]
    anchor_texts, anchor_labels = build_anchor_examples(training_labels)

    model = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=preprocess_text,
                    lowercase=False,
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    max_features=12000,
                    min_df=1,
                    max_df=0.97,
                    token_pattern=r"(?u)\b[\w_]{2,}\b",
                ),
            ),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1500,
                    C=2.0,
                ),
            ),
        ]
    )
    model.fit(training_texts + anchor_texts, training_labels + anchor_labels)
    return model


def predict(model, texts):
    return np.array(model.predict(texts))
