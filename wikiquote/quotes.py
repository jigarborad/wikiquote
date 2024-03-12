from typing import Any, Dict, List, Text

import lxml.html

from . import langs, utils
from .constants import DEFAULT_LANG, DEFAULT_MAX_QUOTES, PAGE_URL, RANDOM_URL, SRCH_URL


def _is_disambiguation(categories: List[Dict[Text, Any]]) -> bool:
    # Checks to see if at least one category includes 'Disambiguation_pages'
    return not categories or any(
        [category["*"] == "Disambiguation_pages" for category in categories]
    )


@utils.validate_lang
def search(s: Text, lang: Text = DEFAULT_LANG) -> List[Text]:
    if not s:
        return []

    local_srch_url = SRCH_URL.format(lang=lang)
    data = utils.json_from_url(local_srch_url, s)
    results = [entry["title"] for entry in data["query"]["search"]]
    return results


@utils.validate_lang
def random_titles(
    lang: Text = DEFAULT_LANG, max_titles: int = DEFAULT_MAX_QUOTES
) -> List[Text]:
    local_random_url = RANDOM_URL.format(lang=lang, limit=max_titles)
    data = utils.json_from_url(local_random_url)
    results = [entry["title"] for entry in data["query"]["random"]]
    return results


@utils.validate_lang
def quotes(
    page_title: Text, max_quotes: int = DEFAULT_MAX_QUOTES, lang: Text = DEFAULT_LANG
) -> List[Text]:
    # Improvement 2: Provide functionality for retrieving a random quote

    # The current functionality retrieves all quotes from a given page.

    # Here's how we can improve:

    # 1. Add a new optional parameter `random` (defaulting to False).
    #    - If `random` is True, the function should return a single random quote
    #      from the extracted quotes.
    #    - If `random` is False (default), the function continues to return
    #      all extracted quotes.

    # 2. Extract all quotes using the existing logic.

    # 3. If `random` is True:
    #    - Use built-in Python functionalities to select a random quote from the extracted list.
    #      - We can use techniques like `choice` from the `random` module (imported internally)
    #        or list indexing with a random number within the list range.
    #    - Return the single random quote.

    # This improvement offers users the flexibility to retrieve either all quotes
    # or a single random quote from the specified page, without requiring them
    # to import the `random` library themselves.

    local_page_url = PAGE_URL.format(lang=lang)
    data = utils.json_from_url(local_page_url, page_title)
    if "error" in data:
        raise utils.NoSuchPageException("No pages matched the title: " + page_title)

    if _is_disambiguation(data["parse"]["categories"]):
        raise utils.DisambiguationPageException("Title returned a disambiguation page.")

    html_content = data["parse"]["text"]["*"]
    html_tree = lxml.html.fromstring(html_content)
    return langs.extract_quotes_lang(lang, html_tree, max_quotes)
