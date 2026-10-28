import pytest

from analytics import ProjectScore, screen_projects


def _p(i, ap):
    return ProjectScore(id=i, name=f"P{i}", ap=ap)


def test_splits_by_threshold_and_keeps_order():
    res = screen_projects([_p(1, 0.9), _p(2, 0.2), _p(3, 0.6)], threshold=0.5)
    assert [p.id for p in res.accepted] == [1, 3]
    assert [p.id for p in res.rejected] == [2]


def test_threshold_is_inclusive():
    res = screen_projects([_p(1, 0.5)], threshold=0.5)
    assert [p.id for p in res.accepted] == [1]


def test_empty_input():
    res = screen_projects([], threshold=0.5)
    assert res.accepted == [] and res.rejected == []


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_rejects_non_finite_threshold(bad):
    with pytest.raises(ValueError):
        screen_projects([_p(1, 0.5)], threshold=bad)


def test_rejects_non_finite_ap():
    with pytest.raises(ValueError):
        screen_projects([_p(1, float("nan"))], threshold=0.5)
