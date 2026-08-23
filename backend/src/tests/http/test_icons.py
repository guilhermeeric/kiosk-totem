from src.http.icons import icon_svg


def test_icon_svg_returns_svg_for_known_key():
    svg = icon_svg("coffee")
    assert svg is not None
    assert svg.startswith("<svg")
    assert "☕" in svg


def test_icon_svg_returns_none_for_unknown_key():
    assert icon_svg("pizza") is None
