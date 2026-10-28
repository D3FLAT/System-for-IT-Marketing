def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_evaluate_flow(client):
    sid = client.post("/strategies", json={"name": "Стратегия 2026"}).json()["id"]
    for name, ap in [("SEO", 0.8), ("Вебинары", 0.3), ("Контекст", 0.55)]:
        r = client.post(f"/strategies/{sid}/projects", json={"name": name, "ap": ap})
        assert r.status_code == 201

    r = client.post(f"/strategies/{sid}/evaluate", json={"threshold": 0.5})
    assert r.status_code == 200
    body = r.json()
    assert [p["name"] for p in body["accepted"]] == ["SEO", "Контекст"]
    assert [p["name"] for p in body["rejected"]] == ["Вебинары"]


def test_unknown_strategy_returns_404(client):
    r = client.post("/strategies/999/evaluate", json={"threshold": 0.5})
    assert r.status_code == 404


def test_rejects_nan_threshold(client):
    sid = client.post("/strategies", json={"name": "S"}).json()["id"]
    r = client.post(f"/strategies/{sid}/evaluate", content='{"threshold": NaN}',
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 422
