"""Process one patient's notes and print the care timeline a doctor would see.

Usage:
  python run_demo.py P003          # Claude agent
  python run_demo.py P003 --mock   # keyword baseline
"""

import json
import sys
from pathlib import Path

from agent import CareHistory, KeywordBaseline


def main():
    pid = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "P001"
    mock = "--mock" in sys.argv
    notes = [json.loads(l) for l in Path("data/notes.jsonl").read_text().splitlines() if l.strip()]
    history = CareHistory()
    if mock:
        runner = KeywordBaseline(history)
    else:
        from agent.agent import CareHistoryAgent
        runner = CareHistoryAgent(history=history)
    for n in sorted((n for n in notes if n["patient_id"] == pid), key=lambda x: x["date"]):
        runner.process_note(n["patient_id"], n["date"], n["text"])
    print(history.to_markdown(pid))


if __name__ == "__main__":
    main()
