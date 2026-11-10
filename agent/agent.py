"""Claude tool-calling agent that turns a caregiver note into structured symptom records."""

import json
import os

from .history import CareHistory
from .schema import SYMPTOM_CATEGORIES, TOOLS

SYSTEM_PROMPT = """You read short daily notes written by family caregivers of people living with dementia.
Your job is to turn each note into a structured symptom record for the care team.

Symptom categories:
{categories}

Steps for every note:
1. Call get_patient_history for the patient.
2. Decide which categories the note clearly describes. Do not guess; ignore normal days.
3. Call record_symptoms once with each symptom, a short evidence quote, and is_new
   (true only if that category is not already in the history).
Do not give medical advice."""


class CareHistoryAgent:
    def __init__(self, model=None, history=None, max_turns=6):
        import anthropic  # imported here so --mock runs need no SDK

        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
        self.history = history or CareHistory()
        self.max_turns = max_turns
        cats = "\n".join(f"- {k}: {v}" for k, v in SYMPTOM_CATEGORIES.items())
        self.system = SYSTEM_PROMPT.format(categories=cats)

    def _run_tool(self, name, args, recorded):
        if name == "get_patient_history":
            return self.history.known_symptoms(args["patient_id"])
        if name == "record_symptoms":
            symptoms = [s for s in args.get("symptoms", []) if s.get("category") in SYMPTOM_CATEGORIES]
            # Recompute is_new from the stored history so the flag is always consistent.
            known = self.history.known_symptoms(args["patient_id"])
            for s in symptoms:
                s["is_new"] = s["category"] not in known
            recorded.extend(symptoms)
            return {"saved": len(symptoms)}
        return {"error": f"unknown tool {name}"}

    def process_note(self, patient_id, note_date, text):
        messages = [{
            "role": "user",
            "content": f"Patient: {patient_id}\nDate: {note_date}\nCaregiver note:\n{text}",
        }]
        recorded = []
        for _ in range(self.max_turns):
            resp = self.client.messages.create(
                model=self.model, max_tokens=16000, system=self.system,
                tools=TOOLS, messages=messages,
            )
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                break
            results = []
            for block in resp.content:
                if block.type == "tool_use":
                    out = self._run_tool(block.name, block.input, recorded)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out)})
            messages.append({"role": "user", "content": results})
        # Deduplicate by category, keep first evidence.
        seen, unique = set(), []
        for s in recorded:
            if s["category"] not in seen:
                seen.add(s["category"])
                unique.append(s)
        self.history.record(patient_id, note_date, unique)
        return unique
