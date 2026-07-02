# Rank Builder SEO

Rank Builder SEO is a static publishing system for `rankbuilderseo.com`.

It is an independent SEO research lab, buyer-defense resource, technical SEO knowledge base, provider-review archive, audit-review archive, pricing transparency project, experiment log, and bad-pattern library.

It is not an agency landing page, lead funnel, affiliate farm, fake review site, or AI slop content mill.

## Deployment model

The repo builds static HTML into `public/` and commits that output so Cloudflare Pages can deploy it with no build step.

### Current Cloudflare Pages settings

| Setting | Value |
| --- | --- |
| Framework preset | `None` |
| Build command | blank |
| Build output directory | `public` |
| Production branch | `main` |

The repo currently commits generated public output so Cloudflare Pages can deploy with a blank build command. If Cloudflare build settings are later enabled, confirm the environment supports the documented build command before changing production settings.

## What lives where

- `content/` contains source content with JSON front matter inside `---` fences.
- `data/` contains site metadata, navigation, section definitions, and experiment registry data.
- `templates/` contains the HTML shell and reusable partials used by the generator.
- `tools/build-site.py` renders published content into `public/`.
- `tools/validate-site.py` checks generated routes, metadata, links, sitemap, RSS, footer links, and draft leakage.
- `tools/new-content.py` scaffolds draft content files with the required metadata and headings.
- `public/` contains committed deploy output for Cloudflare Pages.

## Build

Run:

```powershell
python tools/build-site.py
```

The build script:

- reads metadata from `data/`
- reads source content from `content/`
- renders HTML with `templates/`
- generates section indexes
- generates `public/sitemap.xml`
- generates `public/feed.xml`
- regenerates `public/robots.txt`
- recreates legacy `/articles/` migration pages

Only `status: "published"` content is rendered into `public/`.

## Validate

Run:

```powershell
python tools/validate-site.py
```

Validation fails nonzero if the generated site is missing required files or contains broken internal links, missing metadata, multiple H1 tags, draft leakage, banned placeholder markers, missing footer links, or homepage service-style CTA language.

## Create new content

Example:

```powershell
python tools/new-content.py guide "How to Read an SEO Monthly Report"
```

Supported scaffold types:

- `guide`
- `technical-seo`
- `local-seo`
- `provider-review`
- `audit-review`
- `pricing`
- `dictionary`
- `bad-seo-pattern`
- `experiment`
- `research`
- `template`
- `checklist`

The scaffold script:

- creates a lowercase hyphenated slug
- writes a draft file into the correct `content/` directory
- fills the required metadata fields
- adds required heading sections with draft `TODO` markers
- asks before overwriting an existing file

## Draft and publish workflow

- Drafts use `status: "draft"`.
- Review-stage content uses `status: "review"`.
- Published content uses `status: "published"`.
- Archived content uses `status: "archived"`.

Only published pages are generated into `public/`, included in section indexes, included in `sitemap.xml`, and included in `feed.xml`.

Draft files may contain `TODO` markers. Public generated files must not.

## Sitemap and RSS

`tools/build-site.py` generates both files from content metadata:

- `public/sitemap.xml` includes canonical URLs for generated public pages and excludes drafts and archived entries.
- `public/feed.xml` includes the latest published content entries and excludes drafts, archived entries, and section indexes.

Do not hand-maintain either file after changing content or routes. Rebuild the site instead.

## Legacy URL preservation

The current shell preserves these legacy article URLs as migration pages with canonical links and meta refresh:

- `/articles/technical-seo-baseline-checklist/` -> `/guides/technical-seo-baseline-checklist/`
- `/articles/cloudflare-pages-seo-test-plan/` -> `/experiments/rb-exp-001-title-format-baseline/`

If additional URLs move later, preserve them deliberately instead of silently breaking old links.

## Publishing guardrails

Do not publish:

- SEO service advertising
- book-a-call or hire-us CTAs on editorial pages
- fake testimonials, logos, awards, or proof
- fake provider rankings or star ratings
- unsupported factual claims
- unsupported named-company accusations
- affiliate links or ads before trust and disclosure standards are mature
- placeholder public pages

Start with `CONSTITUTION.md`, `CONTENT_MODEL.md`, and `CONTENT_QA_CHECKLIST.md` before changing the publishing rules.
