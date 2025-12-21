# /ml_backend/dom_extract.py

from playwright.sync_api import sync_playwright
from utils import build_norm_index, normalize_xpath_for_labelstudio

# ----------------------------------
# DOM extraction (raw + normalized + index_map)
# ----------------------------------
def extract_dom_with_chromium(html: str):
    """
    Returns list of dicts:
      {
        "xpath": str,
        "raw": original textContent,
        "content": normalized text,
        "index_map": list[int] mapping normalized indices -> original indices
      }
    """
    extracted = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")

        elements = page.query_selector_all("body *")
        for el in elements:
            try:
                raw_text = page.evaluate("el => el.textContent", el) or ""
                norm_text, index_map = build_norm_index(raw_text)
                if not norm_text:
                    continue

                xpath = page.evaluate(
                    """el => {
                        function getXPath(e) {
                            if (e.id) return '//*[@id="' + e.id + '"]';
                            if (e === document.body) return '/html/body';
                            let ix = 1;
                            const siblings = e.parentNode ? e.parentNode.childNodes : [];
                            for (let i = 0; i < siblings.length; i++) {
                                const s = siblings[i];
                                if (s === e) return getXPath(e.parentNode) + '/' + e.tagName.toLowerCase() + '[' + ix + ']';
                                if (s.nodeType === 1 && s.tagName === e.tagName) ix++;
                            }
                            return '';
                        }
                        return getXPath(el);
                    }""",
                    el,
                )
                cleaned_xpath = normalize_xpath_for_labelstudio(xpath)
                extracted.append(
                    {
                        "xpath": cleaned_xpath,
                        "raw": raw_text,
                        "content": norm_text,
                        "index_map": index_map,
                    }
                )
            except Exception:
                continue

        browser.close()
    return extracted

