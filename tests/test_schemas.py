"""Schemas: the data model rejects malformed production data."""
import pytest
from pydantic import ValidationError

from fm.schemas import EXPORTED, BriefField, CanonEntry, CanonFile, ShotSpec, Status


def test_canon_id_format():
    CanonEntry(id="look.color.primary", statement="x")
    for bad in ("Look.color", "color", "look..x", "look.Color Primary"):
        with pytest.raises(ValidationError):
            CanonEntry(id=bad, statement="x")


def test_serves_must_reference_intent():
    with pytest.raises(ValidationError, match="intent"):
        CanonEntry(id="look.color.primary", statement="x", serves=["tone.register"])


def test_canon_file_domain_enforced():
    with pytest.raises(ValidationError, match="not in domain"):
        CanonFile(domain="look", entries=[{"id": "story.premise", "statement": "x"}])
    with pytest.raises(ValidationError, match="unknown canon domain"):
        CanonFile(domain="vibes", entries=[])


def test_default_lifecycle_is_proposed():
    assert CanonEntry(id="story.premise", statement="x").status == Status.PROPOSED


def test_intent_separate_from_implementation_hash():
    """Hash covers the decision, not bookkeeping (status/version/history/source)."""
    from fm.project import canon_hash
    a = CanonEntry(id="look.color.primary", statement="Blue", value="#1B2A3A", rationale="cold")
    b = a.model_copy(update={"status": Status.LOCKED, "version": 3, "source": "human:x"})
    c = a.model_copy(update={"value": "#1B2A3B"})
    assert canon_hash(a) == canon_hash(b)
    assert canon_hash(a) != canon_hash(c)


def test_shot_id_and_scene_must_agree():
    ShotSpec(shot_id="SC01_SH010", scene_id="SC01", duration_s=3)
    with pytest.raises(ValidationError, match="does not belong"):
        ShotSpec(shot_id="SC01_SH010", scene_id="SC02", duration_s=3)
    with pytest.raises(ValidationError):
        ShotSpec(shot_id="shot1", scene_id="SC01", duration_s=3)


def test_shot_reserves_creative_intent_and_rationale():
    s = ShotSpec(shot_id="SC01_SH010", scene_id="SC01", duration_s=3,
                 creative_intent={"narrative_purpose": "a", "emotional_purpose": "b",
                                  "visual_purpose": "c", "audience_effect": "d"},
                 rationale={"camera": "why", "lighting": "why", "composition": "why",
                            "movement": "why"})
    assert s.creative_intent.audience_effect == "d"
    assert s.rationale.movement == "why"


def test_shot_rejects_unknown_fields_and_bad_lens():
    with pytest.raises(ValidationError):
        ShotSpec(shot_id="SC01_SH010", scene_id="SC01", duration_s=3, mood="sad")
    with pytest.raises(ValidationError):
        ShotSpec(shot_id="SC01_SH010", scene_id="SC01", duration_s=3, camera={"lens_mm": 2})


def test_brief_field_status_consistency():
    BriefField(value=None, status="unknown")
    with pytest.raises(ValidationError):
        BriefField(value=None, status="given")


def test_json_schema_export_is_model_independent(tmp_path):
    for name, model in EXPORTED.items():
        schema = model.model_json_schema()
        assert schema["type"] == "object", name
        assert "properties" in schema
