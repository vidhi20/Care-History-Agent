"""Symptom categories and the tool definitions the agent can call."""

SYMPTOM_CATEGORIES = {
    "memory_loss": "Forgetting recent events, names, conversations, or repeating questions",
    "confusion": "Disorientation about time, place, or people; getting lost in familiar places",
    "agitation": "Restlessness, irritability, anger, or aggressive behavior",
    "sleep_disturbance": "Trouble sleeping, waking at night, sleeping much more or at odd hours",
    "wandering": "Leaving home or walking away without a clear purpose, trying to 'go home'",
    "appetite_change": "Eating much less or more, skipping meals, refusing food",
    "falls": "Falling, near falls, or new trouble with balance and walking",
    "mood_depression": "Sadness, withdrawal, crying, loss of interest in usual activities",
    "hallucinations": "Seeing or hearing things that are not there",
    "communication": "Trouble finding words, following conversations, or speaking clearly",
}

TOOLS = [
    {
        "name": "get_patient_history",
        "description": (
            "Return every symptom already recorded for this patient in earlier notes, "
            "with the date it was first seen. Call this before recording symptoms so you "
            "can decide which symptoms are new."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"patient_id": {"type": "string"}},
            "required": ["patient_id"],
        },
    },
    {
        "name": "record_symptoms",
        "description": (
            "Save the symptoms found in today's caregiver note. Only include symptoms the "
            "note clearly describes. Mark is_new=true when the symptom does not appear in "
            "the patient's history. Call this exactly once per note, even if no symptoms are found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string"},
                "note_date": {"type": "string"},
                "symptoms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": list(SYMPTOM_CATEGORIES)},
                            "evidence": {
                                "type": "string",
                                "description": "Short quote from the note that shows the symptom",
                            },
                            "is_new": {"type": "boolean"},
                        },
                        "required": ["category", "evidence", "is_new"],
                    },
                },
            },
            "required": ["patient_id", "note_date", "symptoms"],
        },
    },
]
