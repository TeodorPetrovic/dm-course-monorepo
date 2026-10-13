"""End-to-end smoke test svih API koraka iz lekcija (Day 1–12), redom kojim ih studenti rade."""


def ok(r, code=200):
    assert r.status_code == code, (r.request.url, r.status_code, r.text[:300])
    return r.json()


def test_day01_events_analytics(client):
    s = ok(client.get("/analytics/summary"))
    assert s["views"] == 94220 and s["sessions"] == 15361
    e = ok(client.post("/events", json={"event_type": "product_view", "user_id": 1, "product_id": 1,
                                         "user_session": "session_test",
                                         "timestamp": "2026-01-31 12:00:00"}), 201)
    assert e["event_id"] > 183468
    ok(client.post("/events", json={"event_type": "bogus"}), 422)
    ok(client.get("/analytics/products/99999/views"), 404)
    p = ok(client.get("/analytics/products/1"))
    assert set(p) == {"product_id", "views", "carts", "purchases"}
    ok(client.get("/analytics/share-by-category?metric=cart"))
    ok(client.get("/analytics/share-by-category?metric=nope"), 422)
    assert ok(client.get("/analytics/average-order-value"))["average_order_value"] > 0
    ok(client.get("/analytics/searches"))


def test_live_event_now_does_not_break_training(client, tmp_path):
    """Živi događaj sa današnjim timestamp-om (npr. iz frontenda) ide u store i vidi se u analitici,
    ali batch trening (Day 2–4) koristi seeded snapshot -> referenca se ne pomera, trening radi."""
    import pandas as pd
    from app.data.events import EventStore
    from app.services import store
    from app.services.conversion import ConversionService
    old = store.get_store()
    ev = old.events_dataframe().copy()
    extra = ev.iloc[[0]].copy(); extra["timestamp"] = "2026-10-13 10:00:00"
    store.set_store(EventStore(pd.concat([ev, extra], ignore_index=True), n_seed=len(ev)))
    try:
        assert len(store.require_events()) == len(ev) + 1
        assert len(store.require_events(include_live=False)) == len(ev)
        meta = ConversionService(models=tmp_path).train()
        assert meta["reference"].startswith("2026-01-31")
        # bez snapshot granice (n_seed = sve) zamka i dalje postoji -> jasna greška, ne 500
        store.set_store(EventStore(pd.concat([ev, extra], ignore_index=True)))
        import pytest
        with pytest.raises(ValueError):
            ConversionService(models=tmp_path).train()
    finally:
        store.set_store(old)


def test_day02_03_untrained_then_trained(client):
    ok(client.get("/segments"), 503)
    ok(client.get("/models/conversion/status"), 503)
    m = ok(client.post("/segments/train", json={"k": 4}))
    assert m["k"] == 4
    ok(client.post("/segments/train", json={"k": 1}), 422)
    seg = ok(client.get("/customers/395/segment"))
    assert seg["segment"].startswith("segment_")
    assert ok(client.get("/segments/customer/999999"))["fallback"] is True
    ok(client.post("/models/conversion/train", json={"model_type": "logistic_regression"}))
    st = ok(client.get("/analytics/conversion/status"))
    assert 0 < st["base_rate"] < 1
    pr = ok(client.get("/customers/395/conversion-probability"))
    assert 0 <= pr["probability"] <= 1
    assert ok(client.get("/models/conversion/probability/999999"))["reason"] == "no_history"


def test_day04_targeting(client):
    assert len(ok(client.get("/campaigns"))) == 4
    ok(client.get("/campaigns/99"), 404)
    a = ok(client.get("/campaigns/1/recommended-audience?mode=ml&limit=5"))
    assert a["mode"] == "ml" and a["returned"] <= 5
    ok(client.get("/campaigns/1/audience?mode=rule&limit=5"))
    ok(client.get("/campaigns/1/recommended-audience?mode=zzz"), 422)
    assert "metrics" in ok(client.get("/campaigns/1/targeting-comparison"))


def test_day05_06_recs(client):
    p = ok(client.get("/recommendations/popular"))
    assert [r["product_id"] for r in p["recommendations"]] == [90, 184, 110, 12, 49]
    c = ok(client.get("/recommendations/content/1?limit=5"))
    assert 1 not in [r["product_id"] for r in c["recommendations"]]
    assert ok(client.get("/recommendations/content/99999"))["fallback"] is True
    ok(client.get("/recommendations/category/99999"), 404)
    ok(client.get("/recommendations/content/1/comparison"))
    cf = ok(client.get("/recommendations/collaborative/1?limit=5"))
    assert cf["method"] == "collaborative" and cf["returned"] == 5
    assert ok(client.get("/recommendations/collaborative/99999"))["fallback_reason"] == "unknown_product"
    assert "overlap" in ok(client.get("/recommendations/collaborative/1/comparison"))
    assert ok(client.get("/recommendations/legacy/1"))["returned"] == 5


def test_day07_08_09(client):
    ev = ok(client.get("/analytics/recommendations?k=5&split_ratio=0.8"))
    assert {r["method"] for r in ev["comparison"]} >= {"popularity", "category", "content", "collaborative"}
    h = ok(client.get("/recommendations/395?limit=5"))
    assert h["method"] == "hybrid" and h["returned"] == 5
    assert ok(client.get("/recommendations/user/395"))["method"] == "hybrid"
    assert ok(client.get("/recommendations/999999"))["fallback_reason"] == "unknown_user"
    rep = ok(client.get("/analytics/recommendations/hybrid?k=5&max_test_users=50"))
    assert rep["comparison"][0]["method"] == "hybrid"
    s = ok(client.get("/recommendations/session/session_005246?limit=5"))
    assert s["method"] == "session"
    assert ok(client.get("/recommendations/session/session_DOESNOTEXIST"))["fallback"] is True
    ok(client.post("/recommendations/events", json={"event_type": "recommendation_impression",
                                                    "user_session": "session_x", "product_id": 1,
                                                    "recommendation_source": "popular",
                                                    "recommendation_position": 1}), 201)
    ok(client.post("/recommendations/events", json={"event_type": "product_view", "product_id": 1}), 422)
    assert ok(client.get("/analytics/recommendations/ctr"))["overall"]["impressions"] == 2000
    assert ok(client.get("/analytics/recommendations/session-comparison"))["n_sessions"] == 200


def test_day10_semantic(client):
    r = ok(client.get("/search/semantic?q=wireless earbuds for travel&limit=3"))
    assert r["results"]
    ok(client.get("/search/semantic?q="), 422)
    assert ok(client.get("/recommendations/semantic/99999?limit=3"))["fallback"] is True
