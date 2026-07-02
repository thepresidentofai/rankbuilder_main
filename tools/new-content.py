from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
SITE_URL = "https://rankbuilderseo.com"

TYPE_MAP = {
    "guide": {"directory": "guides", "section": "guides"},
    "technical-seo": {"directory": "technical-seo", "section": "technical-seo"},
    "local-seo": {"directory": "local-seo", "section": "local-seo"},
    "provider-review": {"directory": "providers", "section": "providers"},
    "audit-review": {"directory": "audit-reviews", "section": "audit-reviews"},
    "pricing": {"directory": "pricing", "section": "pricing"},
    "dictionary": {"directory": "dictionary", "section": "dictionary"},
    "bad-seo-pattern": {"directory": "bad-seo-patterns", "section": "bad-seo-patterns"},
    "experiment": {"directory": "experiments", "section": "experiments"},
    "research": {"directory": "research", "section": "research"},
    "template": {"directory": "templates", "section": "templates"},
    "checklist": {"directory": "checklists", "section": "checklists"},
}

DEFAULT_HEADINGS = {
    "guide": ["Short answer", "Why it matters", "How to verify", "Sources and notes", "Related links"],
    "technical-seo": ["Short answer", "Why it matters", "How to verify", "Sources and notes", "Related links"],
    "local-seo": ["Short answer", "Why it matters", "How to verify", "Sources and notes", "Related links"],
    "provider-review": ["Short answer", "Buyer questions", "How to verify", "Sources and notes", "Related links"],
    "audit-review": ["Short answer", "Buyer questions", "How to verify", "Sources and notes", "Related links"],
    "pricing": ["Short answer", "Why it matters", "Cost and effort", "Sources and notes", "Related links"],
    "dictionary": ["Short answer", "Why it matters", "How to verify", "Sources and notes", "Related links"],
    "bad-seo-pattern": ["Short answer", "Why it matters", "Verdict", "Sources and notes", "Related links"],
    "experiment": ["Short answer", "Why it matters", "Methodology", "How to verify", "Sources and notes", "Related links"],
    "research": ["Short answer", "Why it matters", "How to verify", "Sources and notes", "Related links"],
    "template": ["Short answer", "Why it matters", "How to use", "Sources and notes", "Related links"],
    "checklist": ["Short answer", "Checklist", "How to verify", "Sources and notes", "Related links"],
}


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug


def build_front_matter(content_type: str, title: str, slug: str, section: str) -> str:
    today = date.today().isoformat()
    payload = {
        "title": title,
        "slug": slug,
        "type": content_type,
        "section": section,
        "description": "TODO: add a concise public description.",
        "canonical": f"{SITE_URL}/{section}/{slug}/",
        "published": today,
        "modified": today,
        "status": "draft",
        "evidence_level": "draft",
        "risk_level": "low",
        "author": "Rank Builder SEO",
        "reviewer": "TODO: assign reviewer.",
        "sources": [],
        "related": [],
    }
    return json.dumps(payload, indent=2)


def build_body(content_type: str) -> str:
    headings = DEFAULT_HEADINGS[content_type]
    blocks = []
    for heading in headings:
        blocks.append(f"## {heading}\n\nTODO: add content.\n")
    return "\n".join(blocks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a draft Rank Builder content file.")
    parser.add_argument("content_type", choices=sorted(TYPE_MAP))
    parser.add_argument("title")
    args = parser.parse_args()

    mapping = TYPE_MAP[args.content_type]
    slug = slugify(args.title)
    destination = CONTENT_DIR / mapping["directory"] / f"{slug}.md"

    if destination.exists():
        response = input(f"{destination} exists. Overwrite? [y/N]: ").strip().lower()
        if response != "y":
            raise SystemExit("Aborted.")

    front_matter = build_front_matter(args.content_type, args.title, slug, mapping["section"])
    body = build_body(args.content_type)
    text = f"---\n{front_matter}\n---\n{body}"

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    print(f"Created {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
