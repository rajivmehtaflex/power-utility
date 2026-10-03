"""Strict-TDD contract tests for the explainify video renderer template.

Written FIRST (plan milestone M2, first checkbox) against the stable template
interface of plan section 6, BEFORE scripts/render_video.py exists:

- validate_storyboard(data, schema) -> None
    Raises a readable ValueError (naming the offending field/id/value) for
    schema violations and for the three cross-field rules that JSON Schema
    cannot express: unique scene ids, claim references resolving into
    brief.claims, and a 60-second total-duration ceiling. Also rejects
    zero, negative, and non-finite (NaN/inf) scene durations.
- main(argv=None) -> int
    --check-only validates without rendering; --output rejects an existing
    path before any rendering unless --overwrite was explicitly passed;
    --self-test exercises an in-memory fixture and encodes nothing.
- draw_scene(ax, scene, progress, brief) -> None
    Generic, topic-neutral scene drawing on a matplotlib Axes.

Storyboards under test validate against the REAL packaged schema at
assets/storyboard.schema.json (loaded via Path(__file__), never a copy), and
the valid fixture mirrors the frozen generic example in
docs/superpowers/verification/explainify/cases.md section 3 ("Why seasons
occur"). No network access; all writes stay inside TemporaryDirectory()s.
Every test is independent; the only slow tests are the two real encodes in
MainOutputGuardTests (about 1 s of video at 30 fps).
"""
import contextlib
import copy
import io
import json
import os
import shutil
import struct
import sys
import tempfile
import time
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PACKAGE_ROOT / "scripts"
SCHEMA_PATH = PACKAGE_ROOT / "assets" / "storyboard.schema.json"
sys.path.insert(0, str(SCRIPTS))

import render_video as rv  # noqa: E402

# Minimal-but-real generic storyboard, mirroring the frozen "Why seasons occur"
# example from docs/superpowers/verification/explainify/cases.md section 3.
# It satisfies the schema plus all three cross-field rules: unique scene ids,
# claim ids that resolve into brief.claims, and 21 s total duration.
_VALID_STORYBOARD = {
    "schema_version": "1.0",
    "brief": {
        "title": "Why seasons occur",
        "source": {
            "kind": "topic",
            "requested_location": None,
            "resolved_location": None,
            "source_title": None,
            "retrieval_status": "not-applicable",
            "retrieved_at": None,
        },
        "audience": "A curious reader unfamiliar with why seasons occur.",
        "learning_objective": "Explain that Earth's axial tilt, not distance from the Sun, causes seasons.",
        "prerequisites": [
            "Earth orbits the Sun once per year",
            "Earth spins around its own axis once per day",
        ],
        "terms": [
            {"term": "axis", "definition": "The imaginary line Earth spins around."},
            {
                "term": "axial tilt",
                "definition": "The angle between Earth's axis and the line perpendicular to its orbit plane.",
            },
        ],
        "core_claim": (
            "Seasons occur because Earth's axis is tilted, so each hemisphere gets more "
            "direct sunlight and longer days during the part of the orbit where it leans "
            "toward the Sun."
        ),
        "mechanism": [
            {"step": 1, "description": "Earth's axis stays tilted about 23.4 degrees and keeps pointing the same way while Earth orbits the Sun."},
            {"step": 2, "description": "The hemisphere tilted toward the Sun gets sunlight at a steeper angle and longer days."},
            {"step": 3, "description": "More energy per day piles up over weeks and becomes summer; the opposite hemisphere gets less and has winter."},
        ],
        "claims": [
            {
                "id": "claim-1",
                "statement": "Seasons are caused by Earth's axial tilt, not by changes in Earth's distance from the Sun.",
                "origin": "model-knowledge",
                "qualifications": [
                    "Earth's distance from the Sun does change during the year, but that change is not what causes seasons.",
                    "The two hemispheres have opposite seasons at the same time.",
                ],
            },
            {
                "id": "claim-2",
                "statement": "Earth's axis is tilted by about 23.4 degrees relative to the perpendicular of its orbital plane.",
                "origin": "model-knowledge",
            },
            {
                "id": "claim-3",
                "statement": "A hemisphere tilted toward the Sun receives more direct sunlight and longer days, which accumulate into its warm season.",
                "origin": "model-knowledge",
            },
        ],
        "example": {
            "summary": "Flashlight spot: the same beam makes a small bright circle on a wall when held straight, and a larger dimmer ellipse when tilted.",
            "value_origin": "illustrative",
            "detail": "The beam spreads over more area when tilted, so each unit of area gets less light, exactly like sunlight hitting a tilted hemisphere.",
            "calculation": "If a fixed amount of light L spreads over area A when straight and over 2A when tilted, each unit of area receives L/A versus L/2A, half as much.",
        },
        "analogy": {
            "description": "Sunlight on a tilted hemisphere behaves like a flashlight beam tilted against a wall: the light spreads out, so it is less intense per unit of area.",
            "stops_matching": "A flashlight dims only because its light spreads; sunlight keeps the same total power before spreading, and the analogy says nothing about longer summer days.",
        },
        "must_preserve": [
            "The negation: tilt is the cause, distance from the Sun is not.",
            "The approximate value 23.4 degrees is not rounded into a different claim.",
            "The hemispheres have opposite seasons at the same time.",
        ],
        "omissions": [
            "Calendar definitions of solstices and equinoxes.",
            "Climate effects such as oceans, weather, and lag between sunlight and warmest days.",
        ],
    },
    "render": {
        "width": 1280,
        "height": 720,
        "fps": 30,
        "title": "Why seasons occur",
    },
    "scenes": [
        {
            "id": "scene-1-misconception",
            "duration_seconds": 6,
            "purpose": "Name the common misconception and state the correct cause.",
            "on_screen_text": "Closer to the Sun in summer?\nNo. The cause is Earth's tilt.",
            "visual_intent": "Show the Sun and Earth's orbit ring with Earth's axis visibly tilted; draw then cross out an annotation saying the cause is distance.",
            "claim_ids": ["claim-1"],
        },
        {
            "id": "scene-2-tilt",
            "duration_seconds": 8,
            "purpose": "Quantify the tilt and show it keeps a fixed direction through the orbit.",
            "on_screen_text": "Axis tilted about 23.4 degrees,\nsame direction all year",
            "visual_intent": "Move Earth along its orbit while its tilted axis arrow stays parallel to itself; label the 23.4-degree angle between the axis and the orbit's perpendicular.",
            "claim_ids": ["claim-2"],
        },
        {
            "id": "scene-3-energy",
            "duration_seconds": 7,
            "purpose": "Connect the tilt to sunlight concentration, day length, and the seasons.",
            "on_screen_text": "Tilted toward the Sun:\nmore direct light, longer days, summer",
            "visual_intent": "Parallel light rays hit a tilted globe; rays concentrate on the hemisphere tilted toward the Sun and spread out on the other; fade in summer and winter labels on opposite sides.",
            "claim_ids": ["claim-3", "claim-1"],
        },
    ],
}


def load_schema() -> dict:
    """Load the real packaged schema; tests never validate against a copy."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def make_storyboard() -> dict:
    """A fresh, independently mutable valid storyboard (deep copy each call)."""
    return copy.deepcopy(_VALID_STORYBOARD)


def make_tiny_storyboard() -> dict:
    """Two scenes of 0.5 s (1 s total) so real render tests stay fast."""
    storyboard = make_storyboard()
    storyboard["scenes"] = storyboard["scenes"][:2]
    for scene in storyboard["scenes"]:
        scene["duration_seconds"] = 0.5
    return storyboard


def write_storyboard(directory: Path, storyboard: dict, name: str = "storyboard.json") -> Path:
    path = directory / name
    path.write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
    return path


def run_main(argv: list[str]):
    """Call rv.main capturing stdout+stderr.

    Returns (return_code, combined_text). If main raises instead of returning
    a nonzero code, the return code is None and the exception text (plus any
    output produced so far) is included in combined_text, so callers can
    accept either reporting style.
    """
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = rv.main(list(argv))
    except Exception as exc:  # main may raise rather than return nonzero
        return None, f"{type(exc).__name__}: {exc}\n{out.getvalue()}{err.getvalue()}"
    return code, out.getvalue() + err.getvalue()


class ValidateStoryboardTests(unittest.TestCase):
    """validate_storyboard: schema layer plus the three programmatic cross-field rules."""

    def setUp(self):
        self.schema = load_schema()

    def test_valid_storyboard_passes(self):
        self.assertIsNone(rv.validate_storyboard(make_storyboard(), self.schema))

    def test_zero_duration_rejected(self):
        storyboard = make_storyboard()
        storyboard["scenes"][0]["duration_seconds"] = 0
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn("duration", str(ctx.exception).lower())

    def test_negative_duration_rejected(self):
        storyboard = make_storyboard()
        storyboard["scenes"][1]["duration_seconds"] = -3.5
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn("duration", str(ctx.exception).lower())

    def test_nan_duration_rejected(self):
        storyboard = make_storyboard()
        storyboard["scenes"][0]["duration_seconds"] = float("nan")
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn("duration", str(ctx.exception).lower())

    def test_inf_duration_rejected(self):
        storyboard = make_storyboard()
        storyboard["scenes"][2]["duration_seconds"] = float("inf")
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn("duration", str(ctx.exception).lower())

    def test_total_duration_over_sixty_seconds_rejected(self):
        storyboard = make_storyboard()
        for scene in storyboard["scenes"]:
            scene["duration_seconds"] = 25  # 3 x 25 s = 75 s, each individually valid
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        message = str(ctx.exception).lower()
        self.assertTrue("60" in message or "total" in message, message)

    def test_duplicate_scene_ids_rejected(self):
        storyboard = make_storyboard()
        storyboard["scenes"][1]["id"] = storyboard["scenes"][0]["id"]
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn(storyboard["scenes"][0]["id"], str(ctx.exception))

    def test_unknown_claim_id_rejected(self):
        storyboard = make_storyboard()
        storyboard["scenes"][0]["claim_ids"].append("claim-99")
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn("claim-99", str(ctx.exception))

    def test_missing_required_scene_field_rejected(self):
        storyboard = make_storyboard()
        del storyboard["scenes"][0]["purpose"]
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn("purpose", str(ctx.exception).lower())

    def test_unknown_top_level_field_rejected(self):
        storyboard = make_storyboard()
        storyboard["totally-unexpected"] = {"not": "in the schema"}
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn("totally-unexpected", str(ctx.exception))

    def test_non_default_render_width_rejected(self):
        storyboard = make_storyboard()
        storyboard["render"]["width"] = 1920
        with self.assertRaises(ValueError) as ctx:
            rv.validate_storyboard(storyboard, self.schema)
        self.assertIn("1920", str(ctx.exception))


class MainCheckOnlyTests(unittest.TestCase):
    """--check-only: validation without rendering; readable nonzero failures."""

    def test_valid_storyboard_returns_zero(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_storyboard(Path(td), make_storyboard())
            code, _ = run_main(["--storyboard", str(path), "--check-only"])
            self.assertEqual(code, 0)

    def test_valid_storyboard_with_explicit_schema_returns_zero(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_storyboard(Path(td), make_storyboard())
            code, _ = run_main(
                [
                    "--storyboard", str(path),
                    "--schema", str(SCHEMA_PATH),
                    "--check-only",
                ]
            )
            self.assertEqual(code, 0)

    def test_invalid_storyboard_returns_nonzero_and_names_the_problem(self):
        storyboard = make_storyboard()
        storyboard["scenes"][2]["claim_ids"].append("claim-99")
        with tempfile.TemporaryDirectory() as td:
            path = write_storyboard(Path(td), storyboard)
            code, text = run_main(["--storyboard", str(path), "--check-only"])
            self.assertNotEqual(code, 0, text)
            self.assertIn("claim-99", text)


class MainOutputGuardTests(unittest.TestCase):
    """Output-path policy.

    SLOW: the --overwrite and new-path tests really encode a 1-second,
    30 fps, 1280x720 movie (ffmpeg + matplotlib), so they take a few
    seconds each. The no-overwrite guard test itself does not render.
    """

    def test_existing_output_rejected_without_overwrite_and_file_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = write_storyboard(tmp, make_tiny_storyboard())
            output = tmp / "out.mp4"
            output.write_bytes(b"sentinel-explainify-guard")
            code, text = run_main(
                ["--storyboard", str(storyboard), "--output", str(output)]
            )
            self.assertNotEqual(code, 0, text)
            self.assertIn(str(output), text)
            self.assertEqual(output.read_bytes(), b"sentinel-explainify-guard")
            self.assertEqual(output.stat().st_size, len(b"sentinel-explainify-guard"))

    def test_existing_output_with_explicit_overwrite_is_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = write_storyboard(tmp, make_tiny_storyboard())
            output = tmp / "out.mp4"
            output.write_bytes(b"sentinel-explainify-guard")
            code, text = run_main(
                ["--storyboard", str(storyboard), "--output", str(output), "--overwrite"]
            )
            self.assertEqual(code, 0, text)
            content = output.read_bytes()
            self.assertNotEqual(content, b"sentinel-explainify-guard")
            self.assertGreater(output.stat().st_size, 1000)

    def test_new_output_path_created_without_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = write_storyboard(tmp, make_tiny_storyboard())
            output = tmp / "fresh-out.mp4"
            code, text = run_main(
                ["--storyboard", str(storyboard), "--output", str(output)]
            )
            self.assertEqual(code, 0, text)
            self.assertTrue(output.exists(), text)
            self.assertGreater(output.stat().st_size, 1000)


class SelfTestTests(unittest.TestCase):
    """--self-test: in-memory fixture only; no movie is encoded."""

    def test_self_test_returns_zero_without_writing_a_movie(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            try:
                code, _ = run_main(["--self-test"])
                self.assertEqual(code, 0)
                leftovers = [str(p) for p in Path.cwd().rglob("*.mp4")]
                self.assertEqual([], leftovers)
            finally:
                os.chdir(original_cwd)

    def test_self_test_completes_quickly(self):
        start = time.monotonic()
        code, _ = run_main(["--self-test"])
        elapsed = time.monotonic() - start
        self.assertEqual(code, 0)
        self.assertLess(elapsed, 30.0)


class MainPreviewTests(unittest.TestCase):
    """--preview: one labeled PNG contact sheet; no ffmpeg and no video.

    SLOW-ish: each test draws every scene of a small storyboard once and
    rasterizes it, so a few seconds each; nothing is encoded.
    """

    def test_preview_writes_png_without_encoding_a_video(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = write_storyboard(tmp, make_tiny_storyboard())
            preview = tmp / "sheet.png"
            code, text = run_main(
                ["--storyboard", str(storyboard), "--preview", str(preview)]
            )
            self.assertEqual(code, 0, text)
            self.assertTrue(preview.exists(), text)
            self.assertEqual(preview.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertGreater(preview.stat().st_size, 1000)
            self.assertEqual([], list(tmp.glob("*.mp4")))
            self.assertIn("no video was encoded", text)

    def test_preview_tiles_one_cell_per_scene_in_one_row(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = write_storyboard(tmp, make_storyboard())  # 3 scenes
            preview = tmp / "sheet.png"
            code, text = run_main(
                ["--storyboard", str(storyboard), "--preview", str(preview)]
            )
            self.assertEqual(code, 0, text)
            width, height = struct.unpack(">II", preview.read_bytes()[16:24])
            frame_w, frame_h = int(rv.W * 100), int(rv.H * 100)
            # Three cells across, one row of cells plus its label strip.
            self.assertGreaterEqual(width, 3 * frame_w)
            self.assertGreater(height, frame_h)
            self.assertLess(height, 2 * frame_h)

    def test_preview_needs_no_ffmpeg_on_path(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = write_storyboard(tmp, make_tiny_storyboard())
            preview = tmp / "sheet.png"
            real_which = shutil.which
            shutil.which = lambda name, *a, **k: (
                None if name in ("ffmpeg", "ffprobe")
                else real_which(name, *a, **k)
            )
            try:
                code, text = run_main(
                    ["--storyboard", str(storyboard), "--preview", str(preview)]
                )
            finally:
                shutil.which = real_which
            self.assertEqual(code, 0, text)
            self.assertTrue(preview.exists(), text)

    def test_preview_rejects_invalid_storyboard_without_writing_a_png(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = make_storyboard()
            storyboard["scenes"][2]["claim_ids"].append("claim-99")
            path = write_storyboard(tmp, storyboard)
            preview = tmp / "sheet.png"
            code, text = run_main(
                ["--storyboard", str(path), "--preview", str(preview)]
            )
            self.assertNotEqual(code, 0, text)
            self.assertIn("claim-99", text)
            self.assertFalse(preview.exists())

    def test_preview_runs_the_prerender_check_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = make_tiny_storyboard()
            storyboard["scenes"][0]["on_screen_text"] = "$\\brokenmath_{$_%"
            path = write_storyboard(tmp, storyboard)
            preview = tmp / "sheet.png"
            code, text = run_main(
                ["--storyboard", str(path), "--preview", str(preview)]
            )
            self.assertNotEqual(code, 0, text)
            self.assertIn("pre-render", text)
            self.assertFalse(preview.exists())

    def test_preview_refuses_existing_path_without_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = write_storyboard(tmp, make_tiny_storyboard())
            preview = tmp / "sheet.png"
            preview.write_bytes(b"sentinel-explainify-preview")
            code, text = run_main(
                ["--storyboard", str(storyboard), "--preview", str(preview)]
            )
            self.assertNotEqual(code, 0, text)
            self.assertIn(str(preview), text)
            self.assertEqual(preview.read_bytes(), b"sentinel-explainify-preview")

    def test_preview_and_output_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = write_storyboard(tmp, make_tiny_storyboard())
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as ctx:
                    rv.main(["--storyboard", str(storyboard),
                             "--preview", str(tmp / "sheet.png"),
                             "--output", str(tmp / "out.mp4")])
            self.assertNotEqual(ctx.exception.code, 0)
            self.assertIn("exactly one mode", err.getvalue())
            self.assertEqual(list(tmp.glob("*.png")), [])
            self.assertEqual(list(tmp.glob("*.mp4")), [])


class DrawSceneTests(unittest.TestCase):
    """draw_scene: generic topic-neutral scene drawing on a matplotlib Axes."""

    def test_draw_scene_on_axes_does_not_raise(self):
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        storyboard = make_storyboard()
        fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
        try:
            rv.draw_scene(ax, storyboard["scenes"][0], 0.5, storyboard["brief"])
        finally:
            plt.close(fig)

    def test_draw_scene_clamps_out_of_range_progress(self):
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        storyboard = make_storyboard()
        fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
        try:
            for progress in (-0.5, 1.5):
                rv.draw_scene(ax, storyboard["scenes"][0], progress, storyboard["brief"])
        finally:
            plt.close(fig)


class IndependenceTests(unittest.TestCase):
    """The template stays self-contained: PEP-723 deps, no skill-package imports.

    These inspect the SOURCE TEXT of scripts/render_video.py; nothing is
    executed here beyond reading the file.
    """

    def _source(self) -> str:
        return (SCRIPTS / "render_video.py").read_text(encoding="utf-8")

    def test_declares_inline_pep723_dependency_metadata(self):
        source = self._source()
        start = source.find("# /// script")
        self.assertNotEqual(start, -1, "missing PEP-723 '# /// script' metadata block")
        end = source.find("# ///", start + 1)
        self.assertNotEqual(end, -1, "unterminated PEP-723 metadata block")
        block = source[start:end]
        for dependency in ("numpy", "matplotlib", "jsonschema"):
            self.assertIn(dependency, block)

    def test_does_not_import_skill_package_helpers(self):
        source = self._source()
        self.assertNotIn("import check_env", source)
        self.assertNotIn("from check_env", source)

    def test_sys_path_manipulation_anchors_only_to_own_file(self):
        source = self._source()
        offenders = [
            line.strip()
            for line in source.splitlines()
            if "sys.path" in line and "__file__" not in line
        ]
        self.assertEqual([], offenders)


class ReviewRound1Tests(unittest.TestCase):
    """Fixes from the 2026-10-03 code review (branch fix/explainify-review-round-1).

    Covers: cumulative frame allocation (no rounding accumulation), sub-frame
    duration rejection, pre-encode scene rasterization, encoder-name contract
    (libx264 accepted; discovered encoder drives the writer), text fit guard,
    duplicate claim-id rejection, conditional URL provenance, and schema
    version 1.1 acceptance.
    """

    # --- gap 1: cumulative frame allocation -------------------------------
    def test_frame_schedule_six_times_005s_totals_exactly_nine_frames(self):
        # The reviewer's case: per-scene rounding gave 12 frames (0.40 s) for a
        # 0.30 s storyboard; cumulative allocation must give exactly 9 (0.30 s).
        schedule = rv._frame_schedule([0.05] * 6, 30)
        total = sum(frames for _, frames in schedule)
        self.assertEqual(total, 9)
        self.assertEqual(total / 30, 0.30)

    def test_frame_schedule_totals_track_round_of_cumulative_duration(self):
        import math as _math
        import random as _random
        rng = _random.Random(7)
        for _ in range(100):
            durations = [round(rng.uniform(0.05, 2.0), 3) for _ in range(rng.randint(1, 8))]
            schedule = rv._frame_schedule(durations, 30)
            total = sum(frames for _, frames in schedule)
            expected = round(_math.fsum(durations) * 30)
            self.assertIn(total, (expected, expected + 1))
            self.assertTrue(all(frames >= 1 for _, frames in schedule))

    def test_sub_frame_duration_rejected(self):
        storyboard = make_storyboard()
        storyboard["scenes"][0]["duration_seconds"] = 0.02  # < 1 frame at 30 fps
        with self.assertRaises(ValueError) as cm:
            rv.validate_storyboard(storyboard, load_schema())
        self.assertIn("below one frame", str(cm.exception))

    # --- gap 5: duplicate claim ids ----------------------------------------
    def test_duplicate_claim_ids_rejected(self):
        storyboard = make_storyboard()
        storyboard["brief"]["claims"].append(
            {"id": "claim-1", "statement": "conflicting duplicate", "origin": "illustrative"}
        )
        with self.assertRaises(ValueError) as cm:
            rv.validate_storyboard(storyboard, load_schema())
        self.assertIn("duplicate claim id 'claim-1'", str(cm.exception))

    # --- gap 6: conditional URL provenance ---------------------------------
    def test_url_complete_without_provenance_rejected(self):
        storyboard = make_storyboard()
        storyboard["schema_version"] = "1.1"
        storyboard["brief"]["source"] = {"kind": "url", "retrieval_status": "complete"}
        with self.assertRaises(ValueError) as cm:
            rv.validate_storyboard(storyboard, load_schema())
        self.assertIn("resolved_location", str(cm.exception))

    def test_url_complete_with_provenance_passes(self):
        storyboard = make_storyboard()
        storyboard["schema_version"] = "1.1"
        storyboard["brief"]["source"] = {
            "kind": "url",
            "retrieval_status": "complete",
            "requested_location": "https://example.org/a",
            "resolved_location": "https://example.org/a",
            "retrieved_at": "2026-10-03",
        }
        rv.validate_storyboard(storyboard, load_schema())  # must not raise

    def test_url_unavailable_requires_requested_location(self):
        storyboard = make_storyboard()
        storyboard["schema_version"] = "1.1"
        storyboard["brief"]["source"] = {"kind": "url", "retrieval_status": "unavailable"}
        with self.assertRaises(ValueError):
            rv.validate_storyboard(storyboard, load_schema())
        storyboard["brief"]["source"]["requested_location"] = "https://example.org/gone"
        rv.validate_storyboard(storyboard, load_schema())  # must not raise

    def test_text_source_stays_unconditional(self):
        storyboard = make_storyboard()  # kind topic, not-applicable, all-null locations
        rv.validate_storyboard(storyboard, load_schema())  # must not raise

    def test_schema_version_1_1_accepted(self):
        storyboard = make_storyboard()
        storyboard["schema_version"] = "1.1"
        rv.validate_storyboard(storyboard, load_schema())  # must not raise

    # --- gap 3: encoder contract -------------------------------------------
    def test_select_encoder_accepts_libx264_only_listing(self):
        listing = " V....D libx264              libx264 H.264 / AVC / MPEG-4 AVC\n"
        self.assertEqual(rv._select_encoder(listing), "libx264")

    def test_select_encoder_prefers_libx264_over_videotoolbox(self):
        listing = (" V....D h264_videotoolbox VideoToolbox H.264\n"
                   " V....D libx264              libx264 H.264\n")
        self.assertEqual(rv._select_encoder(listing), "libx264")

    def test_select_encoder_returns_none_without_h264(self):
        self.assertIsNone(rv._select_encoder(" V....D mpeg4 mpeg4\n V.S... ffv1 FFV1\n"))

    def test_encoder_extra_args_match_encoder(self):
        self.assertIn("-crf", rv._encoder_extra_args("libx264"))
        self.assertIn("-q:v", rv._encoder_extra_args("h264_videotoolbox"))
        self.assertEqual(rv._encoder_extra_args("unknownenc"), ["-pix_fmt", "yuv420p"])

    # --- gap 2: pre-encode scene rasterization ------------------------------
    def test_broken_mathtext_fails_prerender_check(self):
        storyboard = make_storyboard()
        storyboard["scenes"][0]["on_screen_text"] = "$\\brokenmath_{$_%"
        with self.assertRaises(ValueError) as cm:
            rv._prerender_check(storyboard["scenes"], storyboard["brief"])
        self.assertIn("scene-", str(cm.exception))

    def test_unclipped_patch_outside_frame_fails_prerender_check(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        from matplotlib.patches import Rectangle

        fig = _plt.figure(figsize=(rv.W, rv.H), dpi=100)
        try:
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_xlim(0, rv.W)
            ax.set_ylim(0, rv.H)
            artist = Rectangle((rv.W - 0.4, 1.0), 2.0, 1.0, fc="none", ec="w")
            artist.set_clip_on(False)
            ax.add_patch(artist)
            fig.canvas.draw()
            message = rv._overflow_message("a patch", artist,
                                           fig.canvas.get_renderer(),
                                           rv.W * fig.dpi, rv.H * fig.dpi)
            self.assertIsNotNone(message)
            self.assertIn("outside the frame", message)
        finally:
            _plt.close(fig)

    def test_clipped_artists_that_still_render_are_not_reported(self):
        # Clipped artists are cut at the axes edge, which is the frame, so a
        # full-bleed background or a shape half past the edge renders
        # correctly and must not fail the check.
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        from matplotlib.patches import Rectangle

        fig = _plt.figure(figsize=(rv.W, rv.H), dpi=100)
        try:
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_xlim(0, rv.W)
            ax.set_ylim(0, rv.H)
            bleed = Rectangle((-1.0, -1.0), rv.W + 2.0, rv.H + 2.0,
                              fc="none", ec="w")
            past_edge = Rectangle((rv.W - 0.4, 1.0), 2.0, 1.0, fc="none", ec="w")
            ax.add_patch(bleed)
            ax.add_patch(past_edge)
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            for artist in (bleed, past_edge):
                self.assertIsNone(rv._overflow_message(
                    "a patch", artist, renderer, rv.W * fig.dpi, rv.H * fig.dpi))
        finally:
            _plt.close(fig)

    def test_render_mode_rejects_broken_math_before_creating_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = make_tiny_storyboard()
            storyboard["scenes"][0]["on_screen_text"] = "$\\brokenmath_{$_%"
            path = write_storyboard(tmp, storyboard)
            output = tmp / "out.mp4"
            code, text = run_main(
                ["--storyboard", str(path), "--output", str(output)]
            )
            self.assertNotEqual(code, 0, text)
            self.assertIn("pre-render", text)
            self.assertFalse(output.exists(), "a partial output file was created")

    # --- gap 4: text fit guard ----------------------------------------------
    def test_oversized_text_renders_wrapped_and_truncated_not_off_frame(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            storyboard = make_tiny_storyboard()
            storyboard["scenes"][0]["on_screen_text"] = "word " * 400
            path = write_storyboard(tmp, storyboard)
            output = tmp / "wrapped.mp4"
            code, text = run_main(
                ["--storyboard", str(path), "--output", str(output)]
            )
            self.assertEqual(code, 0, text)
            self.assertTrue(output.exists())

    def test_fit_scene_text_wraps_and_steps_down(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        fig = _plt.figure(figsize=(rv.W, rv.H), dpi=100)
        try:
            text, size = rv._fit_scene_text(fig, "word " * 60)
            usable_px = 0.92 * rv.W * fig.dpi
            px_per_char = size * fig.dpi / 72.0 * 0.58
            longest = max(len(l) for l in text.splitlines())
            self.assertLessEqual(longest * px_per_char, usable_px)
            self.assertIn(size, rv._TEXT_SIZES)
            huge, small = rv._fit_scene_text(fig, "word " * 400)
            self.assertEqual(small, rv._TEXT_SIZES[-1])
            self.assertTrue(huge.endswith("…"))
        finally:
            _plt.close(fig)

    # --- embedded schema sync ------------------------------------------------
    def test_embedded_schema_matches_packaged_schema(self):
        self.assertEqual(rv.EMBEDDED_SCHEMA, load_schema())


if __name__ == "__main__":
    unittest.main()
