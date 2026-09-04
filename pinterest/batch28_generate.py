from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import time
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

# audit_generate.py reads HEAD_SHA at import time.
os.environ.setdefault("HEAD_SHA", "local")
import audit_generate as old
import audit_generate_v3 as v3

ROOT = Path(__file__).parent
OUT = ROOT / "audit_output_batch28"
CARDS = ROOT / "generated_batch_28_no_button"
SAMPLES = OUT / "sample_cards"
for directory in (OUT, CARDS, SAMPLES):
    directory.mkdir(parents=True, exist_ok=True)

SITE = "https://catalog-plans.ru"
REPO = os.environ.get("GITHUB_REPOSITORY", "nemchenik/test")
ASSET_BRANCH = os.environ.get("ASSET_BRANCH", "catalog-plans-pinterest-assets")
PROJECT_RE = re.compile(r"^\d{2}-[A-Za-z0-9]+$")
CATALOG_RE = re.compile(r"/catalog/(\d{2}-[A-Za-z0-9]+)(?:[/?#]|$)")
HEADERS = [
    "Title", "Media URL", "Pinterest board", "Thumbnail",
    "Description", "Link", "Publish date", "Keywords",
]


def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()


def previous_ids():
    path = ROOT / "generated_batch_27" / "catalog_plans_pinterest_house_cards_batch_26_FIXED_200.csv"
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return {
            urllib.parse.urlsplit(row["Link"]).path.rstrip("/").split("/")[-1]
            for row in csv.DictReader(file)
        }


def sitemap_urls(url, seen=None, depth=0):
    if seen is None:
        seen = set()
    if depth > 3 or url in seen:
        return []
    seen.add(url)
    response = old.get(url, timeout=60)
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        return []
    tag = root.tag.rsplit("}", 1)[-1].lower()
    locs = [clean(node.text) for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() == "loc"]
    if tag == "sitemapindex":
        result = []
        for child in locs:
            try:
                result.extend(sitemap_urls(child, seen, depth + 1))
            except Exception as exc:
                print("SITEMAP CHILD SKIP", child, exc, flush=True)
        return result
    return locs


def discover_ids():
    sources = []
    try:
        robots = old.get(SITE + "/robots.txt").text
        sources.extend(match.group(1).strip() for match in re.finditer(r"(?im)^\s*Sitemap:\s*(\S+)", robots))
    except Exception as exc:
        print("ROBOTS SKIP", exc, flush=True)
    sources.extend([SITE + "/sitemap.xml", SITE + "/sitemap_index.xml"])
    sources = list(dict.fromkeys(sources))

    ids = set()
    for source in sources:
        try:
            urls = sitemap_urls(source)
            print("SITEMAP", source, len(urls), flush=True)
        except Exception as exc:
            print("SITEMAP SKIP", source, exc, flush=True)
            continue
        for url in urls:
            match = CATALOG_RE.search(url)
            if match:
                ids.add(match.group(1))

    if len(ids) < 500:
        raise RuntimeError(f"Only {len(ids)} project IDs found in sitemaps")
    return sorted(ids, key=lambda project: hashlib.sha1(f"batch28:{project}".encode()).hexdigest())


def strict_record(record):
    if record is None:
        return False
    return (
        record.image_origin == "og:image"
        and record.image_width >= 1000
        and record.image_height >= 620
        and record.white_ratio <= 0.45
        and PROJECT_RE.fullmatch(record.project)
    )


def render_without_button(record, index, source_path, target_path):
    intent = v3.render(record, index, source_path, target_path)
    image = Image.open(target_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    paper = "#F5F1E9"
    accent = "#C86F45"
    ink_muted = "#667068"

    # Remove the complete orange CTA block from the previous layout.
    draw.rectangle((535, 1340, 980, 1465), fill=paper)
    draw.line((48, 1360, 952, 1360), fill="#D9D0C2", width=2)
    draw.text((48, 1400), "catalog-plans.ru", font=v3.font(22, True), fill=ink_muted)
    footer = "Планы • фасады • размеры  →"
    footer_font = v3.font(22, True)
    footer_width = draw.textbbox((0, 0), footer, font=footer_font)[2]
    draw.text((952 - footer_width, 1400), footer, font=footer_font, fill=accent)
    image.save(target_path, "JPEG", quality=87, optimize=True, progressive=True)
    return intent


def description(record):
    facts = []
    if record.area:
        facts.append(f"{record.area} м²")
    if record.floors:
        facts.append(v3.floor_text(record.floors))
    if record.dimensions:
        facts.append(f"габариты {record.dimensions} м")
    if record.material:
        facts.append(f"стены — {record.material}")
    if record.style:
        facts.append(f"стиль — {record.style}")
    if record.feature:
        facts.append(f"особенность — {record.feature}")
    text = (
        f"Проект дома №{record.project}. На превью показана каноническая "
        "визуализация со страницы этого проекта на catalog-plans.ru. "
        "В карточке доступны планы этажей, фасады, размеры и характеристики."
    )
    if facts:
        text += f" Параметры: {'; '.join(facts)}."
    return (text + " Откройте проект и сопоставьте планировку и габариты со своим участком до заказа.")[:500]


def title(record, index):
    variants = [
        f"Проект дома №{record.project}: планы, фасады и размеры",
        f"Дом №{record.project}: проверить параметры проекта",
        f"Проект №{record.project}: габариты и планировка дома",
        f"Дом №{record.project}: посмотреть проект целиком",
        f"Проект дома №{record.project}: сравнить перед выбором",
        f"Дом №{record.project}: фасады, этажи и характеристики",
    ]
    return variants[index % len(variants)]


def make_contact_sheet(records):
    tile_w, tile_h, label_h, cols = 180, 270, 26, 5
    rows = math.ceil(len(records) / cols)
    sheet = Image.new("RGB", (tile_w * cols, (tile_h + label_h) * rows), "white")
    draw = ImageDraw.Draw(sheet)
    label_font = v3.font(14, True)
    for index, record in enumerate(records):
        x = (index % cols) * tile_w
        y = (index // cols) * (tile_h + label_h)
        card = Image.open(CARDS / f"{record.project}.jpg")
        sheet.paste(ImageOps.fit(card, (tile_w, tile_h), Image.Resampling.LANCZOS), (x, y))
        draw.rectangle((x, y + tile_h, x + tile_w, y + tile_h + label_h), fill="#17211B")
        draw.text((x + 6, y + tile_h + 5), record.project, font=label_font, fill="white")
    sheet.save(OUT / "contact_sheet_batch28_200.jpg", "JPEG", quality=88, optimize=True)


def main():
    for directory in (OUT, CARDS, SAMPLES):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)

    excluded = previous_ids()
    candidates = [project for project in discover_ids() if project not in excluded]
    print("EXCLUDED", len(excluded), "CANDIDATES", len(candidates), flush=True)

    accepted = []
    used_images = set()
    cursor = 0
    while len(accepted) < 200 and cursor < len(candidates):
        chunk = candidates[cursor:cursor + 260]
        cursor += 260
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {executor.submit(old.process, project): project for project in chunk}
            for future in as_completed(futures):
                try:
                    record = future.result()
                except Exception as exc:
                    print("PROCESS ERROR", futures[future], exc, flush=True)
                    continue
                if not strict_record(record) or record.image_url in used_images:
                    continue
                accepted.append(record)
                used_images.add(record.image_url)
                print(
                    f"ACCEPT {len(accepted):03d} {record.project} "
                    f"{record.image_width}x{record.image_height} white={record.white_ratio:.3f}",
                    flush=True,
                )
                if len(accepted) == 200:
                    break

    if len(accepted) < 200:
        raise RuntimeError(f"Only {len(accepted)} strict verified projects found")
    accepted.sort(key=lambda record: record.project)

    source_dir = OUT / "source_images"
    source_dir.mkdir(exist_ok=True)

    def download(record):
        content = old.get(record.image_url, timeout=45).content
        path = source_dir / f"{record.project}.img"
        path.write_bytes(content)
        return record.project, path

    source_paths = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(download, record) for record in accepted]
        for future in as_completed(futures):
            project, path = future.result()
            source_paths[project] = path

    rows = []
    sample_indices = {0, 25, 50, 75, 100, 125, 150, 175}
    for index, record in enumerate(accepted):
        target = CARDS / f"{record.project}.jpg"
        intent = render_without_button(record, index, source_paths[record.project], target)
        with Image.open(target) as check:
            assert check.size == (1000, 1500)
        if index in sample_indices:
            shutil.copy2(target, SAMPLES / target.name)

        board = v3.board(record, index)
        pin_number = 5112 + index
        query = urllib.parse.urlencode({
            "utm_source": "pinterest",
            "utm_medium": "organic",
            "utm_campaign": "generated_house_cards_no_button_batch_28",
            "utm_content": f"pin_{pin_number}_{record.project.lower()}_{intent}",
            "utm_term": v3.slug(board),
        })
        media_url = (
            f"https://raw.githubusercontent.com/{REPO}/{ASSET_BRANCH}/"
            f"pinterest/generated_batch_28_no_button/{record.project}.jpg"
        )
        rows.append({
            "Title": title(record, index),
            "Media URL": media_url,
            "Pinterest board": board,
            "Thumbnail": "",
            "Description": description(record),
            "Link": f"{record.page_url}?{query}",
            "Publish date": "",
            "Keywords": v3.keywords(record, board),
        })

    assert len(rows) == 200
    assert len({row["Title"] for row in rows}) == 200
    assert len({row["Media URL"] for row in rows}) == 200
    assert len({row["Link"] for row in rows}) == 200
    assert all(len(row["Title"]) <= 100 for row in rows)
    assert all(len(row["Description"]) <= 500 for row in rows)

    csv_path = CARDS / "catalog_plans_pinterest_house_cards_batch_28_NO_BUTTON_200.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    audit_path = OUT / "image_audit_batch28.csv"
    with audit_path.open("w", encoding="utf-8-sig", newline="") as file:
        fieldnames = list(asdict(accepted[0]).keys())
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(record) for record in accepted)

    make_contact_sheet(accepted)
    shutil.copy2(csv_path, OUT / csv_path.name)
    (OUT / "summary_batch28.json").write_text(json.dumps({
        "projects": 200,
        "previous_projects_excluded": len(excluded),
        "unique_source_images": len(used_images),
        "generated_cards": 200,
        "card_size": "1000x1500",
        "image_origin": "strict og:image from exact project page",
        "max_white_ratio": max(record.white_ratio for record in accepted),
        "button_block_removed": True,
        "campaign": "generated_house_cards_no_button_batch_28",
        "asset_branch": ASSET_BRANCH,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(source_dir, ignore_errors=True)
    print("DONE", len(rows), "projects", len(used_images), "images", flush=True)


if __name__ == "__main__":
    main()
