"""Helpers for tests that inspect a page's own content."""

import re

SITE_HEADER = re.compile(
    r'<header class="topbar site-header">.*?</header>', flags=re.DOTALL
)


def without_site_header(response):
    """Return the page's HTML with the shared site header removed.

    The header carries the account menu's log-out form on every page, so
    tests about a page's own forms and buttons look at the rest of it.
    """
    return SITE_HEADER.sub("", response.content.decode())
