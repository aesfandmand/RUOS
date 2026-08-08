# CIE 3D Visual Evidence Workflow

The post-LOD gate requires human visual approval. This workflow creates consistent evidence for that review without pretending an automated image metric is a human decision.

## Capture contract

For each model section and each of `source`, `high`, and `medium`, RUOS plans the same three camera views:

- front
- three-quarter
- side

Every level in a view uses the same camera parameters, 55mm lens, lighting setup, background and 768×768 PNG output. The Blender evidence renderer imports each GLB into a clean scene, derives the model bounds, places the camera deterministically and renders the evidence image.

Run the capture as a separate review-preparation stage after the source/high/medium GLBs exist:

```bash
ruos capture-3d-evidence structures \
  --3d-source-map .ruos/3d-sources.json
```

`ruos-cie capture-3d-evidence` exposes the same contract. The command writes the compile plan, render plan, execution report, automated comparison report and a visual-approval template under `.ruos/3d-evidence/`. It never marks the template approved.

## Automated signal

After rendering, RUOS computes normalized mean absolute image difference between the source render and each LOD render. Default advisory thresholds are:

- High LOD: 0.08
- Medium LOD: 0.14

These thresholds are an investigation signal only. They do not approve or reject visual quality by themselves because lighting, material export and topology changes can alter pixels without necessarily making the model unacceptable, and small pixel differences can still hide important semantic defects.

## Human approval

The evidence evaluator produces a review template with:

- `approved: false`
- no reviewer by default
- all evidence image URIs retained
- the automated signal retained
- an empty review-notes field

A human reviewer must explicitly set approval and reviewer identity before the existing post-LOD production gate can pass.

At production build time every approved evidence URI must resolve to a real file. RUOS copies those files into `assets/3d-qa/<section>/`, rewrites the post-LOD artifact to the retained URIs and includes their SHA-256 values in `build-manifest.json`.

## Truth rule

`evidence-ready` means only that the required comparison images exist and remain inside advisory similarity thresholds. It MUST NOT be interpreted as production approval. Production approval remains the combination of semantic GLB validation, geometry QA, retained visual evidence and explicit reviewer approval.
