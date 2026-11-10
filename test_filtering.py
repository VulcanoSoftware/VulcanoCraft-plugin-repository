import pytest
import mongomock
from unittest.mock import patch

mongo_patcher = patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

from webserver import (
    _check_category_filter,
    is_plugin_included,
    expand_plugin_categories,
    extract_plugin_categories
)


def test_category_filter_include_and_exclude():
    # 5 plugins in cat1 only
    # 16 plugins in cat2 only
    # 10 plugins in cat1 AND cat2
    plugins = []
    for i in range(5):
        plugins.append({'title': f'Cat1-only {i}', 'categories': ['cat1']})
    for i in range(16):
        plugins.append({'title': f'Cat2-only {i}', 'categories': ['cat2']})
    for i in range(10):
        plugins.append({'title': f'Cat1+Cat2 {i}', 'categories': ['cat1', 'cat2']})

    # Scenario 1: Select cat2 with category_include=True
    inc_cat2 = [p for p in plugins if _check_category_filter(p, 'cat2', category_include=True)]
    exp_inc_cat2 = expand_plugin_categories(inc_cat2, 'cat2', category_include=True)
    assert len(inc_cat2) == 26
    assert len(exp_inc_cat2) == 26

    # Scenario 2: Select cat2 with category_include=False (exclude cat2)
    exc_cat2 = [p for p in plugins if _check_category_filter(p, 'cat2', category_include=False)]
    exp_exc_cat2 = expand_plugin_categories(exc_cat2, 'cat2', category_include=False)
    assert len(exc_cat2) == 15  # 5 cat1-only + 10 cat1+cat2
    assert len(exp_exc_cat2) == 15  # 15 category results displayed (41 total - 26 = 15)

    # Scenario 3: No category selected
    no_cat = [p for p in plugins if _check_category_filter(p, '', category_include=True)]
    exp_no_cat = expand_plugin_categories(no_cat, '', category_include=True)
    assert len(no_cat) == 31
    assert len(exp_no_cat) == 41  # Total expanded entries across all categories is 41


def test_is_plugin_included_category_exclusion():
    plugin_multi = {'title': 'Multi', 'categories': ['cat1', 'cat2'], 'url': ''}
    plugin_cat2 = {'title': 'Cat2', 'categories': ['cat2'], 'url': ''}

    # Excluding cat2
    assert is_plugin_included(plugin_multi, '', '', [], [], 'cat2', include=True, platforms_provided=False, loaders_provided=False, category_include=False) is True
    assert is_plugin_included(plugin_cat2, '', '', [], [], 'cat2', include=True, platforms_provided=False, loaders_provided=False, category_include=False) is False


# ---------------------------------------------------------------------------
# Plugins zonder loaders/platform mogen niet verdwijnen als alle filters aan staan
# ---------------------------------------------------------------------------

ALL_PLATFORMS = ['hangar', 'spigot', 'modrinth', 'curseforge', 'bukkitdev', 'github', 'planetminecraft']
ALL_LOADERS = ['bukkit', 'datapack', 'paper', 'spigot']


def _include(plugin, platforms, loaders, **kwargs):
    return is_plugin_included(
        plugin, '', '', platforms, loaders, '', True,
        ALL_PLATFORMS, ALL_LOADERS, True, True, **kwargs
    )


def test_include_with_all_filters_checked_keeps_plugins_without_loaders():
    # Bijv. een Modrinth-plugin waarvan de fetch (tijdelijk) mislukt is: geen loaders bekend.
    unfetched = {'title': '', 'url': 'https://modrinth.com/plugin/x', 'loaders': []}
    assert _include(unfetched, ALL_PLATFORMS, ALL_LOADERS) is True


def test_include_with_all_filters_checked_keeps_unknown_platform():
    plugin = {'title': 'X', 'url': 'https://example.com/x', 'loaders': ['paper']}
    assert _include(plugin, ALL_PLATFORMS, ALL_LOADERS) is True


def test_include_still_filters_when_a_loader_is_unchecked():
    unfetched = {'title': '', 'url': 'https://modrinth.com/plugin/x', 'loaders': []}
    paper_only = {'title': 'P', 'url': 'https://modrinth.com/plugin/p', 'loaders': ['paper']}
    spigot_only = {'title': 'S', 'url': 'https://modrinth.com/plugin/s', 'loaders': ['spigot']}
    selected = ['paper', 'spigot', 'bukkit']  # 'datapack' uitgevinkt
    assert _include(unfetched, ALL_PLATFORMS, selected) is False
    assert _include(paper_only, ALL_PLATFORMS, selected) is True
    assert _include(spigot_only, ALL_PLATFORMS, ['paper']) is False


def test_include_still_filters_when_a_platform_is_unchecked():
    plugin = {'title': 'G', 'url': 'https://github.com/a/b', 'loaders': ['bukkit']}
    assert _include(plugin, [p for p in ALL_PLATFORMS if p != 'github'], ALL_LOADERS) is False
    assert _include(plugin, ['github'], ALL_LOADERS) is True


def test_exclude_mode_is_unchanged():
    with_loader = {'title': 'A', 'url': 'https://modrinth.com/plugin/a', 'loaders': ['paper']}
    without_loader = {'title': 'B', 'url': 'https://modrinth.com/plugin/b', 'loaders': []}
    kwargs = dict(all_platforms=ALL_PLATFORMS, all_loaders=ALL_LOADERS, platforms_provided=False, loaders_provided=True)
    assert is_plugin_included(with_loader, '', '', [], ALL_LOADERS, '', False, **kwargs) is False
    assert is_plugin_included(without_loader, '', '', [], ALL_LOADERS, '', False, **kwargs) is True
