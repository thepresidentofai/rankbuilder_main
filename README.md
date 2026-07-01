# Rank Builder SEO Site

Static starter for `rankbuilderseo.com`.

## Purpose

Rank Builder SEO is the controlled SEO how-to, knowledge-base, and future agency funnel property. It should be safe to use for experiments that would be too risky to run on a client site.

## Deployment

Target platform: Cloudflare Pages

Build settings:

| Setting | Value |
| --- | --- |
| Framework preset | `None` |
| Build command | blank |
| Build output directory | `public` |
| Production branch | `main` |

## Local Structure

- `public/` contains deployable static files.
- `content/` contains source briefs and future article drafts.
- `experiments/` tracks SEO tests, hypotheses, and outcomes.

## First Launch Checklist

- Create GitHub repo `thepresidentofai/rankbuilderseo-site`.
- Push this repo to `main`.
- Create Cloudflare Pages project `rankbuilderseo`.
- Attach `rankbuilderseo.com` and `www.rankbuilderseo.com`.
- Enable separate Cloudflare Web Analytics for this project.
