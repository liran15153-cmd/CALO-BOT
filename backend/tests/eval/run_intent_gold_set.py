from __future__ import annotations

import json
from collections import Counter
from typing import Any

from backend.app.services.coach_intent_service import CoachIntentService
from backend.tests.eval.intent_gold_set import GOLD_CASES


def evaluate() -> dict[str, Any]:
    service = CoachIntentService()
    categories: Counter[str] = Counter()
    failures: list[dict[str, str]] = []
    deterministic_cases = deterministic_hits = 0
    fallback_cases = fallback_hits = fallback_used = 0
    final_hits = 0

    for case in GOLD_CASES:
        expected = case["expected_intent"]
        deterministic = service.classify(case["text"]).name
        final = deterministic
        fallback_intent = case.get("fallback_intent")
        if fallback_intent and deterministic == "general_chat":
            final = fallback_intent
            fallback_used += 1

        categories[case["category"]] += 1
        if fallback_intent:
            fallback_cases += 1
            if final == expected:
                fallback_hits += 1
        else:
            deterministic_cases += 1
            if deterministic == expected:
                deterministic_hits += 1

        if final == expected:
            final_hits += 1
        else:
            failures.append(
                {
                    "text": case["text"],
                    "expected": expected,
                    "deterministic": deterministic,
                    "final": final,
                }
            )

    cases = len(GOLD_CASES)
    return {
        "cases": cases,
        "deterministic_cases": deterministic_cases,
        "fallback_cases": fallback_cases,
        "fallback_used": fallback_used,
        "deterministic_accuracy": round(deterministic_hits / deterministic_cases, 4),
        "fallback_accuracy": round(fallback_hits / fallback_cases, 4),
        "final_accuracy": round(final_hits / cases, 4),
        "categories": dict(sorted(categories.items())),
        "failures": failures,
    }


def main() -> int:
    metrics = evaluate()
    print(json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    if metrics["deterministic_accuracy"] < 0.9 or metrics["final_accuracy"] < 0.95:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
