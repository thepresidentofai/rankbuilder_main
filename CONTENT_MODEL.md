# Rank Builder SEO Content Model

Rank Builder SEO uses JSON front matter inside `---` fences so the build script can parse content with Python standard library only.

## Front Matter Format

Example:

```md
---
{
  "title": "How to Read an SEO Monthly Report",
  "slug": "how-to-read-an-seo-monthly-report",
  "type": "guide",
  "section": "guides",
  "description": "A buyer-defense guide to reading monthly SEO reports without getting snowed by vanity metrics.",
  "canonical": "https://rankbuilderseo.com/guides/how-to-read-an-seo-monthly-report/",
  "published": "2026-07-01",
  "modified": "2026-07-01",
  "status": "draft",
  "evidence_level": "editorial-shell",
  "risk_level": "low",
  "author": "Rank Builder SEO",
  "reviewer": "Editorial review pending",
  "sources": [],
  "related": [
    "/methodology/source-and-citation-standard/"
  ]
}
---
## Short answer

...
```

## Required Fields

- `title`
- `slug`
- `type`
- `section`
- `description`
- `published`
- `modified`
- `status`
- `evidence_level`
- `risk_level`
- `author`
- `reviewer`
- `sources`
- `related`

`canonical` is recommended. If it is omitted, the generator derives it from the site URL and output route.

## Supported Status Values

- `draft`
- `review`
- `published`
- `archived`

Only `published` entries are rendered into `public/`, included in section listings, added to `sitemap.xml`, and added to `feed.xml`.

Draft, review, and archived entries remain source-only unless the generator is deliberately changed.

## Supported Content Types

- `page`
- `guide`
- `technical-seo`
- `local-seo`
- `provider-review`
- `audit-review`
- `pricing`
- `dictionary`
- `template`
- `checklist`
- `bad-seo-pattern`
- `experiment`
- `research`

## Section Rules

- `page` content can publish to top-level routes like `/about/` or nested routes like `/methodology/source-and-citation-standard/`.
- Non-page content publishes under its `section` path and `slug`.
- Slugs should be lowercase, hyphenated, and stable.
- Only published entries should set claims, links, and metadata that are ready for public output.

## Body Structure

The generator recognizes `##` headings and can style several common sections specially:

- `Short answer`
- `Why it matters`
- `How to verify`
- `Sources and notes`
- `Related links`
- `Buyer questions`
- `Verdict`
- `Methodology`
- `Cost and effort`

Unrecognized `##` sections are still rendered as normal article sections.
