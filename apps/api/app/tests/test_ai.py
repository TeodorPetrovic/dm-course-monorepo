"""Day 11: AI rute — template fallback i validacija."""


def ok(r, code=200):
    assert r.status_code == code, (r.request.url, r.status_code, r.text[:300])
    return r.json()


def test_day11_ai(client):
    seo = ok(client.post("/ai/seo", json={"product_name": "Smartphone Compact 686", "description": "x",
                                          "category_name": "Electronics"}))
    assert seo["source"] == "template" and seo["fallback_reason"] == "model_unavailable"
    ok(client.post("/ai/seo", json={"product_name": ""}), 422)
    ok(client.post("/ai/content", json={"kind": "nope"}), 422)
    ok(client.post("/ai/content", json={"kind": "campaign_copy", "campaign_name": "VIP"}))
