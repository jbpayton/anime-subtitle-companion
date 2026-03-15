from urllib.parse import quote

from ..models.schemas import DictionaryLinks


def generate_links(surface: str, lemma: str) -> DictionaryLinks:
    """Generate external dictionary URLs for a token."""
    query = lemma or surface
    encoded = quote(query, safe="")
    return DictionaryLinks(
        jisho=f"https://jisho.org/search/{encoded}",
        wiktionary=f"https://en.wiktionary.org/wiki/{encoded}",
    )
