from fractions import Fraction
import runpy

import pytest

from src.solitude_kaizen.calculator import calculate, run_calculator
from src.solitude_kaizen.memory import ensure_json_file
from src.solitude_kaizen.database import initialize_database


@pytest.mark.parametrize("left,op,right,expected", [
    ("1250.50", "/", "25", "50.02"), ("600", "/", "20", "30"),
    ("900", "+", "0", "900"), ("0.1", "+", "0.2", "0.3"),
    ("1", "/", "3", "1/3"), ("-1", "/", "8", "-0.125"),
    (".5", "*", "0.2", "0.1"), ("5", "-", "7", "-2"),
    ("1", "/", "40", "0.025"), ("-0", "+", "0", "0"),
])
def test_exact_arithmetic(left, op, right, expected):
    assert calculate(left, op, right) == expected


@pytest.mark.parametrize("value", ["nan", "inf", "1e5", "1,000", "60s", "900 pesos", "1/2", "9" * 51, "__import__('os')", "²"])
def test_rejects_nondecimal_inputs(value):
    with pytest.raises(ValueError):
        calculate(value, "+", "1")


def test_division_by_zero_and_unknown_operation():
    with pytest.raises(ValueError, match="zero"):
        calculate("1", "/", "0.0")
    with pytest.raises(ValueError, match="Choose"):
        calculate("1", "**", "2")


def test_results_are_exact_for_a_bounded_number_grid():
    for numerator in range(-12, 13):
        for denominator in range(1, 41):
            assert Fraction(calculate(str(numerator), "/", str(denominator))) == Fraction(numerator, denominator)


@pytest.mark.parametrize("stage", [0, 1, 2])
@pytest.mark.parametrize("cancel", ["", "/CANCEL", EOFError, KeyboardInterrupt])
def test_cancellation_at_every_prompt(stage, cancel):
    answers = iter(["900", "+", "0"][:stage] + [cancel])
    def read(prompt):
        value = next(answers)
        if value in (EOFError, KeyboardInterrupt):
            raise value()
        return value
    assert run_calculator(read, lambda *args: None) == {"status": "canceled"}


def test_menu_calculator_preserves_files_and_chat(tmp_path, monkeypatch, capsys):
    directory = tmp_path / "src" / "solitude_kaizen" / "data"
    paths = [directory / "memories.json", directory / "profile.json", directory / "solitude_kaizen.db"]
    ensure_json_file(paths[0], {"memories": []})
    ensure_json_file(paths[1], {"user_name": "Test"})
    initialize_database(paths[2])
    original = {path: path.read_bytes() for path in paths}
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    def forbidden(*args, **kwargs):
        pytest.fail("Calculator must not access network.")
    monkeypatch.setattr("socket.socket.connect", forbidden)
    answers = iter(["33", "1250.50", "/", "25", "27"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.chdir(tmp_path)
    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    assert "(1250.50) / (25) = 50.02" in capsys.readouterr().out
    assert state["conversation_history"] == []
    assert all(path.read_bytes() == before for path, before in original.items())
