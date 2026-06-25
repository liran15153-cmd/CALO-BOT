from backend.tests.eval.run_intent_gold_set import evaluate


def test_intent_gold_set_routes_hebrew_coach_requests(capsys):
    metrics = evaluate()
    print(
        f"intent_eval deterministic_accuracy={metrics['deterministic_accuracy']} "
        f"fallback_accuracy={metrics['fallback_accuracy']} final_accuracy={metrics['final_accuracy']}"
    )

    assert metrics["cases"] >= 30
    assert metrics["deterministic_cases"] >= 30
    assert metrics["fallback_cases"] >= 3
    assert metrics["fallback_used"] >= 3
    assert metrics["deterministic_accuracy"] >= 0.9
    assert metrics["fallback_accuracy"] >= 0.95
    assert metrics["final_accuracy"] >= 0.95
    assert metrics["failures"] == []
