import pytest
from app.services.content_filter import _layer1_check


def test_safe_prompt_passes():
    safe, reason = _layer1_check("A cute bunny explores the magical forest")
    assert safe is True
    assert reason == ""


def test_blocked_violence():
    safe, reason = _layer1_check("A child with a gun shooting monsters")
    assert safe is False
    assert "gun" in reason


def test_blocked_adult():
    safe, reason = _layer1_check("An adult party with wine and beer")
    assert safe is False


def test_safe_adventure():
    safe, _ = _layer1_check("Luna the dragon goes on an adventure to find treasure")
    assert safe is True


def test_safe_animals():
    safe, _ = _layer1_check("Three puppies playing in the garden with butterflies")
    assert safe is True


def test_blocked_drugs():
    safe, reason = _layer1_check("Characters smoking cigarettes at a party")
    assert safe is False


def test_case_insensitive():
    safe, reason = _layer1_check("A scene with VIOLENCE and chaos")
    assert safe is False
