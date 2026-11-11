import pytest

from analytics import Measurement, Status, current_status, evaluate_kpi


def test_higher_is_better_statuses():
    res = evaluate_kpi([
        Measurement("2026-01", 100, 100),   # 100% -> в норме
        Measurement("2026-02", 100, 90),    # 90%  -> риск
        Measurement("2026-03", 100, 50),    # 50%  -> отставание
    ])
    assert [r.status for r in res] == [Status.ON_TRACK, Status.AT_RISK, Status.OFF_TRACK]
    assert res[1].deviation == -10
    assert res[1].completion_pct == 90.0


def test_lower_is_better_inverts_logic():
    # CAC: план 100, факт 80 -> лучше плана (125%); факт 200 -> 50%
    res = evaluate_kpi(
        [Measurement("2026-01", 100, 80), Measurement("2026-02", 100, 200)],
        higher_is_better=False,
    )
    assert res[0].completion_pct == 125.0 and res[0].status is Status.ON_TRACK
    assert res[1].completion_pct == 50.0 and res[1].status is Status.OFF_TRACK


def test_missing_fact_is_no_data_and_current_status_skips_it():
    res = evaluate_kpi([Measurement("2026-01", 100, 100), Measurement("2026-02", 100, None)])
    assert res[1].status is Status.NO_DATA and res[1].deviation is None
    assert current_status(res) is Status.ON_TRACK


def test_current_status_without_any_fact():
    assert current_status(evaluate_kpi([Measurement("2026-01", 10, None)])) is Status.NO_DATA


def test_results_sorted_by_period():
    res = evaluate_kpi([Measurement("2026-03", 1, 1), Measurement("2026-01", 1, 1)])
    assert [r.period for r in res] == ["2026-01", "2026-03"]


def test_zero_plan_edge_cases():
    assert evaluate_kpi([Measurement("p", 0, 0)])[0].completion_pct == 100.0
    assert evaluate_kpi([Measurement("p", 0, 5)], higher_is_better=False)[0].completion_pct == 0.0


def test_invalid_thresholds_and_values():
    with pytest.raises(ValueError):
        evaluate_kpi([], ok_threshold=50, risk_threshold=80)
    with pytest.raises(ValueError):
        evaluate_kpi([Measurement("p", float("nan"), 1)])
