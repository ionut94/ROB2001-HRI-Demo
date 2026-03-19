"""Emotion classification from text using keyword matching."""

EMOTION_KEYWORDS = {
    "excited": ["great", "wonderful", "amazing", "excellent", "fantastic",
                "awesome", "brilliant", "incredible", "perfect", "love"],
    "positive": ["good", "nice", "happy", "pleased", "fine", "well",
                 "beautiful", "pretty", "lovely", "enjoy", "glad"],
    "warning":  ["danger", "warning", "careful", "caution", "risk", "hazard",
                 "unsafe", "alert", "watch out", "stop", "don't", "avoid"],
    "negative": ["bad", "terrible", "awful", "horrible", "wrong", "error",
                 "fail", "broken", "damage", "problem", "sorry", "unfortunately"],
}

EMOTION_RATE = {
    "excited": 210,
    "positive": 185,
    "neutral":  175,
    "negative": 155,
    "warning":  140,
}


def classify_emotion(text: str) -> str:
    """Classify emotion from text using keyword matching."""
    text_lower = text.lower()
    scores = {e: 0 for e in EMOTION_KEYWORDS}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[emotion] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "neutral"


def get_emotion_rate(emotion: str) -> int:
    """Return pyttsx3 speech rate for a given emotion."""
    return EMOTION_RATE.get(emotion, 175)
