# core/command_parser.py
"""
Spell-tolerant command parsing with fuzzy matching.
"""

import re
from difflib import SequenceMatcher

# Command verb synonyms
VERB_SYNONYMS = {
    "open": ["open", "launch", "start", "run", "show", "kholo", "chalu"],
    "search": ["search", "find", "look", "google", "youtube", "khojo", "dhundo"],
    "play": ["play", "start", "run", "chala", "bajao"],
    "pause": ["pause", "stop", "hold", "ruko", "band"],
    "close": ["close", "exit", "quit", "end", "band karo"],
    "talk": ["talk", "speak", "say", "tell", "chat", "bolo", "baat"],
    "click": ["click", "press", "tap", "select", "choose"],
    "type": ["type", "write", "enter", "input", "likho"],
    "screenshot": ["screenshot", "capture", "snap", "photo"],
}

# App name synonyms
APP_SYNONYMS = {
    "youtube": ["youtube", "yt", "you tube", "utube"],
    "whatsapp": ["whatsapp", "wa", "whats app", "watsapp"],
    "chrome": ["chrome", "google chrome", "browser"],
    "vscode": ["vscode", "vs code", "visual studio code", "code"],
    "notepad": ["notepad", "note pad", "notes"],
    "calculator": ["calculator", "calc", "calculate"],
    "spotify": ["spotify", "music", "songs"],
    "discord": ["discord", "disc"],
    "gmail": ["gmail", "email", "mail", "g mail"],
    "github": ["github", "git hub", "git"],
}

# Common misspellings and phonetic confusions
PHONETIC_FIXES = {
    "tank": "talk",
    "tack": "talk",
    "tok": "talk",
    "tongue": "talk",
    "taught": "talk",
    "ope": "open",
    "opn": "open",
    "serch": "search",
    "sreach": "search",
    "plau": "play",
    "paly": "play",
    "paus": "pause",
    "clik": "click",
    "tipe": "type",
}


def normalize_text(text: str) -> str:
    """
    Normalize text for command parsing:
    - Collapse spaced-out letters (T A N K -> TANK)
    - Fix common phonetic misspellings
    - Lowercase
    - Remove extra punctuation
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower().strip()
    
    # Collapse spaced-out single letters (e.g., "T A N K" -> "tank")
    # Pattern: single letters separated by spaces
    spaced_pattern = r'\b([a-z])\s+([a-z])\s+([a-z])(?:\s+([a-z]))?(?:\s+([a-z]))?\b'
    
    def collapse_letters(match):
        letters = [g for g in match.groups() if g]
        return ''.join(letters)
    
    text = re.sub(spaced_pattern, collapse_letters, text)
    
    # Also handle 2-letter spacing
    text = re.sub(r'\b([a-z])\s+([a-z])\b', lambda m: m.group(1) + m.group(2), text)
    
    # Apply phonetic fixes
    words = text.split()
    fixed_words = []
    for word in words:
        fixed = PHONETIC_FIXES.get(word, word)
        fixed_words.append(fixed)
    text = ' '.join(fixed_words)
    
    # Remove extra punctuation but keep basic structure
    text = re.sub(r'[^\w\s\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def fuzzy_match(word: str, candidates: list, threshold: float = 0.7) -> str:
    """
    Find best fuzzy match for a word among candidates.
    Returns the best match or original word if no good match.
    """
    if not word or not candidates:
        return word
    
    best_match = word
    best_score = 0
    
    for candidate in candidates:
        score = SequenceMatcher(None, word.lower(), candidate.lower()).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate
    
    return best_match


def extract_command_verb(text: str) -> tuple:
    """
    Extract the command verb from text using fuzzy matching.
    Returns (verb, remaining_text)
    """
    text = normalize_text(text)
    words = text.split()
    
    if not words:
        return (None, text)
    
    # Check first few words for command verbs
    all_verbs = []
    for verb, synonyms in VERB_SYNONYMS.items():
        all_verbs.extend(synonyms)
    
    for i, word in enumerate(words[:3]):
        matched_verb = fuzzy_match(word, all_verbs, threshold=0.65)
        if matched_verb != word or matched_verb in all_verbs:
            # Find canonical verb
            for verb, synonyms in VERB_SYNONYMS.items():
                if matched_verb in synonyms:
                    remaining = ' '.join(words[i+1:])
                    return (verb, remaining)
    
    return (None, text)


def extract_app_name(text: str) -> str:
    """
    Extract app name from text using fuzzy matching.
    """
    text = normalize_text(text)
    
    all_apps = []
    for app, synonyms in APP_SYNONYMS.items():
        all_apps.extend(synonyms)
    
    words = text.split()
    for word in words:
        matched_app = fuzzy_match(word, all_apps, threshold=0.7)
        if matched_app in all_apps:
            # Find canonical app name
            for app, synonyms in APP_SYNONYMS.items():
                if matched_app in synonyms:
                    return app
    
    # Return first word as fallback
    return words[0] if words else ""


def parse_command(text: str) -> dict:
    """
    Parse a command with fuzzy matching.
    Returns dict with: verb, target, query, original
    """
    original = text
    normalized = normalize_text(text)
    
    verb, remaining = extract_command_verb(normalized)
    
    result = {
        "original": original,
        "normalized": normalized,
        "verb": verb,
        "target": None,
        "query": remaining,
    }
    
    if verb in ["open", "close", "play"]:
        result["target"] = extract_app_name(remaining)
    
    return result


# Tests
if __name__ == "__main__":
    test_cases = [
        "O P E N YouTube",
        "T A N K to me",
        "serch for biology videos",
        "opn notepad",
        "paus the video",
        "Open YouTube, search biology 2024, click third video",
    ]
    
    print("Command Parser Tests:")
    print("=" * 50)
    
    for test in test_cases:
        result = parse_command(test)
        print(f"\nInput: '{test}'")
        print(f"  Normalized: '{result['normalized']}'")
        print(f"  Verb: {result['verb']}")
        print(f"  Target: {result['target']}")
        print(f"  Query: '{result['query']}'")
