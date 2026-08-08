# Post-LOD QA

Every generated high/medium GLB remains provisional until three independent gates pass.

1. **Semantic revalidation** reruns the GLB authoring contract against each optimized file. Required material variants, animations, semantic groups, and hotspot anchors must still exist.
2. **Geometry integrity** compares POSITION accessor counts and model bounds. Medium must be lighter than high, high lighter than source, and normalized bounds drift must remain within policy.
3. **Visual review** requires retained comparison evidence plus an explicit reviewer approval. Geometry reduction is not treated as proof of visual equivalence.

The gate is intentionally blocking. A smaller file that loses a hotspot, exploded-state animation, semantic group, or visible fidelity is not a valid production optimization.
