"""Item icon resolution: the DB stores a KEY, this module resolves it to a
renderable glyph (emoji wrapped in SVG). When real food photos arrive, the
key points at a media path instead and this endpoint serves that file."""

ICONS: dict[str, str] = {
    "coffee": "☕",
    "iced-tea": "🧋",
    "lemonade": "🍋",
    "chocolate-cake": "🍰",
    "cheesecake": "🍮",
    "cookie": "🍪",
    "burger": "🍔",
    "wrap": "🌯",
    "fries": "🍟",
    "plate": "🍽️",
}


def icon_svg(key: str) -> str | None:
    """Return an SVG rendering the emoji for the key, or None if unknown."""
    emoji = ICONS.get(key)
    if emoji is None:
        return None
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<text x="50" y="52" font-size="64" text-anchor="middle" '
        f'dominant-baseline="central">{emoji}</text></svg>'
    )
