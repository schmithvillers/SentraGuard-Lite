from __future__ import annotations

import json

import cli


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        body: object | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._body = body
        self.text = text

    def json(self) -> object:
        if self._body is None:
            raise ValueError("no JSON body")
        return self._body


def _payload() -> dict:
    return {
        "prompt": "Summarize the report.",
        "context_docs": [],
        "metadata": {
            "app_id": "test-app",
            "user_id": "test-user",
            "request_id": "test-request-1",
        },
    }


def _write_input(tmp_path, payload: object) -> str:
    path = tmp_path / "input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_cli_success_writes_valid_json(tmp_path, monkeypatch) -> None:
    input_path = _write_input(tmp_path, _payload())
    output_path = tmp_path / "out.json"
    captured: dict = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse(
            200,
            {
                "decision": "allow",
                "risk_score": 0,
                "risk_tags": [],
                "sanitized_prompt": "Summarize the report.",
                "sanitized_context_docs": [],
                "reasons": [],
            },
        )

    monkeypatch.setattr(cli.requests, "post", fake_post)
    code = cli.main(
        [
            "analyze",
            "--input",
            input_path,
            "--output",
            str(output_path),
            "--api-base-url",
            "http://api:8000",
        ]
    )
    assert code == 0
    assert captured["url"] == "http://api:8000/analyze"
    assert captured["json"]["prompt"] == "Summarize the report."
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["decision"] == "allow"


def test_cli_http_error_does_not_echo_validation_input(
    tmp_path, monkeypatch, capsys
) -> None:
    input_path = _write_input(tmp_path, _payload())
    output_path = tmp_path / "out.json"

    monkeypatch.setattr(
        cli.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            422,
            {
                "detail": [
                    {
                        "loc": ["body", "prompt"],
                        "msg": "Field required",
                        "input": {"prompt": "secret@example.com"},
                    }
                ]
            },
        ),
    )
    code = cli.main(
        ["analyze", "--input", input_path, "--output", str(output_path)]
    )
    assert code == 1
    error = capsys.readouterr().err
    assert "HTTP 422" in error
    assert "Field required" in error
    assert "secret@example.com" not in error
    assert "input" not in error
    assert not output_path.exists()


def test_cli_connection_error(tmp_path, monkeypatch, capsys) -> None:
    input_path = _write_input(tmp_path, _payload())

    def raise_connection_error(*args, **kwargs):
        raise cli.requests.exceptions.ConnectionError()

    monkeypatch.setattr(cli.requests, "post", raise_connection_error)
    code = cli.main(
        [
            "analyze",
            "--input",
            input_path,
            "--output",
            str(tmp_path / "out.json"),
        ]
    )
    assert code == 1
    assert "could not connect" in capsys.readouterr().err.lower()


def test_cli_invalid_json(tmp_path, capsys) -> None:
    input_path = tmp_path / "bad.json"
    input_path.write_text("{not-json", encoding="utf-8")
    code = cli.main(
        [
            "analyze",
            "--input",
            str(input_path),
            "--output",
            str(tmp_path / "out.json"),
        ]
    )
    assert code == 2
    assert "invalid JSON" in capsys.readouterr().err


def test_cli_missing_input_file(tmp_path, capsys) -> None:
    code = cli.main(
        [
            "analyze",
            "--input",
            str(tmp_path / "missing.json"),
            "--output",
            str(tmp_path / "out.json"),
        ]
    )
    assert code == 2
    assert "not found" in capsys.readouterr().err


def test_cli_rejects_non_object_input(tmp_path, capsys) -> None:
    input_path = _write_input(tmp_path, [])
    code = cli.main(
        [
            "analyze",
            "--input",
            input_path,
            "--output",
            str(tmp_path / "out.json"),
        ]
    )
    assert code == 2
    assert "must be an object" in capsys.readouterr().err


def test_cli_uses_api_base_url_environment_variable(
    tmp_path, monkeypatch
) -> None:
    input_path = _write_input(tmp_path, _payload())
    output_path = tmp_path / "out.json"
    captured: dict = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        return FakeResponse(
            200,
            {
                "decision": "allow",
                "risk_score": 0,
                "risk_tags": [],
                "sanitized_prompt": "ok",
                "sanitized_context_docs": [],
                "reasons": [],
            },
        )

    monkeypatch.setenv("API_BASE_URL", "http://env-api:9000")
    monkeypatch.setattr(cli.requests, "post", fake_post)
    code = cli.main(
        ["analyze", "--input", input_path, "--output", str(output_path)]
    )
    assert code == 0
    assert captured["url"] == "http://env-api:9000/analyze"
