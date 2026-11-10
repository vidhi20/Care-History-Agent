"""Generate 50 synthetic, labeled caregiver notes (10 patients x 5 weekly notes).

All names and notes are fictional. No real patient data is used anywhere in this project.
Run: python data/generate_notes.py  -> writes data/notes.jsonl
"""

import json
import random
import re
from datetime import date, timedelta
from pathlib import Path

SEED = 42

PHRASES = {
    "memory_loss": [
        "She asked me three times what day her doctor visit was.",
        "He forgot that his grandson had visited this morning.",
        "Mom kept repeating the same story about her sister.",
        "Dad didn't remember eating lunch an hour after we ate together.",
        "She put the keys in the fridge and had no idea how they got there.",
    ],
    "confusion": [
        "He thought it was 1985 and asked when he had to leave for work.",
        "She didn't know where she was when she woke up from her nap.",
        "Dad got lost walking back from the mailbox.",
        "Mom called me by my aunt's name all afternoon and seemed unsure who I was.",
    ],
    "agitation": [
        "He got very angry when I helped him with his shirt.",
        "She was restless all evening and kept pacing the hallway.",
        "Dad yelled at the home aide and refused his shower.",
        "Mom snapped at everyone during dinner, which is not like her.",
    ],
    "sleep_disturbance": [
        "She was up at 3am folding towels.",
        "He couldn't sleep most of the night and kept turning on lights.",
        "Mom slept most of the day and was awake until 4am.",
        "Dad woke up four times last night asking for his mother.",
    ],
    "wandering": [
        "I found him at the front door with his coat on, saying he had to go home.",
        "She walked out to the street before the neighbor brought her back.",
        "Dad tried to leave the house twice tonight.",
        "Mom wandered into the neighbor's yard this afternoon.",
    ],
    "appetite_change": [
        "She barely touched her dinner again.",
        "He skipped breakfast and lunch and said he wasn't hungry.",
        "Mom has lost her appetite this week and only drinks tea.",
        "Dad refused to eat anything except crackers.",
    ],
    "falls": [
        "He fell in the bathroom but did not hit his head.",
        "She nearly fell getting out of the car.",
        "Dad seems unsteady on the stairs now and holds the wall.",
        "Mom lost her balance in the kitchen and grabbed the counter.",
    ],
    "mood_depression": [
        "She cried for a long time after her phone call.",
        "He seems withdrawn and didn't want to see his friends from church.",
        "Mom says she feels sad and has no interest in her garden anymore.",
        "Dad sat quietly all day and wouldn't join us for cards.",
    ],
    "hallucinations": [
        "He said he saw a man in the corner of the room who was not there.",
        "She was talking to someone who wasn't in the room.",
        "Mom said she saw children playing in the living room, but nobody was there.",
    ],
    "communication": [
        "She couldn't find the word for spoon and pointed instead.",
        "He lost his train of thought in the middle of every sentence.",
        "Mom's words came out mixed up when she tried to tell me about her day.",
        "Dad was hard to follow on the phone today.",
    ],
}

NEUTRAL = [
    "We went for a short walk around the block.",
    "Her daughter visited and they looked at photo albums.",
    "He enjoyed listening to music after dinner.",
    "Took all medications on time today.",
    "No falls this week, which is good news.",
    "The weather was nice so we sat on the porch.",
    "Physical therapy session went fine.",
    "She was in a good mood at breakfast.",
]

FEMALE = {r"\bHe\b": "She", r"\bhe\b": "she", r"\bhis\b": "her", r"\bhim\b": "her", r"\bHis\b": "Her", r"\bDad\b": "Mom"}
MALE = {r"\bShe\b": "He", r"\bshe\b": "he", r"\bher\b": "his", r"\bHer\b": "His", r"\bMom\b": "Dad"}


def set_gender(sentence, female):
    for pat, rep in (FEMALE if female else MALE).items():
        sentence = re.sub(pat, rep, sentence)
    return sentence


NAMES = ["P001", "P002", "P003", "P004", "P005", "P006", "P007", "P008", "P009", "P010"]


def main():
    rng = random.Random(SEED)
    cats = list(PHRASES)
    rows = []
    start = date(2026, 1, 5)
    for pid in NAMES:
        base = rng.sample(cats, 2)  # symptoms this patient tends to show
        seen = set()
        female = rng.random() < 0.5
        for week in range(5):
            n_today = rng.choice([0, 1, 2, 2, 3])
            today = set(rng.sample(base, min(len(base), n_today)))
            if n_today and rng.random() < 0.5:
                today.add(rng.choice(cats))  # occasional new symptom
            today = sorted(today)[:3]
            sentences = [rng.choice(PHRASES[c]) for c in today]
            sentences += rng.sample(NEUTRAL, rng.choice([1, 2]))
            rng.shuffle(sentences)
            sentences = [set_gender(x, female) for x in sentences]
            rows.append({
                "note_id": f"{pid}-W{week + 1}",
                "patient_id": pid,
                "date": str(start + timedelta(weeks=week)),
                "text": " ".join(sentences),
                "labels": {
                    "symptoms": today,
                    "new_symptoms": [c for c in today if c not in seen],
                },
            })
            seen.update(today)
    out = Path(__file__).parent / "notes.jsonl"
    out.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print(f"Wrote {len(rows)} notes to {out}")


if __name__ == "__main__":
    main()
