"""Real novelty grounding via the public arXiv API (no API key needed).

Exists specifically so the idea agent checks novelty against actual literature
instead of self-assessing novelty from its own judgment -- prior audits found
Sakana AI Scientist v1's self-assessed novelty check labeled a well-known
existing technique (SGD micro-batching) as novel because it never grounded
against real search results.
"""
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ATOM_NS = "{http://www.w3.org/2005/Atom}"


def search_arxiv(query, max_results=6):
    params = urllib.parse.urlencode(
        {"search_query": f"all:{query}", "start": 0, "max_results": max_results, "sortBy": "relevance"}
    )
    url = f"http://export.arxiv.org/api/query?{params}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            raw = resp.read()
    except Exception as e:
        return [{"title": f"(arXiv search failed: {e})", "summary": "", "url": ""}]

    root = ET.fromstring(raw)
    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        title = (entry.findtext(f"{ATOM_NS}title", default="") or "").strip().replace("\n", " ")
        summary = (entry.findtext(f"{ATOM_NS}summary", default="") or "").strip().replace("\n", " ")
        link = (entry.findtext(f"{ATOM_NS}id", default="") or "").strip()
        if title:
            papers.append({"title": title, "summary": summary[:400], "url": link})
    return papers
