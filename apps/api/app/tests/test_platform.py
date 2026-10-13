"""Day 12: integrisana platforma."""


def ok(r, code=200):
    assert r.status_code == code, (r.request.url, r.status_code, r.text[:300])
    return r.json()


def test_day12_platform(client):
    m = ok(client.get("/platform/modules"))
    assert m["summary"]["total"] == 18
    ok(client.get("/platform/profile/395"))
    hp = ok(client.get("/platform/homepage?user_id=395&session_id=session_005246"))
    assert hp["hero"]["fallback"] is True
    ok(client.get("/platform/product/22"))
    ok(client.get("/platform/product/99999"), 404)
