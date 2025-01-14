import json
import re
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Text, TypeVar

try:
    import lxml

    lxml.html
except AttributeError:
    import lxml.html

from . import langs
from .constants import MIN_QUOTE_LEN, MIN_QUOTE_WORDS

T = TypeVar("T")


class NoSuchPageException(Exception):
    pass


class DisambiguationPageException(Exception):
    pass


class UnsupportedLanguageException(Exception):
    pass


class MissingQOTDException(Exception):
    pass


def json_from_url(url: Text, params: Optional[Text] = None) -> Dict[Text, Any]:
    """
    Given a URL that returns JSON, returns a Python dictionary of the parsed JSON by
    making an HTTP GET request to the url with the given params.

    :param url: The URL to retrieve
    :param params: The parameters to pass to the URL
    :return: A Python dictionary of the parsed JSON
    """
    if params:
        url += urllib.parse.quote(params)
    res = urllib.request.urlopen(url)
    body = res.read().decode("utf-8")
    return json.loads(body)


def validate_lang(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator function to validate the language parameter of a function by checking if
    it is in SUPPORTED_LANGUAGES.

    :param fn: The function to decorate
    :return: The decorated function
    """

    def internal(*args: Any, **kwargs: Any) -> T:
        """Helper function to validate the language parameter of a function."""
        lang = kwargs.get("lang")
        if lang and lang not in langs.SUPPORTED_LANGUAGES:
            raise UnsupportedLanguageException("Unsupported language: {}".format(lang))

        return fn(*args, **kwargs)

    return internal


def remove_credit(quote: Text) -> Text:
    """
    Remove credits from a wikiquote quote if they exist. Credits are denoted by a dash
    or em dash at the end of the quote.

    :param quote: The quote to remove credits from
    :return: The quote with credits removed
    """
    if quote.endswith(("–", "-")):
        quote = quote[:-1].rstrip()
    return quote


# ==================================================================================================
# Extract Functions
# ==================================================================================================


def extract_quotes_li(
    tree: lxml.html.HtmlElement,
    max_quotes: int,
    headings: Optional[List[Text]] = None,
    word_blacklist: Optional[List[Text]] = None,
) -> List[Text]:
    """
    Extract quotes from a list of list items and return them as a list. This function
    will only extract quotes from the first max_quotes list items.

    :param tree: The HTML tree to extract quotes from.
    :param max_quotes: The maximum number of quotes to extract.
    :param headings: A list of headings to skip.
    :param word_blacklist: A list of words to blacklist (skip quotes containing these
    words).
    :return: A list of quotes, e.g. ["Quote 1", "Quote 2", ...].
    """
    remove_toc(tree)  # Remove table of contents
    quotes_list = []
    skip_to_next_heading = bool(tree.xpath("//h2|//h3"))
    node_list = tree.xpath("//div/ul/li|//div/dl|//h2|//h3")

    # Iterate through the list items and description list tags
    # node is a list item or description list tag, e.g.) <li> Quote </li>
    for node in node_list:
        if node.tag in ["h2", "h3"]:
            skip_to_next_heading = check_skip_heading(node, headings or [])
            continue
        elif skip_to_next_heading:
            continue

        # Potential quote is the first child node of the list item
        potential_quote = extract_potential_quote(node)
        if potential_quote and is_quote(potential_quote, word_blacklist or []):
            quotes_list.append(potential_quote)
            if max_quotes == len(quotes_list):
                break
    return quotes_list


# TODO: Add features to extract author pages, disambiguation pages, and other pages

# Improvement: Extracting Author Pages

# We've identified a potential optimization in the `quotes()` function within `quotes.py`.
# The current approach to extracting quotes might be adaptable to retrieve author pages.

# Here's the reasoning:

# 1. Similarities to Quote Extraction:
#    - The logic behind finding the `page_title` variable in `quotes()` might be applicable
#      to locating a specific `page_title` that signifies author pages.

# 2. Identifying Author Page Pattern:
#    - Author pages on Wikiquote often follow a consistent URL structure.
#      - The English version uses `https://en.wikiquote.org/wiki/Category:Authors`.
#      - Other languages may have similar patterns but in their respective languages
#        (e.g., German: `https://de.wikiquote.org/wiki/Kategorie:Person`).

# 3. Leveraging Existing Functionality:
#    - Instead of implementing a completely new mechanism, we can potentially
#      reuse the existing structure of the `quotes()` function.

# Proposed Approach:

# A. Define Specific Page Title:
#    - We'll need to determine the precise `page_title` that indicates author pages
#      (e.g., "Category:Authors" or its equivalent in different languages).

# B. Modify `quotes()` Function:
#    - Within `quotes()` (or a related function if more suitable), we can check if
#      the extracted `page_title` matches the defined author page title.
#    - If it does, we can perform the necessary actions to extract author information
#      instead of quote data.

# C. Flexibility for Different Languages:
#    - The code should be adaptable to handle variations in the author page title
#      across different languages. This might involve using a mapping or dictionary
#      to associate language codes with their corresponding author page title patterns.

# D. Potential Challenges:
#    - The HTML structure of Wikiquote pages might change, potentially affecting
#      the reliability of relying solely on the `page_title` for identification.
#      We may need to consider additional parsing techniques for robustness.

# By refining the existing code and addressing potential issues, we can achieve efficient
# author page extraction while maintaining code maintainability and future-proofing
# against potential website changes.


#---------------------------------------------------------------------------------------------------------

# Improvement 2: Offline Data Backup (Optional)

# While the current implementation relies on the Wikiquote API, we can consider incorporating an optional fallback
# mechanism using an offline dataset in case the API becomes unavailable.

# This would provide increased resilience against API outages. An example dataset is available at:
# https://www.kaggle.com/code/kerneler/starter-wikiquote-en-simplified-a2e29c89-c/input (English dataset)

# However, there are considerations:

# - Offline datasets might not be as up-to-date as the online API.
# - Extracting "Quote of the Day" might not be feasible with offline data.
# - Managing offline data could introduce additional complexity.

# The decision to include an offline backup depends on the trade-off between resilience and complexity
# within your specific use case.

#---------------------------------------------------------------------------------------------------------

# Improvement 3: Enhanced Quote Extraction 

# We can potentially improve the accuracy of extracted quotes by considering the structure of Wikiquote pages.

# Sometimes, entire text blocks or bullet points are mistakenly identified as quotes instead of the intended,
# smaller quote segments within those blocks. Not all authors or languages exhibit this behavior.

# A possible approach is to heuristically identify quotes based on their presence within **<b>** tags (bold formatting).
# This approach might require further refinement depending on specific website structures.

# This improvement aims to enhance the quality of extracted quotes by providing a more precise representation
# of the intended quotes. However, it's important to acknowledge that this heuristic approach might not be
# foolproof and could require adjustments based on language-specific website structures. Consider evaluating
# its effectiveness for your use case.


# ===================================================================================================
# Helper functions to extract_quotes_li
# ===================================================================================================


def remove_toc(tree: lxml.html.HtmlElement) -> None:
    """
    Remove the table of contents from the given HTML tree.

    :param tree: The HTML tree.
    """
    for toc in tree.xpath('//div[@id="toc"]'):
        toc.getparent().remove(toc)


def check_skip_heading(node: lxml.html.HtmlElement, headings: List[Text]) -> bool:
    """
    Determine if we should skip the quotes under a given heading.

    :param node: The heading node.
    :param headings: List of headings to be checked.
    :return: True if the heading indicates skipping, False otherwise.
    """
    return any(
        node.text_content().lower().startswith(unwanted.lower())
        for unwanted in headings
    )


def extract_potential_quote(node: lxml.html.HtmlElement) -> Optional[Text]:
    """
    Extract a potential quote from a given node.

    :param node: The node potentially containing a quote.
    :return: Extracted quote or None if not found.
    """
    if node.tag == "dl":
        dds = node.xpath("dd")
        if all(is_quote_node(dd) for dd in dds):
            return clean_txt("\n".join(dd.text_content().strip() for dd in dds))
        return None

    # Remove nested uls (unordered lists) from the node, if any
    for ul in node.xpath("ul"):
        ul.getparent().remove(ul)

    return (
        clean_txt(" ".join(node.text_content().split()))
        if is_quote_node(node)
        else None
    )


def is_quote(txt: Text, word_blacklist: List[Text]) -> bool:
    """
    This function will check if a string is a valid quote. A valid quote is defined as a
    string that:
    - Does not start with a lowercase letter
    - Is at least MIN_QUOTE_LEN characters long
    - Is at least MIN_QUOTE_WORDS words long
    - Does not contain any words in the word_blacklist
    - Does not end with a colon, parenthesis, or bracket
    - Does not start with a parenthesis

    :param txt: The text to check
    :param word_blacklist: A list of words to blacklist
    :return: True if the text is a valid quote, False otherwise
    :rtype: bool
    """
    txt_split = txt.split()
    invalid_conditions = [
        txt and txt[0].isalpha() and txt[0].islower(),
        len(txt) < MIN_QUOTE_LEN,
        len(txt_split) < MIN_QUOTE_WORDS,
        any(True for word in txt_split if word in word_blacklist),
        txt.endswith(("(", ":", "]")),
        txt.startswith(("(",)),
    ]

    # Returns False if any invalid conditions are True, otherwise returns True.
    return not any(invalid_conditions)


def is_quote_node(node: lxml.html.HtmlElement) -> bool:
    """
    This function will check if a node is a valid quote. It returns True if the node is
    a valid quote, False otherwise.
    - A valid quote is defined as a node that is not a small tag, and is not just a
      link.

    :param node: The node to check
    :return: True if the node is a valid quote, False otherwise
    """
    # Discard nodes with the <small> tag
    if node.find("small") is not None:
        return False

    # Discard nodes that are just a link
    # (using xpath so lxml will show text nodes)
    # The link may be inside <i> or <b> tags, so keep peeling layers
    suspect_node = node
    while True:
        node_children = suspect_node.xpath("child::node()")
        if len(node_children) != 1:
            break
        suspect_node = node_children[0]
        if not isinstance(suspect_node, lxml.etree._Element):
            break
        if suspect_node.tag == "a":
            return False
    return True


def clean_txt(txt: Text) -> Text:
    """
    This function will clean the text of a quote by removing unwanted characters,
    non-breaking spaces, and leading and trailing newlines/quotes.

    :param txt: The text to clean
    :return: The cleaned text
    """
    txt = re.sub(r'«|»|"|“|”', "", txt)  # Remove unwanted characters
    txt = txt.replace("\xa0", "")  # Remove non-breaking spaces
    return txt.strip()  # Remove leading and trailing newlines/quotes
