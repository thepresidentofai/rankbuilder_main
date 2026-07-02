from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONTENT_DIR = ROOT / "content"
TEMPLATES_DIR = ROOT / "templates"
PUBLIC_DIR = ROOT / "public"

DATE_FORMAT = "%Y-%m-%d"

SUPPORTED_STATUSES = {"draft", "review", "published", "archived"}
SUPPORTED_TYPES = {
    "page",
    "guide",
    "technical-seo",
    "local-seo",
    "provider-review",
    "audit-review",
    "pricing",
    "dictionary",
    "template",
    "checklist",
    "bad-seo-pattern",
    "experiment",
    "research",
}

HOME_SECTION_ORDER = [
    "guides",
    "technical-seo",
    "providers",
    "audit-reviews",
    "pricing",
    "bad-seo-patterns",
    "experiments",
    "dictionary",
    "methodology",
    "research",
]

MANAGED_OUTPUTS = [
    "index.html",
    "404.html",
    "about",
    "editorial-policy",
    "corrections",
    "privacy",
    "methodology",
    "reviews",
    "guides",
    "technical-seo",
    "local-seo",
    "providers",
    "audit-reviews",
    "pricing",
    "dictionary",
    "templates",
    "checklists",
    "bad-seo-patterns",
    "experiments",
    "research",
    "articles",
    "sitemap.xml",
    "feed.xml",
    "robots.txt",
]

LEGACY_REDIRECTS = {
    "/articles/technical-seo-baseline-checklist/": "/guides/technical-seo-baseline-checklist/",
    "/articles/cloudflare-pages-seo-test-plan/": "/experiments/rb-exp-001-title-format-baseline/",
}

ICON_SVGS = {
    "wrench": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.5 4.5a5 5 0 0 0 5 5l-8.9 '
        '8.9a2 2 0 0 1-2.8 0l-1.7-1.7a2 2 0 0 1 0-2.8l8.9-8.9a5 5 0 0 0 5 5"/></svg>'
    ),
    "magnifying-glass": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/>'
        '<path d="M16 16l5 5"/></svg>'
    ),
    "clipboard": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 4h6l1 2h3v14H5V6h3l1-2Z"/>'
        '<path d="M9 11h6M9 15h6"/></svg>'
    ),
    "warning-triangle": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4 21 20H3L12 4Z"/>'
        '<path d="M12 9v5M12 17h.01"/></svg>'
    ),
    "flask": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 3h4M11 3v5l-5 8a3 3 0 0 0 2.6 4.5h6.8A3 3 0 0 0 18 16l-5-8V3"/>'
        '<path d="M9 14h6"/></svg>'
    ),
    "receipt": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4h10v16l-2-1.5L13 20l-2-1.5L9 20l-2-1.5L5 20V4h2Z"/>'
        '<path d="M9 9h6M9 13h6"/></svg>'
    ),
    "book": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5.5A2.5 2.5 0 0 1 7.5 3H19v16H7.5A2.5 2.5 0 0 0 5 21.5Z"/>'
        '<path d="M5 5.5v16M9 7h6"/></svg>'
    ),
    "shield-check": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 19 6v6c0 4.2-2.9 7.9-7 9-4.1-1.1-7-4.8-7-9V6l7-3Z"/>'
        '<path d="m9.5 12 1.8 1.8 3.7-3.8"/></svg>'
    ),
    "link-source": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 14 8 16a3 3 0 0 1-4.2-4.2l3-3A3 3 0 0 1 11 9"/>'
        '<path d="M14 10 16 8a3 3 0 1 1 4.2 4.2l-3 3A3 3 0 0 1 13 15"/>'
        '<path d="M8.5 12h7"/></svg>'
    ),
    "ruler-measure": (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 15 15 4l5 5-11 11H4Z"/>'
        '<path d="M13 6l5 5M9 10l2 2M6 13l2 2"/></svg>'
    ),
}


@dataclass(frozen=True)
class ContentEntry:
    source_path: Path
    metadata: dict
    body: str
    route: str
    canonical_url: str
    output_path: Path
    template_name: str
    published: datetime
    modified: datetime


@dataclass(frozen=True)
class PageRecord:
    route: str
    canonical_url: str
    output_path: Path
    title: str
    description: str
    modified: datetime
    include_in_sitemap: bool = True
    include_in_feed: bool = False


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def format_human_date(value: datetime) -> str:
    return value.strftime("%B %d, %Y")


def route_to_output_path(route: str) -> Path:
    trimmed = route.strip("/")
    if not trimmed:
        return PUBLIC_DIR / "index.html"
    return PUBLIC_DIR / trimmed / "index.html"


def ensure_clean_public() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    for name in MANAGED_OUTPUTS:
        target = PUBLIC_DIR / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def parse_date(raw_value: str, *, field_name: str, path: Path) -> datetime:
    try:
        return datetime.strptime(raw_value, DATE_FORMAT)
    except ValueError as exc:
        raise SystemExit(f"{path}: invalid {field_name} value {raw_value!r}") from exc


def parse_front_matter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise SystemExit(f"{path}: missing opening front matter fence")
    remainder = text[4:]
    marker = "\n---\n"
    end_index = remainder.find(marker)
    if end_index == -1:
        raise SystemExit(f"{path}: missing closing front matter fence")
    raw_front_matter = remainder[:end_index]
    body = remainder[end_index + len(marker) :].lstrip("\n")
    try:
        metadata = json.loads(raw_front_matter)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON front matter: {exc}") from exc
    return metadata, body


def build_route(metadata: dict) -> str:
    slug = str(metadata["slug"]).strip("/")
    section = str(metadata["section"]).strip("/")
    content_type = metadata["type"]
    if content_type == "page":
        if section in {"root", "pages", ""}:
            return f"/{slug}/"
        return f"/{section}/{slug}/"
    return f"/{section}/{slug}/"


def choose_template(metadata: dict, sections_by_id: dict[str, dict]) -> str:
    if metadata["type"] == "page":
        return "standard-page.html"
    section_id = str(metadata["section"])
    section_config = sections_by_id.get(section_id)
    if not section_config:
        raise SystemExit(f"Unknown section {section_id!r} for {metadata['title']!r}")
    return section_config["template"]


def validate_metadata(metadata: dict, path: Path) -> None:
    required_fields = {
        "title",
        "slug",
        "type",
        "section",
        "description",
        "published",
        "modified",
        "status",
        "evidence_level",
        "risk_level",
        "author",
        "reviewer",
        "sources",
        "related",
    }
    missing = sorted(field for field in required_fields if field not in metadata)
    if missing:
        raise SystemExit(f"{path}: missing required fields: {', '.join(missing)}")
    if metadata["status"] not in SUPPORTED_STATUSES:
        raise SystemExit(f"{path}: unsupported status {metadata['status']!r}")
    if metadata["type"] not in SUPPORTED_TYPES:
        raise SystemExit(f"{path}: unsupported type {metadata['type']!r}")
    if not isinstance(metadata["sources"], list) or not isinstance(metadata["related"], list):
        raise SystemExit(f"{path}: sources and related must be lists")


def load_entries(site: dict, sections_by_id: dict[str, dict]) -> list[ContentEntry]:
    entries: list[ContentEntry] = []
    seen_routes: dict[str, Path] = {}
    for path in sorted(CONTENT_DIR.rglob("*.md")):
        metadata, body = parse_front_matter(path)
        validate_metadata(metadata, path)
        published = parse_date(metadata["published"], field_name="published", path=path)
        modified = parse_date(metadata["modified"], field_name="modified", path=path)
        route = build_route(metadata)
        if route in seen_routes:
            raise SystemExit(f"Duplicate route {route} in {path} and {seen_routes[route]}")
        seen_routes[route] = path
        canonical_url = metadata.get("canonical") or f"{site['url'].rstrip('/')}{route}"
        template_name = choose_template(metadata, sections_by_id)
        entries.append(
            ContentEntry(
                source_path=path,
                metadata=metadata,
                body=body,
                route=route,
                canonical_url=canonical_url,
                output_path=route_to_output_path(route),
                template_name=template_name,
                published=published,
                modified=modified,
            )
        )
    return entries


def render_inline(text: str) -> str:
    tokens: list[str] = []

    def stash(fragment: str) -> str:
        token = f"@@TOKEN{len(tokens)}@@"
        tokens.append(fragment)
        return token

    text = re.sub(
        r"`([^`]+)`",
        lambda match: stash(f"<code>{escape(match.group(1))}</code>"),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: stash(
            f'<a href="{escape(match.group(2), quote=True)}">{escape(match.group(1))}</a>'
        ),
        text,
    )
    rendered = escape(text)
    for index, fragment in enumerate(tokens):
        rendered = rendered.replace(f"@@TOKEN{index}@@", fragment)
    return rendered


def markdown_to_html(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").split("\n")
    output: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_type: str | None = None
    quote_lines: list[str] = []
    code_lines: list[str] = []
    in_code_block = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.append(f"<p>{render_inline(' '.join(part.strip() for part in paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items, list_type
        if list_items and list_type:
            items_html = "".join(f"<li>{item}</li>" for item in list_items)
            output.append(f"<{list_type}>{items_html}</{list_type}>")
            list_items = []
            list_type = None

    def flush_quote() -> None:
        nonlocal quote_lines
        if quote_lines:
            joined = "\n".join(quote_lines).strip()
            output.append(f"<blockquote>{markdown_to_html(joined)}</blockquote>")
            quote_lines = []

    def flush_code() -> None:
        nonlocal code_lines
        if code_lines:
            output.append(f"<pre><code>{escape('\n'.join(code_lines))}</code></pre>")
            code_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if in_code_block:
            if stripped.startswith("```"):
                in_code_block = False
                flush_code()
            else:
                code_lines.append(raw_line)
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_quote()
            in_code_block = True
            code_lines = []
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            flush_list()
            quote_lines.append(stripped[1:].lstrip())
            continue
        flush_quote()

        heading_match = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            output.append(f"<h{level}>{render_inline(heading_match.group(2).strip())}</h{level}>")
            continue

        unordered_match = re.match(r"^[-*]\s+(.*)$", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if unordered_match:
            flush_paragraph()
            if list_type not in {None, "ul"}:
                flush_list()
            list_type = "ul"
            list_items.append(render_inline(unordered_match.group(1).strip()))
            continue
        if ordered_match:
            flush_paragraph()
            if list_type not in {None, "ol"}:
                flush_list()
            list_type = "ol"
            list_items.append(render_inline(ordered_match.group(1).strip()))
            continue

        flush_list()
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    flush_quote()
    if in_code_block:
        raise SystemExit("Unclosed code fence in markdown content")
    return "\n".join(output)


def split_body_sections(body: str) -> tuple[str, dict[str, str]]:
    preface: list[str] = []
    sections: dict[str, list[str]] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_heading, current_lines
        if current_heading is not None:
            sections[current_heading] = current_lines[:]
        current_heading = None
        current_lines = []

    for raw_line in body.replace("\r\n", "\n").split("\n"):
        if raw_line.startswith("## "):
            flush_current()
            current_heading = raw_line[3:].strip()
            current_lines = []
        else:
            if current_heading is None:
                preface.append(raw_line)
            else:
                current_lines.append(raw_line)
    flush_current()
    section_text = {heading: "\n".join(lines).strip() for heading, lines in sections.items()}
    preface_html = markdown_to_html("\n".join(preface).strip()) if "\n".join(preface).strip() else ""
    return preface_html, section_text


def render_template_file(template_name: str, context: dict[str, str]) -> str:
    template_path = TEMPLATES_DIR / template_name
    return render_template_string(template_path.read_text(encoding="utf-8"), context)


def render_template_string(template_text: str, context: dict[str, str]) -> str:
    include_pattern = re.compile(r"\[\[include:([^\]]+)\]\]")
    token_pattern = re.compile(r"\[\[([a-zA-Z0-9_.:\-/]+)\]\]")

    def include_replacer(match: re.Match[str]) -> str:
        include_path = TEMPLATES_DIR / match.group(1)
        return render_template_string(include_path.read_text(encoding="utf-8"), context)

    rendered = include_pattern.sub(include_replacer, template_text)
    return token_pattern.sub(lambda match: context.get(match.group(1), ""), rendered)


def render_partial(partial_name: str, context: dict[str, str]) -> str:
    partial_path = TEMPLATES_DIR / "partials" / partial_name
    return render_template_string(partial_path.read_text(encoding="utf-8"), context)


def build_nav_links(navigation: list[dict]) -> str:
    return "".join(
        f'<a href="{escape(item["href"], quote=True)}">{escape(item["label"])}</a>'
        for item in navigation
    )


def build_section_label(entry: ContentEntry, sections_by_id: dict[str, dict]) -> str:
    if entry.metadata["type"] == "page":
        if entry.metadata["section"] == "methodology" or entry.route.startswith("/methodology/"):
            return "Methodology"
        if entry.route == "/reviews/":
            return "Reviews"
        return "Rank Builder SEO"
    section_config = sections_by_id.get(entry.metadata["section"])
    return section_config["label"] if section_config else "Rank Builder SEO"


def evidence_badge_class(evidence_level: str) -> str:
    if "public" in evidence_level:
        return "badge-green"
    if "source" in evidence_level or "platform" in evidence_level:
        return "badge-orange"
    if "definition" in evidence_level or "starter" in evidence_level:
        return "badge-yellow"
    return "badge-orange"


def risk_badge_class(risk_level: str) -> str:
    risk_level = risk_level.lower()
    if risk_level == "low":
        return "badge-green"
    if risk_level == "medium":
        return "badge-yellow"
    return "badge-red"


def evidence_summary(entry: ContentEntry) -> str:
    evidence_level = entry.metadata["evidence_level"]
    if evidence_level == "public-experiment-log":
        return "This page logs a bounded public experiment and states its limits explicitly."
    if evidence_level in {"starter-guide", "buyer-defense-shell", "definition-shell"}:
        return "This is a restrained starter entry built for clarity, verification, and later expansion."
    if evidence_level in {"editorial-standard", "platform-disclosure"}:
        return "This page defines policy or platform context for how the publication operates."
    return "This page is published only after it meets the current review and sourcing threshold."


def risk_summary(entry: ContentEntry) -> str:
    risk_level = entry.metadata["risk_level"].lower()
    if risk_level == "low":
        return "Low practical risk: the page stays narrow and avoids strong unsupported claims."
    if risk_level == "medium":
        return "Medium practical risk: readers should inspect scope, missing evidence, and limits carefully."
    return "High practical risk: buyers should inspect caveats, proof, and contractual language closely."


def build_meta_html(entry: ContentEntry) -> str:
    return (
        f"Published <time datetime=\"{entry.metadata['published']}\">{format_human_date(entry.published)}</time>"
        f" <span class=\"meta-divider\">|</span> Updated "
        f"<time datetime=\"{entry.metadata['modified']}\">{format_human_date(entry.modified)}</time>"
    )


def list_from_paths(paths: Iterable[str]) -> str:
    items = []
    for raw_path in paths:
        if raw_path.startswith("/"):
            label = raw_path.strip("/").split("/")[-1].replace("-", " ").title()
            items.append(f'<li><a href="{escape(raw_path, quote=True)}">{escape(label)}</a></li>')
        else:
            items.append(
                f'<li><a href="{escape(raw_path, quote=True)}">{escape(raw_path)}</a></li>'
            )
    return f"<ul>{''.join(items)}</ul>" if items else ""


def paragraph_text(markdown: str) -> str:
    compact = " ".join(line.strip() for line in markdown.splitlines() if line.strip())
    return escape(compact)


def build_content_blocks(preface_html: str, sections: dict[str, str], excluded_headings: set[str]) -> str:
    blocks: list[str] = []
    if preface_html:
        blocks.append(preface_html)
    for heading, section_markdown in sections.items():
        if heading in excluded_headings:
            continue
        section_html = markdown_to_html(section_markdown)
        blocks.append(
            f"<section><h2>{escape(heading)}</h2>{section_html}</section>"
        )
    return "\n".join(blocks)


def build_schema(entry: ContentEntry | None, site: dict, *, is_home: bool = False) -> str:
    if is_home:
        payload = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": site["name"],
            "url": site["url"],
            "description": site["description"],
        }
    elif entry is not None:
        if entry.metadata["type"] == "page":
            payload = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": entry.metadata["title"],
                "url": entry.canonical_url,
                "description": entry.metadata["description"],
                "datePublished": entry.metadata["published"],
                "dateModified": entry.metadata["modified"],
            }
        else:
            payload = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": entry.metadata["title"],
                "url": entry.canonical_url,
                "description": entry.metadata["description"],
                "datePublished": entry.metadata["published"],
                "dateModified": entry.metadata["modified"],
                "author": {"@type": "Organization", "name": entry.metadata["author"]},
            }
    else:
        return ""
    return (
        "<script type=\"application/ld+json\">"
        + json.dumps(payload, separators=(",", ":"))
        + "</script>"
    )


def wrap_with_base(
    *,
    site: dict,
    navigation: list[dict],
    title: str,
    description: str,
    canonical_url: str,
    body_html: str,
    schema: str,
    og_type: str = "article",
    body_class: str = "",
    head_extras: str = "",
) -> str:
    context = {
        "title": escape(title),
        "meta_description": escape(description, quote=True),
        "canonical_url": escape(canonical_url, quote=True),
        "site_name": escape(site["name"]),
        "og_title": escape(title, quote=True),
        "og_description": escape(description, quote=True),
        "og_url": escape(canonical_url, quote=True),
        "og_type": escape(og_type, quote=True),
        "body": body_html,
        "body_class": escape(body_class, quote=True),
        "schema": schema,
        "head_extras": head_extras,
        "nav_links": build_nav_links(navigation),
    }
    return render_template_file("base.html", context)


def write_page(path: Path, html_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = "\n".join(line.rstrip() for line in html_text.rstrip().splitlines()) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(cleaned)


def write_text_file(path: Path, contents: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(contents)


def build_home_section_cards(sections: list[dict]) -> str:
    cards = []
    for section_id in HOME_SECTION_ORDER:
        section = next(item for item in sections if item["id"] == section_id)
        cards.append(
            "\n".join(
                [
                    '<article class="section-card">',
                    f'<div class="tag">{icon_svg(section["icon"])}<span>{escape(section["label"])}</span></div>',
                    f'<h3><a href="{escape(section["output_path"], quote=True)}">{escape(section["label"])}</a></h3>',
                    f"<p>{escape(section['description'])}</p>",
                    f'<a class="button button-secondary" href="{escape(section["output_path"], quote=True)}">Open section</a>',
                    "</article>",
                ]
            )
        )
    return "\n".join(cards)


def icon_svg(icon_name: str) -> str:
    svg = ICON_SVGS[icon_name]
    return f'<span class="icon">{svg}</span>'


def build_home_status_cards() -> str:
    status_cards = [
        ("link-source", "Source-first research", "Claims are expected to point back to a source note, method page, or bounded experiment."),
        ("flask", "Public experiments", "Experiments are logged as public records with narrow claims and explicit limits."),
        ("shield-check", "Provider and audit accountability", "Provider reviews and audit reviews stay separate so the standards stay inspectable."),
        ("receipt", "Pricing transparency", "Pricing pages focus on scope, proof, and contract questions instead of sales fog."),
    ]
    return "\n".join(
        "\n".join(
            [
                '<div class="content-card">',
                f'<div class="tag">{icon_svg(icon)}<span>{escape(title)}</span></div>',
                f"<p>{escape(description)}</p>",
                "</div>",
            ]
        )
        for icon, title, description in status_cards
    )


def content_card(entry: ContentEntry, sections_by_id: dict[str, dict]) -> str:
    if entry.metadata["type"] == "page":
        icon_name = "link-source"
        section_label = build_section_label(entry, sections_by_id)
    else:
        section_config = sections_by_id.get(entry.metadata["section"], {})
        icon_name = section_config.get("icon", "link-source")
        section_label = section_config.get("label", build_section_label(entry, sections_by_id))
    return "\n".join(
        [
            '<article class="content-card">',
            f'<div class="tag">{icon_svg(icon_name)}<span>{escape(section_label)}</span></div>',
            f'<h3><a href="{escape(entry.route, quote=True)}">{escape(entry.metadata["title"])}</a></h3>',
            f'<p>{escape(entry.metadata["description"])}</p>',
            '<div class="article-meta">',
            f'<span class="badge {risk_badge_class(entry.metadata["risk_level"])}">{escape(entry.metadata["risk_level"].title())} risk</span>',
            f'<span>{format_human_date(entry.modified)}</span>',
            "</div>",
            "</article>",
        ]
    )


def build_latest_content_cards(entries: list[ContentEntry], sections_by_id: dict[str, dict]) -> str:
    feed_entries = [entry for entry in entries if entry.metadata["type"] != "page"]
    if not feed_entries:
        return ""
    ordered = sorted(feed_entries, key=lambda item: (item.published, item.route), reverse=True)[:6]
    return "\n".join(content_card(entry, sections_by_id) for entry in ordered)


def render_entry(entry: ContentEntry, site: dict, navigation: list[dict], sections_by_id: dict[str, dict]) -> tuple[str, PageRecord]:
    preface_html, sections = split_body_sections(entry.body)
    short_answer = sections.get("Short answer", "")
    methodology = sections.get("Methodology", "")
    source_notes = sections.get("Sources and notes", "")
    related_links = sections.get("Related links", "")
    buyer_questions = sections.get("Buyer questions", "")
    verdict = sections.get("Verdict", "")

    short_answer_block = (
        f'<section class="short-answer"><h2>Short answer</h2>{markdown_to_html(short_answer)}</section>'
        if short_answer
        else ""
    )
    methodology_block = (
        f'<section class="methodology-box"><h2>Methodology</h2>{markdown_to_html(methodology)}</section>'
        if methodology and entry.template_name in {"standard-page.html", "experiment.html"}
        else ""
    )
    evidence_block = render_partial(
        "evidence-label.html",
        {
            "evidence_badge_class": evidence_badge_class(entry.metadata["evidence_level"]),
            "evidence_level_label": escape(entry.metadata["evidence_level"].replace("-", " ").title()),
            "evidence_summary": escape(evidence_summary(entry)),
        },
    )
    risk_block = render_partial(
        "risk-label.html",
        {
            "risk_badge_class": risk_badge_class(entry.metadata["risk_level"]),
            "risk_level_label": escape(entry.metadata["risk_level"].title()),
            "risk_summary": escape(risk_summary(entry)),
        },
    )
    verdict_block = (
        render_partial(
            "verdict-box.html",
            {"verdict_text": paragraph_text(verdict)},
        )
        if verdict
        else ""
    )
    buyer_questions_block = (
        render_partial(
            "buyer-questions.html",
            {"buyer_questions_items": markdown_to_html(buyer_questions)},
        )
        if buyer_questions
        else ""
    )
    source_notes_block = (
        render_partial(
            "source-notes.html",
            {"source_notes_items": markdown_to_html(source_notes)},
        )
        if source_notes
        else render_partial("source-notes.html", {"source_notes_items": list_from_paths(entry.metadata["sources"])})
        if entry.metadata["sources"]
        else ""
    )
    related_links_block = (
        render_partial(
            "related-links.html",
            {"related_links_items": markdown_to_html(related_links)},
        )
        if related_links
        else render_partial("related-links.html", {"related_links_items": list_from_paths(entry.metadata["related"])})
        if entry.metadata["related"]
        else ""
    )

    excluded_headings = {
        "Short answer",
        "Sources and notes",
        "Related links",
        "Buyer questions",
        "Verdict",
    }
    if methodology_block:
        excluded_headings.add("Methodology")

    content_blocks = build_content_blocks(preface_html, sections, excluded_headings)
    template_context = {
        "section_label": escape(build_section_label(entry, sections_by_id)),
        "page_title": escape(entry.metadata["title"]),
        "page_description": escape(entry.metadata["description"]),
        "article_meta": build_meta_html(entry),
        "short_answer_block": short_answer_block,
        "methodology_block": methodology_block,
        "evidence_block": evidence_block if entry.template_name != "standard-page.html" else "",
        "risk_block": risk_block if entry.metadata["risk_level"] else "",
        "verdict_block": verdict_block,
        "buyer_questions_block": buyer_questions_block,
        "source_notes_block": source_notes_block,
        "related_links_block": related_links_block,
        "content_blocks": content_blocks,
    }
    body_html = render_template_file(entry.template_name, template_context)
    wrapped = wrap_with_base(
        site=site,
        navigation=navigation,
        title=f"{entry.metadata['title']} | {site['name']}",
        description=entry.metadata["description"],
        canonical_url=entry.canonical_url,
        body_html=body_html,
        schema=build_schema(entry, site),
        og_type="article" if entry.metadata["type"] != "page" else "website",
        body_class="article-page",
    )
    page_record = PageRecord(
        route=entry.route,
        canonical_url=entry.canonical_url,
        output_path=entry.output_path,
        title=entry.metadata["title"],
        description=entry.metadata["description"],
        modified=entry.modified,
        include_in_sitemap=True,
        include_in_feed=entry.metadata["type"] != "page",
    )
    return wrapped, page_record


def render_section_index(section: dict, entries: list[ContentEntry], site: dict, navigation: list[dict]) -> tuple[str, PageRecord]:
    if entries:
        note = "Published entries in this section have passed source and review checks and are listed below."
        cards_html = "\n".join(
            content_card(entry, {section["id"]: section}) if entry.metadata["section"] == section["id"] else content_card(entry, {})
            for entry in sorted(entries, key=lambda item: (item.published, item.route), reverse=True)
        )
    else:
        note = (
            "This section is part of the Rank Builder publishing system. "
            "Individual entries are listed only after they pass source and review checks."
        )
        cards_html = ""
    body_html = render_template_file(
        "section-index.html",
        {
            "section_label": escape(section["label"]),
            "section_title": escape(section["label"]),
            "section_description": escape(section["description"]),
            "section_note": escape(note),
            "section_cards": cards_html,
        },
    )
    title = f"{section['label']} | {site['name']}"
    canonical_url = f"{site['url'].rstrip('/')}{section['output_path']}"
    wrapped = wrap_with_base(
        site=site,
        navigation=navigation,
        title=title,
        description=section["description"],
        canonical_url=canonical_url,
        body_html=body_html,
        schema="",
        og_type="website",
        body_class="section-page",
    )
    page_record = PageRecord(
        route=section["output_path"],
        canonical_url=canonical_url,
        output_path=route_to_output_path(section["output_path"]),
        title=section["label"],
        description=section["description"],
        modified=max((entry.modified for entry in entries), default=datetime.strptime("2026-07-01", DATE_FORMAT)),
        include_in_sitemap=True,
        include_in_feed=False,
    )
    return wrapped, page_record


def render_home(entries: list[ContentEntry], site: dict, navigation: list[dict], sections: list[dict], sections_by_id: dict[str, dict]) -> tuple[str, PageRecord]:
    methodology_links = "\n".join(
        [
            '<a href="/methodology/source-and-citation-standard/">Source and Citation Standard</a>',
            '<a href="/methodology/provider-review-methodology/">Provider Review Methodology</a>',
            '<a href="/methodology/audit-review-methodology/">Audit Review Methodology</a>',
            '<a href="/corrections/">Corrections Policy</a>',
        ]
    )
    body_html = render_template_file(
        "home.html",
        {
            "hero_status_cards": build_home_status_cards(),
            "home_section_cards": build_home_section_cards(sections),
            "methodology_links": methodology_links,
            "latest_content_cards": build_latest_content_cards(entries, sections_by_id),
        },
    )
    title = (
        f"{site['name']} | SEO research, pricing clarity, provider reviews, audit reviews, and public experiments"
    )
    wrapped = wrap_with_base(
        site=site,
        navigation=navigation,
        title=title,
        description=site["description"],
        canonical_url=f"{site['url'].rstrip('/')}/",
        body_html=body_html,
        schema=build_schema(None, site, is_home=True),
        og_type="website",
        body_class="home-page",
    )
    latest_modified = max((entry.modified for entry in entries), default=datetime.strptime("2026-07-01", DATE_FORMAT))
    page_record = PageRecord(
        route="/",
        canonical_url=f"{site['url'].rstrip('/')}/",
        output_path=PUBLIC_DIR / "index.html",
        title=site["name"],
        description=site["description"],
        modified=latest_modified,
        include_in_sitemap=True,
        include_in_feed=False,
    )
    return wrapped, page_record


def render_404(site: dict, navigation: list[dict]) -> str:
    body_html = (
        '<section class="section"><div class="page"><article class="article">'
        '<header class="article-header"><p class="kicker">404</p><h1>Page not found</h1>'
        '<p class="lede">The path you requested is not part of the current Rank Builder SEO publishing shell.</p>'
        "</header><div class=\"article-body\"><p>Use the section indexes to navigate the live publication.</p>"
        '<p><a class="button" href="/">Return to the homepage</a></p></div></article></div></section>'
    )
    return wrap_with_base(
        site=site,
        navigation=navigation,
        title=f"Page Not Found | {site['name']}",
        description="Requested page not found on Rank Builder SEO.",
        canonical_url=f"{site['url'].rstrip('/')}/404.html",
        body_html=body_html,
        schema="",
        og_type="website",
        body_class="not-found-page",
    )


def render_redirect_page(old_route: str, new_route: str, site: dict, navigation: list[dict], entries_by_route: dict[str, ContentEntry]) -> str:
    destination = entries_by_route[new_route]
    title = f"Moved: {destination.metadata['title']} | {site['name']}"
    body_html = (
        '<section class="section"><div class="page"><article class="article">'
        '<header class="article-header"><p class="kicker">Moved</p>'
        f'<h1>{escape(destination.metadata["title"])}</h1>'
        f'<p class="lede">This article moved to <a href="{escape(new_route, quote=True)}">{escape(new_route)}</a>.</p>'
        '</header><div class="warning-box"><p>The legacy URL is preserved so existing links do not break, but the canonical page lives at the new route.</p></div>'
        f'<p><a class="button" href="{escape(new_route, quote=True)}">Open the current page</a></p>'
        "</article></div></section>"
    )
    return wrap_with_base(
        site=site,
        navigation=navigation,
        title=title,
        description=f"{destination.metadata['title']} moved to {new_route}",
        canonical_url=destination.canonical_url,
        body_html=body_html,
        schema="",
        og_type="website",
        body_class="redirect-page",
        head_extras=(
            f'<meta http-equiv="refresh" content="0; url={escape(new_route, quote=True)}">\n'
            '<meta name="robots" content="noindex,follow">'
        ),
    )


def build_sitemap(site: dict, pages: list[PageRecord]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in sorted((item for item in pages if item.include_in_sitemap), key=lambda item: item.route):
        lines.extend(
            [
                "  <url>",
                f"    <loc>{escape(page.canonical_url)}</loc>",
                f"    <lastmod>{page.modified.strftime(DATE_FORMAT)}</lastmod>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return "\n".join(lines)


def rfc822_date(value: datetime) -> str:
    return value.strftime("%a, %d %b %Y 00:00:00 GMT")


def build_feed(site: dict, entries: list[ContentEntry]) -> str:
    feed_entries = sorted(
        (entry for entry in entries if entry.metadata["type"] != "page" and entry.metadata["status"] == "published"),
        key=lambda item: (item.published, item.route),
        reverse=True,
    )
    latest = feed_entries[0].modified if feed_entries else datetime.strptime("2026-07-01", DATE_FORMAT)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "  <channel>",
        f"    <title>{escape(site['rss_title'])}</title>",
        f"    <link>{escape(site['url'])}</link>",
        f"    <description>{escape(site['rss_description'])}</description>",
        f"    <language>{escape(site['language'])}</language>",
        f"    <lastBuildDate>{rfc822_date(latest)}</lastBuildDate>",
    ]
    for entry in feed_entries[:20]:
        lines.extend(
            [
                "    <item>",
                f"      <title>{escape(entry.metadata['title'])}</title>",
                f"      <link>{escape(entry.canonical_url)}</link>",
                f"      <guid>{escape(entry.canonical_url)}</guid>",
                f"      <pubDate>{rfc822_date(entry.published)}</pubDate>",
                f"      <description>{escape(entry.metadata['description'])}</description>",
                "    </item>",
            ]
        )
    lines.extend(["  </channel>", "</rss>"])
    return "\n".join(lines)


def build_robots(site: dict) -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {site['url'].rstrip('/')}/sitemap.xml\n"


def main() -> None:
    site = load_json(DATA_DIR / "site.json")
    navigation = load_json(DATA_DIR / "navigation.json")
    sections = load_json(DATA_DIR / "content-types.json")
    sections_by_id = {section["id"]: section for section in sections}

    if not (PUBLIC_DIR / "assets" / "styles.css").exists():
        raise SystemExit("public/assets/styles.css must exist before building")

    ensure_clean_public()
    entries = load_entries(site, sections_by_id)
    published_entries = [entry for entry in entries if entry.metadata["status"] == "published"]
    entries_by_route = {entry.route: entry for entry in published_entries}

    rendered_pages: list[PageRecord] = []

    home_html, home_record = render_home(published_entries, site, navigation, sections, sections_by_id)
    write_page(home_record.output_path, home_html)
    rendered_pages.append(home_record)

    for entry in sorted(published_entries, key=lambda item: item.route):
        html_text, page_record = render_entry(entry, site, navigation, sections_by_id)
        write_page(page_record.output_path, html_text)
        rendered_pages.append(page_record)

    for section in sections:
        if section.get("index_generated", True) is False:
            continue
        section_entries = [
            entry
            for entry in published_entries
            if entry.metadata["section"] == section["id"] and entry.metadata["type"] != "page"
        ]
        html_text, page_record = render_section_index(section, section_entries, site, navigation)
        write_page(page_record.output_path, html_text)
        rendered_pages.append(page_record)

    for old_route, new_route in LEGACY_REDIRECTS.items():
        if new_route not in entries_by_route:
            raise SystemExit(f"Legacy redirect target missing for {old_route}: {new_route}")
        redirect_html = render_redirect_page(old_route, new_route, site, navigation, entries_by_route)
        write_page(route_to_output_path(old_route), redirect_html)

    write_page(PUBLIC_DIR / "404.html", render_404(site, navigation))
    write_text_file(PUBLIC_DIR / "sitemap.xml", build_sitemap(site, rendered_pages) + "\n")
    write_text_file(PUBLIC_DIR / "feed.xml", build_feed(site, published_entries) + "\n")
    write_text_file(PUBLIC_DIR / "robots.txt", build_robots(site))


if __name__ == "__main__":
    main()
