# CIE LOD Build Integration

This layer closes the schema gap between the 3D production job planner and the executable Blender worker, then applies the post-LOD QA gate before runtime delivery.

## Execution order

1. Build 3D production jobs from the authoring manifest.
2. Normalize `output`, `poster_output`, and `lod_outputs` into the Blender worker `outputs` contract.
3. Attach the active deterministic LOD policy.
4. Execute Blender only when a real source is bound.
5. Validate source/high/medium GLBs after generation.
6. Require semantic preservation, geometry hierarchy, bounded drift, and visual approval evidence.
7. Write the post-LOD gate report as a production artifact.
8. Only a `pass` report may proceed to runtime media delivery.

## Compiler and CLI binding

`ruos-cie build` and the standard `ruos build` accept `--post-lod-gate <artifact.json>` together with `--require-publish-media --produce-media`. When derivative production contains any `model-3d` result, the gate artifact is mandatory; omitting it blocks the build.

The compiler replaces model runtime variants with the exact approved high/medium GLBs named by the gate, verifies that retained visual evidence exists, and copies the gate plus evidence into `assets/3d-qa/`. Runtime binding therefore cannot select an unapproved derivative. The final `build-manifest.json` records `cie_post_lod_qa`, while every copied gate, evidence file, and delivered GLB is included in the artifact SHA-256 map.

## Truth constraints

- A missing source is blocking.
- A missing Blender executable is blocking when execution is requested.
- A generated LOD is not approved only because it exists or is smaller.
- Human visual approval remains mandatory until a separately validated perceptual QA system is introduced.
- A passing report whose GLB or visual-evidence file is missing is blocking.
- A gate section that does not exactly cover the model sections entering runtime delivery is blocking.
