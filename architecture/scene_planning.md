# Scene Planning SOP

**Layer**: 1 (Architecture)  
**Service**: `backend/app/services/scene_planner.py`  
**Last Updated**: 2026-02-12

---

## Goal

Generate deterministic, age-appropriate scene descriptions and image prompts for coloring book pages. Zero API cost, pure logic-based planning.

---

## Input

- `theme` (string): User's story theme (e.g., "space adventure")
- `page_count` (int): Number of pages to generate (4-12)
- `art_style` (ArtStyle enum): `simple | standard | detailed`
- `age_range` (AgeRange enum): `4-6 | 7-9 | 10-12`
- `character_name` (string | None): Optional custom character name

---

## Output

- `scenes` (list[dict]): Ordered list of scene dictionaries, each containing:
  - `page_number` (int): 1-indexed page number
  - `description` (string): Human-readable scene description
  - `image_prompt` (string): Complete prompt for fal.ai

---

## Process

### Step 1: Select Art Style Hint

Based on `art_style`, inject complexity instructions into prompts:

**Simple** (ages 4-6):
- "very thick black outlines, large simple shapes, minimal detail"
- "no cross-hatching, no small features, suitable for toddlers"

**Standard** (ages 7-9):
- "clean black outlines, moderate detail, standard coloring book style"
- "clear regions to color, no shading"

**Detailed** (ages 10-12):
- "fine black lines, intricate details, patterns inside shapes"
- "suitable for older children, no shading or gray fills"

### Step 2: Generate Story Arc

Use pre-defined arc templates to create narrative flow:

**Available Templates** (12 total):
1. Introduction of character in home setting
2. Character discovers something magical and sets off
3. Character meets friendly creature or companion
4. Character faces challenge or puzzle
5. Character works with friends to solve problem
6. Character celebrates success
7. Character shares learnings with family
8. Quiet evening reflection
9. Surprise twist to new location
10. Character uses special skill to help someone
11. Group picnic or celebration
12. Peaceful final scene back at home

**Selection Algorithm**:
- Distribute templates evenly across requested `page_count`
- Formula: `round(i * (total_templates - 1) / (page_count - 1))`
- **Rationale**: Ensures narrative arc with proper beginning/middle/end

**Example**: For 8 pages, select templates at indices: [0, 1, 3, 5, 7, 9, 10, 11]

### Step 3: Build Scene Descriptions

For each selected arc template:

1. **Format Template** with character name:
   - Default: "the main character"
   - Custom: User-provided name
   - Example: "introduction of {name} in their home setting" → "introduction of Luna in their home setting"

2. **Create Description**:
   - Format: `"Page {n}: {arc_desc} — themed around: {theme}"`
   - Example: `"Page 1: introduction of Luna in their home setting — themed around: space adventure"`

3. **Build Image Prompt**:
   - Base: "Black and white coloring book page."
   - Arc: Formatted arc description
   - Theme: `"Theme: {theme}."`
   - Style: Art style hint
   - Technical: "Pure white background, only black outlines, no gray fills, no shading, no text"
   - Age: `"print-ready coloring page for age {age_range}"`

**Example Prompt**:
```
Black and white coloring book page. introduction of Luna in their home setting. Theme: space adventure. clean black outlines, moderate detail, standard coloring book style, clear regions to color, no shading. Pure white background, only black outlines, no gray fills, no shading, no text, print-ready coloring page for age 7-9.
```

### Step 4: Return Ordered Scenes

- Scenes maintain page number order (1-indexed)
- Each scene ready for immediate image generation
- No additional processing needed

---

## Edge Cases

### Variable Page Counts
- **4 pages**: Minimal arc (intro, adventure, challenge, resolution)
- **8 pages**: Balanced arc (full narrative)
- **12 pages**: Extended arc (all templates used)

### Character Name Variations
- **None provided**: Use "the main character"
- **Empty string**: Use "the main character"
- **Custom name**: Use as-is (e.g., "Luna", "Max", "Princess Stella")

### Theme Variations
- **Short theme**: "pirates" → Still generates full narrative
- **Long theme**: "underwater adventure with dolphins and coral reefs" → Incorporated into all prompts
- **Multiple words**: Properly included in scene context

---

## Performance Requirements

- **Execution Time**: < 500ms (pure Python logic)
- **No API Calls**: Zero external dependencies
- **Deterministic**: Same inputs always produce same output

---

## Constants

### Art Style Hints
- Stored in `_STYLE_HINTS` dictionary
- Keys: `ArtStyle.simple`, `ArtStyle.standard`, `ArtStyle.detailed`

### Story Arc Templates
- Stored in `_ARC_TEMPLATES` list (12 templates)
- Ordered for narrative flow
- Designed for child-friendly stories

---

## Dependencies

- `app.models.book.ArtStyle` enum
- `app.models.book.AgeRange` enum
- No external API dependencies

---

## Testing Checklist

- [ ] Test 4-page, 8-page, and 12-page generation
- [ ] Verify arc distribution algorithm for each page count
- [ ] Test all 3 art styles produce different prompts
- [ ] Test all 3 age ranges in final prompt
- [ ] Test with custom character name vs None
- [ ] Verify prompt format matches fal.ai requirements
- [ ] Ensure no gray fills or shading mentioned

---

## Maintenance Notes

### When to Add Arc Templates
- ✏️ User feedback: "Stories feel repetitive"
- ✏️ New narrative patterns identified
- ⚠️ Always maintain 12+ templates for good distribution

### When to Update Style Hints
- ✏️ Generated images don't match expected complexity
- ✏️ fal.ai model updates require different prompting
- ✏️ User feedback on age-appropriateness

### When to Adjust Technical Instructions
- ✏️ Images have gray fills despite "no shading" instruction
- ✏️ Text appears in images despite "no text" instruction
- ⚠️ Always include "Pure white background" to ensure coloring compatibility

---

## Related SOPs

- [Image Generation](image_generation.md) — Consumes scene prompts
- [Content Safety](content_safety.md) — Validates theme before planning
- [API Endpoint: Generate Book](../routers/books.md) — Orchestrates planning + generation
