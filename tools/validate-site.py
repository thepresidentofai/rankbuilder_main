from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
DATA_DIR = ROOT / "data"
PUBLIC_DIR = ROOT / "public"

REQUIRED_FILES = [
    PUBLIC_DIR / "index.html",
    PUBLIC_DIR / "sitemap.xml",
    PUBLIC_DIR / "feed.xml",
    PUBLIC_DIR / "robots.txt",
]

BANNED_MARKERS = ["todo", "lorem ipsum", "coming soon", "placeholder", "hello world"]
HOMEPAGE_BANNED_CTA_PHRASES = [
    "book a call",
    "hire us",
    "work with us",
    "request a quote",
    "schedule a call",
]
REQUIRED_FOOTER_HREFS = [
    "/about/",
    "/editorial-policy/",
    "/corrections/",
    "/privacy/",
    "/sitemap.xml",
    "/feed.xml",
]
SUPPORTED_STATUSES = {"draft", "review", "published", "archived"}


@dataclass(frozen=True)
class SourceEntry:
    route: str
    canonical: str
    status: str


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.h1_count = 0
        self.meta_description = ""
        self.canonical = ""
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta" and attr_map.get("name") == "description":
            self.meta_description = attr_map.get("content", "") or ""
        elif tag == "link":
            rel = attr_map.get("rel", "") or ""
            if "canonical" in rel:
                self.canonical = attr_map.get("href", "") or ""
        elif tag == "a" and attr_map.get("href"):
            self.hrefs.append(attr_map["href"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


def load_site() -> dict:
    return json.loads((DATA_DIR / "site.json").read_text(encoding="utf-8"))


def parse_front_matter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise SystemExit(f"{path}: missing opening front matter fence")
    remainder = text[4:]
    marker = "\n---\n"
    end_index = remainder.find(marker)
    if end_index == -1:
        raise SystemExit(f"{path}: missing closing front matter fence")
    metadata = json.loads(remainder[:end_index])
    body = remainder[end_index + len(marker) :]
    return metadata, body


def build_route(metadata: dict) -> str:
    slug = str(metadata["slug"]).strip("/")
    section = str(metadata["section"]).strip("/")
    if metadata["type"] == "page":
        if section in {"root", "pages", ""}:
            return f"/{slug}/"
        return f"/{section}/{slug}/"
    return f"/{section}/{slug}/"


def load_source_entries(site: dict) -> list[SourceEntry]:
    entries: list[SourceEntry] = []
    for path in sorted(CONTENT_DIR.rglob("*.md")):
        metadata, _ = parse_front_matter(path)
        status = metadata.get("status")
        if status not in SUPPORTED_STATUSES:
            raise SystemExit(f"{path}: unsupported status {status!r}")
        route = build_route(metadata)
        canonical = metadata.get("canonical") or f"{site['url'].rstrip('/')}{route}"
        entries.append(SourceEntry(route=route, canonical=canonical, status=status))
    return entries


def route_to_public_path(route: str) -> Path:
    trimmed = route.strip("/")
    if not trimmed:
        return PUBLIC_DIR / "index.html"
    if "." in Path(trimmed).name:
        return PUBLIC_DIR / trimmed
    return PUBLIC_DIR / trimmed / "index.html"


def canonical_to_public_path(url: str, site_url: str) -> Path:
    parsed = urlsplit(url)
    if parsed.scheme and parsed.netloc:
        site_base = urlsplit(site_url)
        if parsed.scheme != site_base.scheme or parsed.netloc != site_base.netloc:
            raise ValueError(f"External URL {url!r} does not map to local public output")
        route = parsed.path or "/"
    else:
        route = parsed.path or "/"
    return route_to_public_path(route)


def normalize_internal_href(href: str, *, page_route: str, site_url: str) -> str | None:
    if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        parsed = urlsplit(href)
        site = urlsplit(site_url)
        if parsed.netloc != site.netloc:
            return None
        return parsed.path or "/"
    resolved = urlsplit(urljoin(page_route, href))
    return resolved.path or "/"


def footer_fragment(html_text: str) -> str:
    match = re.search(r"<footer\b.*?</footer>", html_text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(0) if match else ""


def main() -> None:
    errors: list[str] = []
    site = load_site()

    for required_file in REQUIRED_FILES:
        if not required_file.exists():
            errors.append(f"Missing required file: {required_file.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    source_entries = load_source_entries(site)
    source_by_status: dict[str, list[SourceEntry]] = {status: [] for status in SUPPORTED_STATUSES}
    for entry in source_entries:
        source_by_status[entry.status].append(entry)

    sitemap_root = ET.fromstring((PUBLIC_DIR / "sitemap.xml").read_text(encoding="utf-8"))
    sitemap_urls = [
        loc.text or ""
        for loc in sitemap_root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]
    if not sitemap_urls:
        errors.append("Sitemap is empty")

    feed_root = ET.fromstring((PUBLIC_DIR / "feed.xml").read_text(encoding="utf-8"))
    feed_links = [item.text or "" for item in feed_root.findall("./channel/item/link")]

    html_files = sorted(PUBLIC_DIR.rglob("*.html"))
    if not html_files:
        errors.append("No generated HTML files found in public/")

    public_routes: set[str] = set()
    inspected_pages: dict[Path, PageInspector] = {}

    for html_file in html_files:
        relative = html_file.relative_to(PUBLIC_DIR).as_posix()
        route = "/"
        if relative != "index.html":
            route = "/" + relative.removesuffix("/index.html").removesuffix("index.html")
            if route.endswith(".html"):
                route = "/" + relative
            elif not route.endswith("/"):
                route += "/"
        public_routes.add(route)

        html_text = html_file.read_text(encoding="utf-8")
        inspector = PageInspector()
        inspector.feed(html_text)
        inspected_pages[html_file] = inspector

        if not inspector.title:
            errors.append(f"{relative}: missing <title>")
        if not inspector.meta_description:
            errors.append(f"{relative}: missing meta description")
        if not inspector.canonical:
            errors.append(f"{relative}: missing canonical link")
        if inspector.h1_count != 1:
            errors.append(f"{relative}: expected exactly one H1, found {inspector.h1_count}")

        lowered = html_text.lower()
        for marker in BANNED_MARKERS:
            if marker in lowered:
                errors.append(f"{relative}: contains banned marker {marker!r}")

        footer_html = footer_fragment(html_text)
        if not footer_html:
            errors.append(f"{relative}: missing footer")
        else:
            footer_lower = footer_html.lower()
            for href in REQUIRED_FOOTER_HREFS:
                if href.lower() not in footer_lower:
                    errors.append(f"{relative}: footer missing link {href}")

    for url in sitemap_urls:
        try:
            public_path = canonical_to_public_path(url, site["url"])
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not public_path.exists():
            errors.append(f"Sitemap URL maps to missing file: {url}")

    for entry in source_by_status["draft"] + source_by_status["review"]:
        expected_path = route_to_public_path(entry.route)
        if expected_path.exists():
            errors.append(f"Non-published entry leaked into public output: {entry.route}")
        if entry.canonical in sitemap_urls:
            errors.append(f"Draft/review canonical appears in sitemap: {entry.canonical}")
        if entry.canonical in feed_links:
            errors.append(f"Draft/review canonical appears in feed: {entry.canonical}")

    for entry in source_by_status["archived"]:
        expected_path = route_to_public_path(entry.route)
        if expected_path.exists():
            errors.append(f"Archived entry leaked into public output: {entry.route}")
        if entry.canonical in sitemap_urls:
            errors.append(f"Archived canonical appears in sitemap: {entry.canonical}")
        if entry.canonical in feed_links:
            errors.append(f"Archived canonical appears in feed: {entry.canonical}")

    for html_file, inspector in inspected_pages.items():
        relative = html_file.relative_to(PUBLIC_DIR).as_posix()
        page_route = "/"
        if relative != "index.html":
            page_route = "/" + relative.removesuffix("/index.html").removesuffix("index.html")
            if page_route.endswith(".html"):
                page_route = "/" + relative
            elif not page_route.endswith("/"):
                page_route += "/"
        for href in inspector.hrefs:
            internal_path = normalize_internal_href(href, page_route=page_route, site_url=site["url"])
            if internal_path is None:
                continue
            candidate = route_to_public_path(internal_path)
            if not candidate.exists():
                errors.append(f"{relative}: broken internal link {href}")

    robots_text = (PUBLIC_DIR / "robots.txt").read_text(encoding="utf-8")
    if "User-agent: *" not in robots_text or "Allow: /" not in robots_text:
        errors.append("robots.txt is missing required allow rules")
    if f"Sitemap: {site['url'].rstrip('/')}/sitemap.xml" not in robots_text:
        errors.append("robots.txt is missing the correct sitemap line")

    homepage_text = (PUBLIC_DIR / "index.html").read_text(encoding="utf-8").lower()
    for phrase in HOMEPAGE_BANNED_CTA_PHRASES:
        if phrase in homepage_text:
            errors.append(f"Homepage contains service-style CTA phrase {phrase!r}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    print("Validation passed.")


if __name__ == "__main__":
    main()
