---
name: write-blog-article
description: Research, write, implement, and optimize French SEO blog articles for the Acquora marketing site, including trustworthy institutional sourcing, coherent cover visuals, article-list integration, and technical SEO. Use when creating or substantially updating an Acquora blog article or its blog listing.
---

# Write an Acquora blog article

Create a useful, source-backed article for French home buyers and ship it as a complete part of the Next.js blog. Optimize discovery and search presentation, but prioritize the reader's decision and trust over keyword repetition or content volume.

## Before writing

1. Read every applicable `AGENTS.md`, including the frontend and marketing instructions.
2. Inspect the current blog routes, article model, list and category pages, metadata conventions, visual assets, styles, sitemap, and internal links. Extend the established system instead of creating a parallel one.
3. Read the relevant versioned Next.js documentation in `frontend/node_modules/next/dist/docs/` before changing framework APIs. This repository may use behavior newer than prior knowledge.
4. Clarify from the request or infer conservatively:
   - the primary search intent and query;
   - the French home-buyer audience and decision the page should support;
   - the article category, evergreen or time-sensitive nature, and useful internal links.
5. Browse the current web for the query landscape and factual research. Search results may inform coverage and vocabulary, but never copy a competitor's structure or wording.

If the topic is materially underspecified and different interpretations would produce different articles, ask one concise question. Otherwise proceed using a clearly stated, low-risk assumption.

## Research and source policy

Treat legal, financial, energy, diagnostic, and safety claims as high-stakes information.

- Prefer primary French institutional sources: `legifrance.gouv.fr`, `service-public.fr`, `ecologie.gouv.fr`, `economie.gouv.fr`, `ademe.fr`, `anil.org`, `insee.fr`, `data.gouv.fr`, `georisques.gouv.fr`, local prefectures, and other directly responsible public bodies.
- Use the source closest to the fact. Cite Légifrance for legal text, the responsible administration for a procedure, and the original public dataset for a statistic.
- Do not use estate agents, brokers, insurers, comparison sites, software vendors, competitors, affiliate pages, or other commercial company websites as factual sources.
- A search-result snippet is not a source. Open the page and verify that it supports the claim.
- Check scope, effective date, geographic applicability, definitions, units, and whether a rule has changed. Prefer current pages and record the access or update date when freshness matters.
- If reliable institutional support cannot be found, omit the claim or label the uncertainty explicitly. Never fill gaps with plausible facts.
- Distinguish a legal requirement, an official recommendation, a practical suggestion, and an Acquora interpretation.
- Paraphrase sources. Quote only when the exact wording is genuinely useful, keep quotations short, and link to the exact source page.
- Attach citations to the claims they support and finish with a compact `Sources officielles` section. Descriptive link labels are required. Do not use raw URLs or vague labels such as `cliquez ici`.

Do not present the article as legal, notarial, engineering, energy-audit, or financial advice. Add a concise contextual disclaimer when a reader could reasonably mistake it for such advice.

## SEO strategy

Build one page around one clear intent and a coherent family of related questions.

- Choose a natural primary query and a small set of closely related terms from actual user language. Do not stuff keywords or force exact-match repetitions.
- Make the title and single H1 descriptive, specific, and aligned with the answer. Avoid clickbait, exaggerated promises, and generic headings.
- Answer the central question near the top, then develop the reasoning, exceptions, actions, and source-backed details.
- Use a semantic H2 and H3 hierarchy. Add a table of contents with anchor links when the article is long enough to benefit from one.
- Prefer original value such as a decision checklist, source synthesis, worked example, comparison table, timeline, or explanation of how documents relate. Do not merely rewrite official pages.
- There is no target word count. Cover the intent completely, then stop.
- Add contextual internal links to relevant Acquora articles and marketing pages. Use descriptive anchor text and avoid repetitive promotional links.
- End with a useful next step. A restrained Acquora call to action is appropriate when it follows naturally from the article.

For each article, implement framework-native SEO using the repository's current conventions:

- a stable, short, lowercase French slug without accents;
- unique title and meta description;
- canonical URL;
- Open Graph and social metadata with the article cover image;
- accurate `datePublished` and `dateModified` values. Never change a date solely to simulate freshness;
- `Article` or `BlogPosting` structured data and breadcrumb structured data when the visible page supports them;
- FAQ structured data only when the page contains a genuine, visible FAQ and current search-engine guidance supports its use;
- inclusion in static parameters, sitemap, feeds, or other discovery mechanisms that the repository actually uses.

Structured data must match visible content exactly. Validate its URLs, dates, author or publisher, headline, description, and image. Do not invent reviews, ratings, authorship, credentials, or publication data.

## French editorial style

- Write entirely in clear, idiomatic French for a non-specialist home buyer.
- Address the reader consistently, normally with `vous`. Explain unavoidable technical or administrative terms on first use.
- Favor short sentences, concrete verbs, informative headings, and practical examples.
- Use correct French accents, punctuation, non-breaking spacing where the codebase supports it, euro notation, and unambiguous dates.
- Do not use an em dash, an en dash as an aside, or a double hyphen as punctuation. Rewrite with commas, parentheses, a colon, or separate sentences.
- Avoid filler, generic AI phrasing, unsupported superlatives, fear-based framing, and promises of certainty.
- State limits and exceptions close to the claim they qualify.

## Article experience

The page should feel like a trustworthy inspection guide, not a wall of prose or an AI demo.

Include when useful:

- a short standfirst that says what the reader will learn;
- publication or substantive-update date;
- a readable article column with generous spacing;
- callouts for `À retenir`, `À vérifier`, examples, definitions, or caveats;
- comparison tables that remain usable on small screens;
- a clear official-sources section;
- related articles selected by topic, not at random.

Keep content server-rendered by default. Add client-side code only for a real interaction. Preserve accessibility, keyboard use, visible focus states, responsive behavior, and reduced-motion preferences.

## Visual system

Every article must have a cover visual that also appears in the root blog list. The complete grid should look like one editorial collection, inspired by the consistency and scanability of Pretto's article listing, without copying its assets or layout.

- Inspect existing blog covers first. Reuse their aspect ratio, palette, art direction, framing, and asset naming.
- If no system exists, establish one reusable direction for the collection: a fixed aspect ratio, restrained Acquora palette, consistent background treatment, simple property-related subjects, and one recognizable composition grammar.
- Give each article a distinct subject or motif while keeping the family resemblance. Avoid generic stock-photo randomness.
- Prefer local optimized assets. Never hotlink a third-party image. Record licensing or provenance when an external asset is used.
- Provide meaningful alternative text for informative images and empty alternative text for purely decorative ones.
- Use responsive `next/image` sizing for raster assets and reserve space to prevent layout shift.
- Ensure the social preview image has a suitable wide crop and remains legible at small sizes. Do not bake essential article text into the image.
- Never set an accent border in the UI.

Code-native React, SVG, or CSS illustrations are encouraged for simple shapes, document motifs, timelines, and diagrams. They should reuse design tokens and shared components instead of becoming one-off decoration. If a static cover asset is required for social metadata, provide a corresponding local raster or SVG asset.

Charts are allowed only when they help answer the reader's question:

- derive every value from cited data and show the period, unit, and source near the chart;
- never invent or visually exaggerate values;
- use semantic labels, sufficient contrast, and an accessible table or textual equivalent;
- avoid adding a chart library when a small server-rendered React or SVG component is sufficient;
- keep decorative shapes `aria-hidden` and keep essential information available as text.

## Repository integration

An article is not complete until readers and crawlers can discover it.

- Add it to the root `/blog` listing with cover, title, concise excerpt, category, and honest date.
- Add it to the relevant category view when categories exist.
- Prefer a single typed article catalog as the source for listing cards, route generation, metadata, and related content when the repository does not already have an equivalent source of truth.
- Avoid duplicating article metadata across files. Preserve stable URLs when updating existing content.
- Check that article cards use valid heading order, linked images, useful alt text, responsive crops, and coherent heights.
- Keep the article and listing visually aligned with the existing marketing design system.

Do not introduce a CMS, MDX stack, chart library, image service, analytics product, or other dependency solely for one article. Use the current architecture unless the request explicitly expands the scope.

## Verification

Before finishing:

1. Recheck every material claim against its linked source and remove unsupported statements.
2. Confirm the H1, title, description, slug, canonical, image, dates, internal links, and structured data agree.
3. Confirm the article appears on `/blog` and the appropriate category page, with a coherent cover card.
4. Check mobile and desktop layout, image crops, overflow, focus states, and reduced motion.
5. Run the repository's relevant lint, typecheck, tests, and production build when practical. Report any check not run and why.
6. Review the rendered French for clarity, accents, source placement, uncertainty, and prohibited dash punctuation.

In the handoff, state the target query and intent, summarize the article and visual direction, list the principal official sources, link the changed files, and report validation results. Mention unresolved uncertainty plainly.
