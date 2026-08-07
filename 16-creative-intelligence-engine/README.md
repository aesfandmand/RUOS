# Creative Intelligence Engine (CIE)

## Purpose

The Creative Intelligence Engine turns approved visual references, brand constraints, page intent, market evidence, UX requirements and technical capabilities into a deterministic **Creative Blueprint** before design or code is allowed to start.

CIE is a pre-build intelligence layer for RUOS. It does not copy reference websites. It extracts reusable design principles such as scroll choreography, spatial depth, narrative pacing, typography behavior, industrial/product presentation, interaction logic and motion grammar, then maps them to the target page.

## Core contract

No production page may enter build when `pre-build-blocking-gate.yaml` returns `blocked`.

The engine must produce:

1. a normalized creative brief;
2. provider research outputs with source provenance;
3. a scored and synthesized Creative Blueprint;
4. a page-specific motion and interaction strategy;
5. mobile/desktop behavior rules;
6. accessibility and performance constraints;
7. evidence that approved references were analyzed rather than imitated;
8. a final blocking-gate decision.

## Directory

```text
16-creative-intelligence-engine/
├── README.md
├── architecture.md
├── orchestration/
│   ├── creative-intelligence-orchestrator.yaml
│   └── provider-pipeline.yaml
├── schemas/
│   ├── creative-blueprint.schema.json
│   └── provider-output.schema.json
└── policies/
    └── pre-build-blocking-gate.yaml
```

## Red Umbrella reference direction

The following approved references define the quality bar and interaction direction for Red Umbrella website work. They are references, not templates to copy:

- Fort Vega — scroll-led, 3D and interactive choreography.
- Sky Clinics — cinematic scroll-driven spatial storytelling.
- Bucks Sauce — bold product presentation, animated product grids/sliders and unconventional navigation.
- NRG Build Your Data Center — primary reference for structure/catalog pages: staged scroll, nodes, systems thinking and virtual-tour logic.
- Oryzo AI — primary reference for presentation language: cinematic transitions, 3D/2D continuity and reveal systems.
- Xurya Manufacture — industrial/manufacturing visual language.
- Construction Insurtech B2B — architectural grid, modular B2B composition and heavy-duty industrial clarity.

## Non-negotiables

- Reference-led, never reference-copied.
- Customer journey and page intent precede visual novelty.
- Motion must communicate hierarchy, state or progress; decorative motion alone is insufficient.
- Desktop and mobile are one responsive system.
- Reduced-motion, touch behavior, readable typography and interaction fallbacks are mandatory.
- Unsupported performance, market, technical or product claims block build.
- Every blueprint must be machine-valid against `schemas/creative-blueprint.schema.json`.

## Gate states

- `pass`: build may begin.
- `pass_with_conditions`: build may begin only with explicit conditions attached to the blueprint.
- `blocked`: build is prohibited until all blocking failures are resolved.

## Version

Initial architecture: CIE v1.
