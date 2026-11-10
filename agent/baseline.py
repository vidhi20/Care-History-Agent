"""Simple keyword baseline. Used for offline testing (--mock) and as a comparison point for the agent."""

import re

from .history import CareHistory

KEYWORDS = {
    "memory_loss": [r"forg[eo]t", r"repeat(ed|ing)? (the same|herself|himself|questions?)", r"didn'?t remember", r"asked .* again"],
    "confusion": [r"confus", r"didn'?t know where", r"thought it was", r"got lost", r"disorient"],
    "agitation": [r"agitat", r"angry", r"yell", r"snapped", r"restless", r"irritab"],
    "sleep_disturbance": [r"awake (at|until)", r"up at \d", r"couldn'?t sleep", r"slept (most|all) (of )?the day", r"woke up .* night"],
    "wandering": [r"wander", r"front door", r"walked out", r"tried to leave"],
    "appetite_change": [r"(barely|didn'?t|refused to) (eat|touch)", r"skipped (lunch|dinner|breakfast)", r"lost (his|her) appetite"],
    "falls": [r"fell\b", r"\bfall\b", r"nearly fell", r"lost (his|her) balance", r"unsteady"],
    "mood_depression": [r"cried|crying|tearful", r"withdrawn", r"sad\b", r"no interest", r"didn'?t want to (do|see)"],
    "hallucinations": [r"saw (a|people|someone) .*(not there|wasn'?t there)", r"hearing voices", r"talking to someone who"],
    "communication": [r"couldn'?t find the (word|words)", r"lost (his|her) train of thought", r"hard to follow", r"words? (came out|mixed)"],
}


class KeywordBaseline:
    def __init__(self, history=None):
        self.history = history or CareHistory()

    def process_note(self, patient_id, note_date, text):
        low = text.lower()
        known = self.history.known_symptoms(patient_id)
        found = []
        for cat, pats in KEYWORDS.items():
            for p in pats:
                m = re.search(p, low)
                if m:
                    found.append({"category": cat, "evidence": text[m.start():m.end() + 30].strip(),
                                  "is_new": cat not in known})
                    break
        self.history.record(patient_id, note_date, found)
        return found
