from ruos.cli import _parser
from ruos.cie_cli import _parser as _cie_parser


def test_build_cli_exposes_publish_media_and_lod_gate_flags():
    args = _parser().parse_args([
        "build", "structures",
        "--require-publish-media",
        "--media-bindings", ".ruos/media-bindings.json",
        "--produce-media",
        "--require-3d-lod-qa",
        "--3d-source-map", ".ruos/3d-sources.json",
        "--3d-visual-approvals", ".ruos/3d-approvals.json",
    ])
    assert args.require_publish_media is True
    assert args.produce_media is True
    assert args.require_3d_lod_qa is True
    assert args.media_bindings.endswith("media-bindings.json")
    assert args.three_d_source_map.endswith("3d-sources.json")
    assert args.three_d_visual_approvals.endswith("3d-approvals.json")


def test_both_clis_expose_visual_evidence_capture():
    argv = ["capture-3d-evidence", "structures", "--3d-source-map", ".ruos/3d-sources.json"]
    args = _parser().parse_args(argv)
    cie_args = _cie_parser().parse_args(argv)
    assert args.command == cie_args.command == "capture-3d-evidence"
    assert args.three_d_source_map == cie_args.three_d_source_map == ".ruos/3d-sources.json"
