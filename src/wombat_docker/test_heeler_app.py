import heeler_app


def test_execute_runs_validator_mode(monkeypatch) -> None:
    class FakeValidator:
        def __init__(self, _postgres):
            pass

        def execute(self) -> int:
            return 0

    monkeypatch.setattr(heeler_app, "HeelerValidator", FakeValidator)

    app = heeler_app.HeelerApp("validator")

    assert app.execute() == 0


def test_execute_runs_koala_mode(monkeypatch) -> None:
    class FakeKoala:
        def execute(self) -> None:
            return None

    monkeypatch.setattr(heeler_app, "Koala", FakeKoala)

    app = heeler_app.HeelerApp("koala")

    assert app.execute() == 0


def test_execute_rejects_invalid_mode() -> None:
    app = heeler_app.HeelerApp("bad-mode")

    assert app.execute() == 1
