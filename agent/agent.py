"""Claude tool-calling agent that turns a caregiver note into structured symptom records."""

import json
import os
from pathlib import Path


def _load_env_file():
    """Read ANTHROPIC_API_KEY and CLAUDE_MODEL from a .env file in the project folder, if present."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value and not os.environ.get(key.strip()):
            os.environ[key.strip()] = value


_load_env_file()

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

        if not os.environ.get("ANTHROPIC_API_KEY") or os.environ["ANTHROPIC_API_KEY"] == "your-key-here":
            raise SystemExit(
                "No API key found. Copy .env.example to .env and paste your key after ANTHROPIC_API_KEY=, "
                "or run: export ANTHROPIC_API_KEY=sk-ant-... (Windows: set ANTHROPIC_API_KEY=sk-ant-...)"
            )
        # Organization-wide keys also need the workspace to bill (Console > Settings > Workspaces).
        workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
        headers = {"anthropic-workspace-id": workspace} if workspace else None
        self.client = anthropic.Anthropic(default_headers=headers)
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
