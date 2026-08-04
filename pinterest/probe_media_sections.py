from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

PROJECTS = ["13-59", "65-52", "58-70W", "40-04BBAK", "63-42"]
SITE = "https://catalog-plans.ru"
OUT = Path(__file__).with_name("probe_media_output")
OUT.mkdir(exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Referer": SITE + "/", "Accept-Language": "ru-RU,ru;q=.9"})
IMG_RE = re.compile(r"(?:https?:)?//catalog-plans\.ru/files/[^\"'<> )]+?\.(?:jpe?g|png|webp|avif)(?:\?[^\"'<> )]*)?|/files/[^\"'<> )]+?\.(?:jpe?g|png|webp|avif)(?:\?[^\"'<> )]*)?", re.I)


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def abs_url(value: str, page: str) -> str:
    value = value.strip().replace("&amp;", "&")
    if value.startswith("//"):
        value = "https:" + value
    return urllib.parse.urljoin(page, value)


def nearest_heading(tag: Tag) -> str:
    for previous in tag.find_all_previous(["h1", "h2", "h3", "h4"], limit=6):
        text = clean(previous.get_text(" ", strip=True))
        if text:
            return text
    return ""


def ancestor_context(tag: Tag) -> str:
    bits = []
    node = tag
    for _ in range(5):
        if not isinstance(node, Tag):
            break
        bits.extend(node.get("class", []))
        if node.get("id"):
            bits.append(node.get("id"))
        if node.get("data-type"):
            bits.append(node.get("data-type"))
        if node.get("data-tab"):
            bits.append(node.get("data-tab"))
        node = node.parent
    return clean(" ".join(bits))


def urls_from_tag(tag: Tag, page: str) -> list[tuple[str, str]]:
    result = []
    for attr in ["src", "href", "data-src", "data-lazy", "data-original", "data-full", "data-image", "data-preview"]:
        value = tag.get(attr)
        if value and IMG_RE.search(value):
            result.append((attr, abs_url(value, page)))
    for attr in ["srcset", "data-srcset"]:
        value = tag.get(attr)
        if value:
            for part in value.split(","):
                candidate = part.strip().split(" ")[0]
                if IMG_RE.search(candidate):
                    result.append((attr, abs_url(candidate, page)))
    return result


def section_dump(soup: BeautifulSoup, title: str, page: str) -> dict:
    heading = None
    for candidate in soup.find_all(["h1", "h2", "h3", "h4"]):
        if title.lower() in clean(candidate.get_text(" ", strip=True)).lower():
            heading = candidate
            break
    if not heading:
        return {"found": False, "title": title, "items": []}

    items = []
    node = heading.next_element
    count = 0
    while node is not None and count < 3000:
        count += 1
        if isinstance(node, Tag):
            if node is not heading and node.name in ["h1", "h2"]:
                break
            if node.name in ["img", "source", "a"]:
                for attr, url in urls_from_tag(node, page):
                    items.append({
                        "tag": node.name,
                        "attr": attr,
                        "url": url,
                        "alt": clean(node.get("alt")),
                        "title": clean(node.get("title")),
                        "classes": clean(" ".join(node.get("class", []))),
                        "ancestor_context": ancestor_context(node),
                    })
        node = node.next_element

    unique = []
    seen = set()
    for item in items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)
    return {"found": True, "title": title, "heading_html": str(heading)[:1200], "items": unique}


def probe(project: str) -> dict:
    page = f"{SITE}/catalog/{project}"
    response = S.get(page, timeout=45)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    all_items = []
    for tag in soup.find_all(["img", "source", "a"]):
        for attr, url in urls_from_tag(tag, page):
            all_items.append({
                "tag": tag.name,
                "attr": attr,
                "url": url,
                "alt": clean(tag.get("alt")),
                "title": clean(tag.get("title")),
                "classes": clean(" ".join(tag.get("class", []))),
                "ancestor_context": ancestor_context(tag),
                "heading": nearest_heading(tag),
            })

    unique = []
    seen = set()
    for item in all_items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return {
        "project": project,
        "page": page,
        "title": clean(soup.title.get_text(" ", strip=True) if soup.title else ""),
        "plans_section": section_dump(soup, "Поэтажные планы проекта", page),
        "facades_section": section_dump(soup, "Фасады проекта", page),
        "all_images": unique,
        "html_regex_urls": list(dict.fromkeys(abs_url(match.group(0), page) for match in IMG_RE.finditer(response.text))),
    }


def main() -> None:
    reports = []
    for project in PROJECTS:
        report = probe(project)
        reports.append(report)
        print(project, "plans", len(report["plans_section"]["items"]), "facades", len(report["facades_section"]["items"]), "all", len(report["all_images"]), flush=True)
    (OUT / "media_probe.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
