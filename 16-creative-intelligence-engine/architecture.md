# Creative Intelligence Engine — Architecture

## 1. Position in RUOS

CIE sits between strategy/knowledge inputs and page production.

```text
Governance + Project Knowledge + Research + Approved References
                         │
                         ▼
               Creative Intelligence Engine
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
  Provider Research   Synthesis      Blocking Gate
        │                │                │
        └───────────────► Creative Blueprint
                                         │
                                  PASS / BLOCKED
                                         │
                                         ▼
                                UX/UI + Front-end Build
```

## 2. Inputs

CIE receives a `creative_request` containing:

- project and page identifier;
- page type and funnel stage;
- primary/secondary user intent;
- persona and decision context;
- brand and editorial constraints;
- approved reference URLs and reference roles;
- existing project knowledge and capability evidence;
- SEO/query requirements where relevant;
- target devices and accessibility requirements;
- implementation/runtime constraints;
- required evidence and known unknowns.

## 3. Provider layer

Providers are evidence collectors and specialist analyzers. They do not directly dictate the final design.

Recommended provider roles:

- `reference_visual_analyst`: composition, hierarchy, typography, color, depth, imagery.
- `motion_interaction_analyst`: scroll choreography, state transitions, gestures, spatial logic.
- `ux_journey_analyst`: intent alignment, cognitive load, decision sequence, CTA logic.
- `industrial_product_analyst`: structure/product anatomy, technical presentation, configurators, hotspots.
- `brand_editorial_analyst`: voice, persuasion, information hierarchy, customer-as-hero fit.
- `performance_accessibility_analyst`: mobile, reduced motion, loading cost, input modality, contrast.
- `competitive_differentiation_analyst`: sameness risk, category conventions, opportunities to diverge.

Every provider output must validate against `provider-output.schema.json` and include provenance.

## 4. Synthesis layer

The orchestrator synthesizes provider outputs into one Creative Blueprint. Synthesis resolves conflicts using this priority order:

1. governance and locked project rules;
2. user intent and conversion goal;
3. factual/technical evidence;
4. accessibility and mobile viability;
5. brand distinctiveness;
6. approved reference direction;
7. visual novelty.

Novelty never overrides usability, truth, performance or project constraints.

## 5. Creative Blueprint

The blueprint is the handoff contract to design/build. At minimum it defines:

- creative thesis;
- user journey stages;
- narrative/section architecture;
- visual system;
- motion grammar;
- interaction model;
- spatial/3D strategy;
- responsive behavior;
- content-to-visual mapping;
- evidence/provenance;
- anti-copy constraints;
- implementation recommendations;
- risks and fallbacks;
- gate status.

## 6. Reference translation model

A reference is decomposed into principles instead of copied components.

Example:

```text
NRG Build Your Data Center
  observed: staged system-building through scroll
  principle: reveal complexity progressively
  Red Umbrella translation: assemble advertising structure anatomy by scroll
  prohibited: reproducing NRG layout, assets, copy, geometry or signature sequence
```

For Red Umbrella structure pages, NRG is the primary interaction reference, while industrial references can influence materiality and modular presentation. Oryzo AI can influence transition quality and presentation pacing. Fort Vega and Sky Clinics can influence spatial scroll choreography where the page purpose justifies it.

## 7. Motion grammar

Every motion instruction must have a semantic purpose from this controlled set:

- `reveal_information`
- `show_progress`
- `show_relationship`
- `show_state_change`
- `show_scale_or_depth`
- `focus_attention`
- `transition_context`
- `simulate_configuration`

Motion with purpose `decoration_only` is not sufficient for a core interaction.

## 8. Responsive strategy

Desktop and mobile share the same narrative contract but may use different interaction mechanics.

Examples:

- pinned horizontal desktop sequence → touch-first snap/stack sequence on mobile;
- WebGL/3D exploration → lightweight pre-rendered or DOM/SVG fallback on constrained devices;
- hover hotspot → tap hotspot;
- long cinematic transition → shortened transition under reduced-motion or low-power conditions.

## 9. Blocking gate

Build is blocked when any critical condition fails, including:

- no clear user intent or conversion goal;
- no page-specific creative thesis;
- reference copying risk unresolved;
- missing mobile behavior;
- missing reduced-motion/fallback strategy for essential interactions;
- unsupported claims or invented product/technical data;
- provider outputs lack source provenance;
- blueprint fails schema validation;
- design direction degenerates to generic card-grid composition when a richer approved interaction model is required.

## 10. Output lifecycle

```text
request
  → collect
  → normalize
  → analyze in parallel
  → validate provider outputs
  → synthesize
  → score
  → run blocking gate
  → emit creative_blueprint
  → build handoff
```

A failed gate loops back only to the failed dimensions; it must not restart unrelated research.

## 11. Quality target

For Red Umbrella, the target is an Awwwards-level ambition in presentation and interaction while remaining commercially legible, responsive, evidence-based and maintainable. The engine should prevent both extremes: generic corporate templates and spectacular interactions that obscure the customer journey.
