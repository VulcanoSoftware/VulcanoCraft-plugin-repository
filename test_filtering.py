import pytest
import mongomock
from unittest.mock import patch

with patch('pymongo.MongoClient', mongomock.MongoClient):
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
