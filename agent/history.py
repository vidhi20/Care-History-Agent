"""In-memory care history: what each patient has shown, and when."""

from collections import defaultdict


class CareHistory:
    def __init__(self):
        self._first_seen = defaultdict(dict)   # patient_id -> {category: first date}
        self._timeline = defaultdict(list)     # patient_id -> [entry, ...]

    def known_symptoms(self, patient_id):
        return dict(self._first_seen[patient_id])

    def record(self, patient_id, note_date, symptoms):
        for s in symptoms:
            self._first_seen[patient_id].setdefault(s["category"], note_date)
        self._timeline[patient_id].append({"date": note_date, "symptoms": symptoms})

    def timeline(self, patient_id):
        return list(self._timeline[patient_id])

    def to_markdown(self, patient_id):
        lines = [f"# Care history for {patient_id}", ""]
        for entry in self._timeline[patient_id]:
            lines.append(f"## {entry['date']}")
            if not entry["symptoms"]:
                lines.append("- No symptoms noted")
            for s in entry["symptoms"]:
                tag = " **NEW**" if s.get("is_new") else ""
                lines.append(f"- {s['category'].replace('_', ' ')}{tag}: \"{s['evidence']}\"")
            lines.append("")
        return "\n".join(lines)
