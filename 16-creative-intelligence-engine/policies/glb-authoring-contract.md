# Semantic GLB Authoring Contract

For model-3d assets that participate in CIE mesh states, publish validation is strict.

Required authored capabilities are derived from the page's mesh-state plan and media registry:

- `KHR_materials_variants` names matching required CIE states.
- Animation names matching the mesh-state contract (for example `cie-explode-foundation`).
- Semantic node groups named `cie-group-<state>`.
- Hotspot anchor nodes named `cie-hotspot-<id>` for registered semantic hotspots.
- A resolved source URI that has already passed the publish-media integrity, provenance and license gate.

The source GLB is inspected before derivative production. Missing authored capabilities block publish rather than silently degrading a promised technical 3D presentation. Runtime fallbacks remain available for non-publish previews and for capability/reduced-motion conditions after an authored model has passed validation.
