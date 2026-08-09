# CIE 3D Authoring Manifest

The 3D Authoring Manifest translates RUOS scene/state intent into a deterministic brief for Blender/glTF production.

For every section using `model-3d`, the manifest defines required semantic node names (`cie-group-{state}`), material variants (`{state}`), baked animation names (`cie-explode-{state}` with `cie-overview` for overview), semantic hotspot anchors (`cie-hotspot-{semantic-id}`), and poster/medium/high LOD deliverables.

The contract is intentionally production-facing: node and animation names must survive export, GLB 2.0 is the canonical container, `KHR_materials_variants` carries state variants, transform animations should be baked, and Draco/Meshopt compression is allowed only when semantic names and runtime compatibility are preserved.

The manifest does not claim that a model has been authored. It specifies what the model-production team or a future automated Blender/glTF worker must produce. The existing semantic GLB validation gate remains the source of truth before publish and blocks missing authored capabilities.

Pipeline position:

`Scene/State Orchestration -> 3D Authoring Manifest -> Blender/glTF Authoring -> GLB Semantic Validation -> Publish Media Gate -> LOD/Derivative Production -> Runtime 3D`
