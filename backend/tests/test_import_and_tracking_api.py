import io

from openpyxl import Workbook

CSV = (
    "показатель;период;план;факт;единица;направление\n"
    "Лиды;2026-01;100;105;шт;больше\n"
    "Лиды;2026-02;100;80;шт;больше\n"
    "CAC;2026-01;1000,5;900;руб;меньше\n"
    "CAC;2026-02;1000;;руб;меньше\n"
).encode("utf-8")


def _strategy(client):
    return client.post("/strategies", json={"name": "S"}).json()["id"]


def _upload(client, sid, name, content):
    return client.post(f"/strategies/{sid}/import", files={"file": (name, content)})


def test_csv_import_then_tracking(client):
    sid = _strategy(client)
    r = _upload(client, sid, "data.csv", CSV)
    assert r.status_code == 200
    assert r.json() == {"kpis_created": 2, "measurements_created": 4, "measurements_updated": 0}

    body = client.get(f"/strategies/{sid}/tracking").json()
    kpis = {k["name"]: k for k in body["kpis"]}
    assert kpis["Лиды"]["status"] == "at_risk"            # последний период ровно 80%, граница включительная
    assert kpis["Лиды"]["periods"][0]["completion_pct"] == 105.0
    assert kpis["CAC"]["higher_is_better"] is False
    assert kpis["CAC"]["periods"][0]["plan"] == 1000.5     # десятичная запятая
    assert kpis["CAC"]["periods"][1]["status"] == "no_data"
    assert kpis["CAC"]["status"] == "on_track"             # берётся последний период с фактом


def test_reimport_updates_instead_of_duplicating(client):
    sid = _strategy(client)
    _upload(client, sid, "data.csv", CSV)
    r = _upload(client, sid, "data.csv", CSV)
    assert r.json() == {"kpis_created": 0, "measurements_created": 0, "measurements_updated": 4}


def test_cp1251_csv(client):
    sid = _strategy(client)
    r = _upload(client, sid, "data.csv", CSV.decode("utf-8").encode("cp1251"))
    assert r.status_code == 200 and r.json()["measurements_created"] == 4


def test_xlsx_import(client):
    wb = Workbook()
    ws = wb.active
    ws.append(["kpi", "period", "plan", "fact"])
    ws.append(["ROI", "2026-Q1", 1.5, 1.2])
    buf = io.BytesIO()
    wb.save(buf)
    sid = _strategy(client)
    r = _upload(client, sid, "data.xlsx", buf.getvalue())
    assert r.status_code == 200 and r.json()["kpis_created"] == 1
    k = client.get(f"/strategies/{sid}/tracking").json()["kpis"][0]
    assert k["periods"][0]["completion_pct"] == 80.0 and k["status"] == "at_risk"


def test_import_reports_row_errors_and_saves_nothing(client):
    sid = _strategy(client)
    bad = "kpi;period;plan;fact\nA;2026-01;abc;1\nB;;5;1\nC;2026-01;5;1\n".encode()
    r = _upload(client, sid, "bad.csv", bad)
    assert r.status_code == 422
    assert len(r.json()["detail"]) == 2
    assert client.get(f"/strategies/{sid}/tracking").json()["kpis"] == []


def test_import_missing_columns_and_wrong_format(client):
    sid = _strategy(client)
    assert _upload(client, sid, "x.csv", b"a;b\n1;2\n").status_code == 422
    assert _upload(client, sid, "x.txt", b"hello").status_code == 422


def test_unknown_strategy_404(client):
    assert _upload(client, 999, "data.csv", CSV).status_code == 404
    assert client.get("/strategies/999/tracking").status_code == 404


def test_tracking_threshold_params(client):
    sid = _strategy(client)
    _upload(client, sid, "data.csv", CSV)
    ok = client.get(f"/strategies/{sid}/tracking?ok_threshold=70&risk_threshold=60").json()
    assert {k["name"]: k["status"] for k in ok["kpis"]}["Лиды"] == "on_track"
    assert client.get(f"/strategies/{sid}/tracking?ok_threshold=50&risk_threshold=90").status_code == 422
