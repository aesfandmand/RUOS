"""The motion verb inventory (design model §21) must stay honest.

A rule nobody can check is a rule that gets violated. These tests check the
three things that silently rot: a verb losing its failure plan, a reference
file being renamed out from under the YAML, and a score that breaks the very
adjacency law it exists to encode.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "05-rules" / "website" / "motion-verbs-v1.yaml"

REQUIRED_VERB_FIELDS = {
    "id",
    "fa",
    "family",
    "what",
    "reference",
    "use_for",
    "max_per_page",
    "cost",
    "mobile",
    "reduced_motion",
    "fails_open",
    "library",
}

HEAVY = "heavy"


@pytest.fixture(scope="module")
def spec() -> dict:
    assert SPEC.exists(), f"missing {SPEC.relative_to(REPO)}"
    return yaml.safe_load(SPEC.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def verbs(spec: dict) -> dict:
    return {v["id"]: v for v in spec["verbs"]}


def test_every_verb_declares_how_it_fails(verbs: dict) -> None:
    """§21: mobile, reduced_motion and fails_open are required, not optional."""
    for vid, verb in verbs.items():
        missing = REQUIRED_VERB_FIELDS - set(verb)
        assert not missing, f"verb {vid!r} is missing {sorted(missing)}"
        for field in ("mobile", "reduced_motion", "fails_open"):
            assert str(verb[field]).strip(), f"verb {vid!r} has an empty {field}"


def test_verb_families_are_declared(spec: dict, verbs: dict) -> None:
    known = set(spec["families"])
    for vid, verb in verbs.items():
        assert verb["family"] in known, (
            f"verb {vid!r} claims family {verb['family']!r}, "
            f"which is not in the families table"
        )


def test_every_reference_file_exists(verbs: dict) -> None:
    """A renamed clip must not leave a verb pointing at nothing."""
    root = REPO / "reference" / "motion-strategy-references"
    for vid, verb in verbs.items():
        for ref in verb["reference"]:
            # paths are either relative to the motion folder or to the repo
            candidates = (root / ref, REPO / ref)
            assert any(p.exists() for p in candidates), (
                f"verb {vid!r} references {ref!r}, which is on disk nowhere"
            )


def test_cost_is_one_of_the_three_levels(verbs: dict) -> None:
    for vid, verb in verbs.items():
        assert verb["cost"] in {"light", "medium", HEAVY}, (
            f"verb {vid!r} has cost {verb['cost']!r}"
        )


def test_scores_obey_rule_one_no_verb_twice(spec: dict) -> None:
    for name, score in spec["scores"].items():
        used = score["verbs"]
        assert len(used) == len(set(used)), (
            f"score {name!r} repeats a verb — §21 rule 1"
        )


def test_scores_obey_rule_two_no_adjacent_family(spec: dict, verbs: dict) -> None:
    for name, score in spec["scores"].items():
        families = [verbs[v]["family"] for v in score["verbs"]]
        for i in range(len(families) - 1):
            assert families[i] != families[i + 1], (
                f"score {name!r} puts two {families[i]!r} verbs "
                f"next to each other ({score['verbs'][i]} → "
                f"{score['verbs'][i + 1]}) — §21 rule 2"
            )


def test_scores_obey_rule_four_one_heavy_verb(spec: dict, verbs: dict) -> None:
    for name, score in spec["scores"].items():
        heavy = [v for v in score["verbs"] if verbs[v]["cost"] == HEAVY]
        assert len(heavy) <= 1, (
            f"score {name!r} carries {len(heavy)} heavy verbs ({heavy}) — §21 rule 4"
        )
        assert score["heavy_count"] == len(heavy), (
            f"score {name!r} declares heavy_count={score['heavy_count']} "
            f"but actually uses {len(heavy)}"
        )


def test_scores_name_only_known_verbs(spec: dict, verbs: dict) -> None:
    for name, score in spec["scores"].items():
        for vid in score["verbs"]:
            assert vid in verbs, f"score {name!r} names unknown verb {vid!r}"


def test_cursor_states_are_pointer_only_and_documented(spec: dict) -> None:
    cursor = spec["cursor"]
    assert cursor["pointer_only"] is True, (
        "§21: the custom cursor is never rendered on touch"
    )
    ids = [s["id"] for s in cursor["states"]]
    assert "default" in ids, "the native arrow must remain a declared state"
    assert len(ids) == len(set(ids)), "duplicate cursor state"
    for state in cursor["states"]:
        assert state.get("shape", "").strip(), f"cursor state {state['id']!r} has no shape"
        assert state.get("where", "").strip(), f"cursor state {state['id']!r} has no home"


def test_every_score_has_a_cursor_arc(spec: dict) -> None:
    known = {s["id"] for s in spec["cursor"]["states"]}
    for name, score in spec["scores"].items():
        arc = score["cursor_arc"]
        assert arc, f"score {name!r} has no cursor arc"
        assert arc[0] == "default", (
            f"score {name!r} must start on the native cursor"
        )
        unknown = set(arc) - known
        assert not unknown, f"score {name!r} uses undeclared cursor states {sorted(unknown)}"
