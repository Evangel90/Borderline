"""Source passage: the exact page a citation or quote comes from, with the passage highlighted."""

from __future__ import annotations

import re

import pymupdf
import streamlit as st

from common import BINDING_LAW, REPO_URL, ROOT, chunks, exhibits, sidebar_note, sources

sidebar_note()
st.title("📄 Source passage")
st.write(
    "Every citation and quote on this site links here. You see the passage the AI agent was given, the page of the "
    "registered document it comes from (cited text highlighted) and links to the official source."
)

chunk_id = st.text_input("Passage ID", value=st.query_params.get("chunk", "CH-HEALTH-MedDO:p28:c1")).strip()
quote = st.query_params.get("quote", "") if chunk_id == st.query_params.get("chunk") else ""
if chunk_id:
    st.query_params["chunk"] = chunk_id


def _norm(word: str) -> str:
    return re.sub(r"\W", "", word.casefold())


def find_word_run(page: pymupdf.Page, quote: str) -> list:
    """Rectangles of the first place the quote's words appear in order, joining words hyphenated across lines."""
    tokens: list[tuple[str, list]] = []
    for w in page.get_text("words"):
        rect, text = pymupdf.Rect(w[:4]), w[4]
        if tokens and tokens[-1][0].endswith("-") and tokens[-1][1][-1].y1 < rect.y0 + 2:
            prev, rects = tokens.pop()
            tokens.append((prev[:-1] + text, rects + [rect]))
        else:
            tokens.append((text, [rect]))
    page_words = [_norm(t) for t, _ in tokens]
    wanted = [n for n in (_norm(w) for w in quote.split()) if n]
    for start in range(len(page_words) - len(wanted) + 1):
        if wanted and page_words[start:start + len(wanted)] == wanted:
            return [r for _, rects in tokens[start:start + len(wanted)] for r in rects]
    return []


def highlight_rects(page: pymupdf.Page, quote: str, text: str) -> tuple[list, str]:
    """Find the quote on the page (each part, if it has '...'); failing that, the lines of the passage."""
    if quote:
        hits = [r for part in re.split(r"\.{3}|…", quote) if part.strip() for r in find_word_run(page, part)]
        if hits:
            return hits, "the quoted text"
    lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 12]
    hits = [r for ln in lines[:80] for r in page.search_for(ln)]
    return hits, ("the passage (the quote does not appear word for word on this page)" if quote else "the passage")


@st.cache_data(show_spinner=False)
def render_page(file: str, page_no: int, quote: str, text: str) -> tuple[bytes, str]:
    with pymupdf.open(ROOT / file) as doc:
        page = doc[page_no - 1]
        rects, what = highlight_rects(page, quote, text)
        for rect in rects:
            page.add_highlight_annot(rect)
        return page.get_pixmap(dpi=110).tobytes("png"), what if rects else ""


record = chunks().get(chunk_id)
exhibit = exhibits().get(chunk_id.split(":")[0]) if chunk_id else None

if record:
    meta = next((r for r in sources() if r["doc_id"] == record["doc_id"]), {})
    binding = record.get("source_binding") or meta.get("binding", "")
    file = record.get("source_file") or meta.get("file", "")
    st.markdown(f"### {record.get('title')}")
    st.markdown(
        f"**Page {record.get('page')} of {record.get('total_pages')}** · {record.get('source_issuer', '')} · "
        f"{binding.replace('_', ' ')}"
        + ("" if binding in BINDING_LAW else " · *guidance: can be cited but never counts as a legal basis*")
    )
    links = [f"[Official source ↗]({record.get('source_url') or meta.get('source_url')})"]
    if file:
        links.append(f"[Copy in this repository ↗]({REPO_URL}/blob/incident-drill/{file.replace(' ', '%20')}) "
                     f"(open page {record.get('page')})")
    st.markdown(" · ".join(links))
    if quote:
        st.markdown(f"**Quoted text:**\n\n> {quote}")
    left, right = st.columns([3, 2])
    with left:
        if file and (ROOT / file).is_file():
            png, what = render_page(file, int(record["page"]), quote, record.get("text", ""))
            st.image(png, width="stretch")
            st.caption(f"Highlighted: {what}." if what
                       else "Could not highlight the text automatically on this page; the passage is shown alongside.")
        else:
            st.info("The source file is not in this checkout; use the official source link.")
    with right:
        st.markdown(f"**Passage `{chunk_id}`** (the text the agent was given)")
        st.text(record.get("text", ""))
        if record.get("source_sha256"):
            st.caption(f"File SHA-256: `{record['source_sha256']}`")
elif exhibit:
    st.markdown(f"### Synthetic drill exhibit: {exhibit.get('title', exhibit['id'])}")
    st.caption("Written for the drill, not a real document. It can be quoted but never counts as law.")
    if quote:
        st.markdown(f"**Quoted text:**\n\n> {quote}")
    st.text(exhibit.get("text", ""))
elif chunk_id:
    st.error("No passage with that ID.")
