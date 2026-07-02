---
{
  "title": "Cloudflare Pages SEO Baseline",
  "slug": "cloudflare-pages-seo-baseline",
  "type": "technical-seo",
  "section": "technical-seo",
  "description": "A practical baseline for checking a static Cloudflare Pages deployment before deeper SEO experiments begin.",
  "canonical": "https://rankbuilderseo.com/technical-seo/cloudflare-pages-seo-baseline/",
  "published": "2026-07-01",
  "modified": "2026-07-01",
  "status": "published",
  "evidence_level": "starter-guide",
  "risk_level": "low",
  "author": "Rank Builder SEO",
  "reviewer": "Editorial review",
  "sources": [
    "https://developers.cloudflare.com/pages/",
    "https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap"
  ],
  "related": [
    "/guides/technical-seo-baseline-checklist/",
    "/experiments/rb-exp-001-title-format-baseline/",
    "/dictionary/robots-txt/"
  ]
}
---
## Short answer

A Cloudflare Pages baseline starts with the same crawl and metadata checks as any static site, then adds deployment-specific checks for public routes, canonical consistency, headers, redirects, and whether the committed `public/` output matches what the generator is supposed to build.

## Why it matters

Static hosting removes some sources of rendering noise, but it does not remove deployment mistakes. A clean static stack is only useful if the public paths, metadata, and indexable pages match the intended output.

## How to verify

1. Confirm the generated `public/` output includes the intended HTML, sitemap, feed, and `robots.txt`.
2. Confirm public routes resolve as expected after deployment.
3. Confirm canonical URLs point to the intended production paths.
4. Confirm legacy URLs either redirect or publish a moved notice cleanly.
5. Confirm section indexes do not leak draft content.

## Sources and notes

- Cloudflare Pages documentation is relevant for the platform model.
- Google Search Central documentation remains relevant for sitemap and crawl-facing behavior.
- This page is about baseline verification, not ranking claims.

## Related links

- [Technical SEO Baseline Checklist](/guides/technical-seo-baseline-checklist/)
- [RB-EXP-001: Title Format Baseline](/experiments/rb-exp-001-title-format-baseline/)
- [robots.txt](/dictionary/robots-txt/)
