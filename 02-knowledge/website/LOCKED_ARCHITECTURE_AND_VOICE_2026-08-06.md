# Locked Website Architecture and Voice Decisions

Status: **SOURCE OF TRUTH**
Owner-approved date: 2026-08-06

## 1. Intent architecture

| Route | Primary audience | Mission |
|---|---|---|
| Investment hub | space owners, municipalities, organizations | feasibility, placement, financing, construction, operation and transfer |
| Indoor structure purchase | defined business personas | purchase, build and install indoor advertising structures |
| Outdoor structure purchase | municipalities, organizations and entities able to install | purchase, build and install outdoor advertising structures |
| Billboard rental and campaign execution | advertisers | choose and rent existing media positions; independent journey |
| Structures | all research and comparison users | master encyclopedia and catalog; not the primary sales, rental or investment page |

The latest owner decision overrides older conflicting architecture.

## 2. Structures as the master entity layer

`/structures` is the canonical knowledge and catalog surface for advertising structures. It may contain all relevant information, organized for discovery and reuse:

- photographs, videos and models;
- engineering drawings, installation details and foundations;
- objectives, use cases and suitable locations;
- technical, media, spatial and commercial attributes;
- dimensions and aspect ratio;
- face count;
- horizontal/vertical orientation;
- front-lit, back-lit and other lighting models;
- indoor/outdoor context;
- ownership, purchase, rental, investment and organizational-sale relations.

Pages for products, rental, investment, institutional sales, blog and video must consume views of the same canonical entities instead of duplicating contradictory data.

Each structure record may route users to relevant purchase, investment, rental or organizational paths, but `/structures` must not compete with those pages for their conversion intent.

## 3. Knowledge graph is mandatory at page definition time

Knowledge graph is not an end-of-build add-on. Every page specification must define:

- pillar;
- cluster and topic family;
- page intent and persona;
- entities consumed and entities produced;
- internal graph relations;
- structured-data/schema requirements;
- source records reused from the canonical structure graph.

## 4. Capability layer

Every page must state:

> What can Red Umbrella do, for which problem, using which assets and evidence, and toward which conversion path?

Capability is not a decorative service list. It must be connected to:

- a real audience problem;
- operational assets and delivery ability;
- evidence and proof;
- the correct journey and CTA;
- the page pillar and knowledge graph.

## 5. Supporting content

All important pages should include relevant, non-forced access to:

- blog clusters;
- videos;
- case studies or observable evidence;
- related structure records;
- a clear next step.

## 6. Locked brand voice

The nine-stage Red Umbrella voice calibration is binding.

- Unproven outcomes: only observable effects; no unsupported numbers or certainty claims.
- Storytelling: short, real and used mainly at the beginning of important sections.
- CTA: calm, direct and proportional to user need.
- Never manufacture urgency, pressure, scarcity or fake deadlines.
- Avoid generic promotional language, inflated claims and empty authority signals.
- Preserve the owner-approved Persian rhythm, vocabulary and editorial tone.

## 7. Mandatory architecture review gate

Before any new page is designed or built:

1. review the site architecture layer by layer;
2. identify and mark obsolete conflicting decisions;
3. revise the affected layer;
4. obtain owner approval;
5. lock the approved layer;
6. only then start page production.

Design before architecture approval is prohibited.

## 8. Reference system

Approved Awwwards, Dribbble and product-page references are executable design inputs, not vague inspiration. They must be translated into explicit decisions for hierarchy, typography, composition, scroll narrative, motion, image/text ratio and interaction. Copying is prohibited; quality regression is also prohibited.