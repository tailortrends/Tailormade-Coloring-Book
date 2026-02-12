import pytest
from app.services.scene_planner import plan_scenes
from app.models.book import ArtStyle, AgeRange


def test_plan_scenes_returns_correct_count():
    scenes = plan_scenes("space adventure", 6, ArtStyle.standard, AgeRange.kids)
    assert len(scenes) == 6


def test_plan_scenes_page_numbers_sequential():
    scenes = plan_scenes("ocean friends", 4, ArtStyle.simple, AgeRange.toddler)
    for i, s in enumerate(scenes, 1):
        assert s["page_number"] == i


def test_plan_scenes_injects_character_name():
    scenes = plan_scenes("forest adventure", 3, ArtStyle.standard, AgeRange.kids, "Luna")
    for s in scenes:
        assert "Luna" in s["description"] or "Luna" in s["image_prompt"]


def test_plan_scenes_default_name():
    scenes = plan_scenes("jungle safari", 3, ArtStyle.standard, AgeRange.kids)
    assert "the main character" in scenes[0]["image_prompt"]


def test_plan_scenes_style_hints_in_prompt():
    scenes_simple = plan_scenes("test", 2, ArtStyle.simple, AgeRange.toddler)
    assert "thick" in scenes_simple[0]["image_prompt"].lower()

    scenes_detailed = plan_scenes("test", 2, ArtStyle.detailed, AgeRange.tweens)
    assert "intricate" in scenes_detailed[0]["image_prompt"].lower()


def test_plan_scenes_all_have_required_keys():
    scenes = plan_scenes("dragons", 6, ArtStyle.standard, AgeRange.kids)
    for s in scenes:
        assert "page_number" in s
        assert "description" in s
        assert "image_prompt" in s


def test_plan_scenes_prompt_contains_bw_keywords():
    scenes = plan_scenes("princess castle", 2, ArtStyle.standard, AgeRange.kids)
    prompt = scenes[0]["image_prompt"].lower()
    assert "black and white" in prompt or "coloring book" in prompt


def test_plan_scenes_min_pages():
    scenes = plan_scenes("test", 2, ArtStyle.simple, AgeRange.toddler)
    assert len(scenes) == 2


def test_plan_scenes_max_pages():
    scenes = plan_scenes("test", 12, ArtStyle.detailed, AgeRange.tweens)
    assert len(scenes) == 12
