from __future__ import annotations

import json
from collections import Counter

from backend.app.services.memory_service import MemoryService, SAFETY_FACT_TYPES
from backend.tests.eval.memory_gold_set import GOLD_CASES


def evaluate() -> dict[str, float]:
    service = MemoryService(db=None)  # type: ignore[arg-type]
    tp = fp = fn = safety_should = safety_hit = 0
    for case in GOLD_CASES:
        got = service.extract_safety_candidates(case["text"])
        got_counts = Counter(candidate.fact_type for candidate in got)
        expected_counts = Counter(case["expected_types"])
        tp += sum((got_counts & expected_counts).values())
        fp += sum((got_counts - expected_counts).values())
        fn += sum((expected_counts - got_counts).values())
        expected_safety = [fact_type for fact_type in expected_counts if fact_type in SAFETY_FACT_TYPES]
        safety_should += len(expected_safety)
        safety_hit += sum(1 for fact_type in expected_safety if got_counts[fact_type] > 0)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    safety_recall = safety_hit / safety_should if safety_should else 1.0
    return {
        "cases": float(len(GOLD_CASES)),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "safety_recall": round(safety_recall, 4),
    }


def main() -> int:
    metrics = evaluate()
    print(json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    if metrics["safety_recall"] != 1.0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
