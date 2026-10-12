"""Tests for :class:`surface_navigator.player_location.NavigationUtils`.

Kept separate from the GUI tests so the math helpers live next to their own
behaviour.
"""

from surface_navigator.player_location import NavigationUtils


def test_clean_body_name_strips_system_prefix():
    """Spansh prefixes every body/ring with its parent system.

    "Blaa Eork OH-U d3-1 4 A Ring" -> "4 A Ring".
    """
    assert (
        NavigationUtils.clean_body_name("Blaa Eork OH-U d3-1", "Blaa Eork OH-U d3-1 4 A Ring")
        == "4 A Ring"
    )


def test_clean_body_name_leaves_unprefixed_name_untouched():
    """A name that does not start with the system name is returned as-is."""
    assert NavigationUtils.clean_body_name("Sol", "Proxima b") == "Proxima b"


def test_clean_body_name_handles_exact_match():
    """When the raw name equals the system name exactly, nothing is left."""
    assert NavigationUtils.clean_body_name("Sol", "Sol") == "Sol"


def test_clean_body_name_prefix_only_matches_on_word_boundary():
    """"Sol" must not strip the "Sol" out of "Solaris" -- it needs the space."""
    assert NavigationUtils.clean_body_name("Sol", "Solaris b") == "Solaris b"
