def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["notes"] == []
    assert body["knowledge_base"]["sources"] >= 10
    assert body["knowledge_base"]["graph_edges"] >= 10


def test_health_ready(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_health_reports_degraded_when_knowledge_base_is_empty(monkeypatch, tmp_path):
    # Regression guard for a real bug: seeding can fail (e.g. the seed data
    # wasn't packaged into a deployment) while the database itself stays
    # perfectly reachable. /health must not report "ok" in that case.
    #
    # Calls the health() view function directly against a fully isolated,
    # unseeded temp database -- rather than going through the app's normal
    # startup lifespan (which would auto-seed this fresh database, or
    # mutating the shared session-scoped test database, which other test
    # modules depend on staying intact).
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.base import Base
    import app.main as main_module

    empty_engine = create_engine(f"sqlite:///{tmp_path}/empty.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=empty_engine)
    EmptySessionLocal = sessionmaker(bind=empty_engine, autoflush=False, autocommit=False, future=True)

    monkeypatch.setattr(main_module, "SessionLocal", EmptySessionLocal)

    body = main_module.health()
    assert body["status"] == "degraded"
    assert body["knowledge_base"]["sources"] == 0
    assert any("empty" in n.lower() for n in body["notes"])
