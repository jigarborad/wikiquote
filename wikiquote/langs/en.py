from typing import List, Text, Tuple

import lxml

from .. import utils

WORD_BLOCKLIST = ["quoted", "Variant:", "Retrieved", "Notes:", "article:"]
MAIN_PAGE = "Main Page"
HEADINGS = ["cast", "see also", "external links", "about"]


def extract_quotes(tree: lxml.html.HtmlElement, max_quotes: int) -> List[Text]:
    q_lst = utils.extract_quotes_li(tree, max_quotes, HEADINGS, WORD_BLOCKLIST)
    return [utils.remove_credit(q) for q in q_lst]


def qotd(html_tree: lxml.html.HtmlElement) -> Tuple[Text, Text]:
    tree = html_tree.get_element_by_id("mf-qotd")

    selector = "div/div/table/tbody/tr"
    # Improvement 1: Handle potential layout changes with multiple selectors

    # We currently rely on a single XPath selector to retrieve the quote of the day (QOTD).
    # This might become fragile if the website structure changes.

    # To improve robustness, consider the following:

    # 1. Define multiple alternative selectors targeting different parts of the HTML structure
    #    where the QOTD might be located. Analyze the website to identify these variations.

    # 2. Loop through the list of selectors one by one.
    #    - For each selector, attempt to extract the QOTD using XPath.
    #    - If successful (e.g., extracted text content is not empty), return the quote and author.

    # 3. If none of the selectors are successful, handle the failure gracefully (e.g., log an error).

    # This approach increases the likelihood of retrieving the QOTD even if the layout changes.n.

    raw_quote = tree.xpath(selector)[0].text_content().split("~")
    quote = raw_quote[0].strip()
    author = raw_quote[1].strip()
    return quote, author
