"""Score the agent (or the keyword baseline) against the 50 labeled notes.

Usage:
  python eval/evaluate.py            # Claude agent (needs ANTHROPIC_API_KEY)
  python eval/evaluate.py --mock     # keyword baseline, no API key needed
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import CareHistory, KeywordBaseline, SYMPTOM_CATEGORIES  # noqa: E402


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return round(p, 3), round(r, 3), round(f, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="use the keyword baseline instead of Claude")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    notes = [json.loads(l) for l in (ROOT / "data" / "notes.jsonl").read_text().splitlines() if l.strip()]
    history = CareHistory()
    if args.mock:
        runner, name = KeywordBaseline(history), "keyword_baseline"
    else:
        from agent.agent import CareHistoryAgent
        runner = CareHistoryAgent(model=args.model, history=history)
        name = runner.model

    sym = Counter()      # tp/fp/fn for symptom extraction
    new = Counter()      # tp/fp/fn for new-change detection
    per_cat = {c: Counter() for c in SYMPTOM_CATEGORIES}
    fully_correct, predictions = 0, []

    for n in sorted(notes, key=lambda x: (x["patient_id"], x["date"])):
        pred = runner.process_note(n["patient_id"], n["date"], n["text"])
        p_sym = {s["category"] for s in pred}
        p_new = {s["category"] for s in pred if s.get("is_new")}
        g_sym, g_new = set(n["labels"]["symptoms"]), set(n["labels"]["new_symptoms"])
        for c in SYMPTOM_CATEGORIES:
            per_cat[c]["tp"] += c in p_sym and c in g_sym
            per_cat[c]["fp"] += c in p_sym and c not in g_sym
            per_cat[c]["fn"] += c not in p_sym and c in g_sym
        sym.update(tp=len(p_sym & g_sym), fp=len(p_sym - g_sym), fn=len(g_sym - p_sym))
        new.update(tp=len(p_new & g_new), fp=len(p_new - g_new), fn=len(g_new - p_new))
        fully_correct += p_sym == g_sym and p_new == g_new
        predictions.append({"note_id": n["note_id"], "predicted": sorted(p_sym), "gold": sorted(g_sym)})

    sp, sr, sf = prf(sym["tp"], sym["fp"], sym["fn"])
    np_, nr, nf = prf(new["tp"], new["fp"], new["fn"])
    metrics = {
        "runner": name,
        "notes": len(notes),
        "symptom_extraction": {"precision": sp, "recall": sr, "f1": sf},
        "new_change_detection": {"precision": np_, "recall": nr, "f1": nf},
        "fully_correct_notes": fully_correct,
        "per_category_f1": {c: prf(v["tp"], v["fp"], v["fn"])[2] for c, v in per_cat.items()},
    }
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    tag = "baseline" if args.mock else "agent"
    (out_dir / f"metrics_{tag}.json").write_text(json.dumps(metrics, indent=2))
    (out_dir / f"predictions_{tag}.json").write_text(json.dumps(predictions, indent=2))
    (out_dir / f"timeline_P001_{tag}.md").write_text(history.to_markdown("P001"))

    print(json.dumps(metrics, indent=2))
    print(f"\nPlain English: caught {sr:.0%} of symptoms, {sp:.0%} of flags were correct, "
          f"{fully_correct}/{len(notes)} notes fully correct.")


if __name__ == "__main__":
    main()
