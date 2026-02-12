from app.models.book import ArtStyle, AgeRange

# Complexity hints per art style — injected into fal.ai prompts
_STYLE_HINTS: dict[ArtStyle, str] = {
    ArtStyle.simple: (
        "very thick black outlines, large simple shapes, minimal detail, "
        "no cross-hatching, no small features, suitable for toddlers"
    ),
    ArtStyle.standard: (
        "clean black outlines, moderate detail, standard coloring book style, "
        "clear regions to color, no shading"
    ),
    ArtStyle.detailed: (
        "fine black lines, intricate details, patterns inside shapes, "
        "suitable for older children, no shading or gray fills"
    ),
}

# Story arc templates — scenes are generated deterministically, zero API cost
_ARC_TEMPLATES = [
    "introduction of {name} in their home setting",
    "{name} discovers something magical and sets off on an adventure",
    "{name} meets a friendly creature or companion",
    "{name} faces a challenge or puzzle",
    "{name} works together with new friends to solve the problem",
    "{name} celebrates their success with everyone",
    "{name} shares what they learned with family",
    "a quiet evening as {name} reflects on the journey",
    "a surprise twist sends {name} to a new location",
    "{name} uses a special skill to help someone",
    "the whole group goes on a picnic or celebration",
    "a peaceful final scene with {name} back at home",
]


def plan_scenes(
    theme: str,
    page_count: int,
    art_style: ArtStyle,
    age_range: AgeRange,
    character_name: str | None = None,
) -> list[dict]:
    """
    Build page-by-page scene descriptions from a theme.
    Returns a list of dicts with keys: page_number, description, image_prompt.
    No external API calls — pure logic.
    """
    name = character_name or "the main character"
    style_hint = _STYLE_HINTS[art_style]

    # Pick arc steps evenly distributed across requested page count
    arc_count = len(_ARC_TEMPLATES)
    indices = [round(i * (arc_count - 1) / (page_count - 1)) for i in range(page_count)]
    selected_arcs = [_ARC_TEMPLATES[i] for i in indices]

    scenes = []
    for i, arc_template in enumerate(selected_arcs):
        arc_desc = arc_template.format(name=name)
        description = f"Page {i + 1}: {arc_desc} — themed around: {theme}"

        # This is the actual prompt sent to fal.ai
        image_prompt = (
            f"Black and white coloring book page. "
            f"{arc_desc}. Theme: {theme}. "
            f"{style_hint}. "
            f"Pure white background, only black outlines, no gray fills, no shading, "
            f"no text, print-ready coloring page for age {age_range}."
        )

        scenes.append(
            {
                "page_number": i + 1,
                "description": description,
                "image_prompt": image_prompt,
            }
        )

    return scenes
