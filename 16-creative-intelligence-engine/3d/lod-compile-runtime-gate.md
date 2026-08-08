# CIE Compile-time 3D LOD Runtime Gate

This stage wires the post-LOD approval primitive into the real RUOS build path.

## Production command contract

A build that explicitly requires validated 3D LOD delivery uses all of the following:

```bash
ruos build structures \
  --require-publish-media \
  --media-bindings .ruos/media-bindings.json \
  --produce-media \
  --require-3d-lod-qa \
  --3d-source-map .ruos/3d-sources.json \
  --3d-visual-approvals .ruos/3d-approvals.json
```

`--3d-source-map` is a JSON object keyed by CIE section ID and points to the authored DCC source used for that model section. `--3d-visual-approvals` is keyed by section ID and must carry an explicit approval, reviewer and retained comparison evidence.

## Blocking order

1. Publish-media rights/provenance/integrity validation passes.
2. Source GLB semantic authoring validation passes.
3. The deterministic 3D authoring manifest is converted into production and Blender job contracts.
4. Source/high/medium GLBs are evaluated by the post-LOD semantic, geometry and visual QA gate.
5. The gate must pass before model derivatives are eligible for runtime media delivery.
6. Generic model derivatives in the media worker report are replaced by the approved Blender high/medium LOD files.
7. Runtime delivery, camera choreography and mesh-state binding are built from those approved LOD files.
8. `assets/post-lod-gate.json` is written before runtime binding; the runtime manifest refresh therefore records and hashes it with the final production build.

## Truth policy

The presence of GLB files is not approval. Polygon reduction is not approval. A runtime model marked as post-LOD approved must be backed by a passing semantic/geometry gate plus explicit visual review evidence. If any required file, source binding, approval or semantic capability is missing, the build is rejected before 3D runtime delivery.
