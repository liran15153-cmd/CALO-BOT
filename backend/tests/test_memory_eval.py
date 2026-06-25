from backend.tests.eval.run_memory_gold_set import evaluate


def test_memory_gold_set_safety_recall_is_green(capsys):
    metrics = evaluate()
    print(
        f"memory_eval precision={metrics['precision']} "
        f"recall={metrics['recall']} safety_recall={metrics['safety_recall']}"
    )

    assert metrics["cases"] >= 30
    assert metrics["safety_recall"] == 1.0
    assert metrics["precision"] >= 0.8
    assert metrics["recall"] >= 0.8
