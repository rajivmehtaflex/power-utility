#!/usr/bin/env python3
# /// script
# dependencies = [
#     "numpy>=1.26,<3",
#     "matplotlib>=3.8,<4",
#     "jsonschema>=4,<5",
# ]
# ///

"""Explainify explainer-video renderer template (generic and topic-neutral).

This file is the reusable video template of the explainify skill. The skill
workflow copies it next to a run's storyboard and adapts the scene drawing
to the topic; the CLI, storyboard validation, frame scheduling, and encoding
settings are meant to be preserved as-is. It renders a silent 1280x720,
30 fps H.264 (yuv420p) MP4 from a validated storyboard JSON file.

Usage (exactly one mode per invocation):

    render_video.py --storyboard PATH [--schema PATH] --check-only
        Validate the storyboard against the embedded schema (or the schema at
        PATH when --schema is given) without rendering. Exit 0 when valid;
        exit 1 with a readable message when invalid.

    render_video.py --storyboard PATH [--schema PATH] --output PATH [--overwrite]
        Validate, then render the video to PATH. An existing output path is
        rejected before anything runs unless --overwrite was passed
        explicitly. ffmpeg with an H.264 encoder must be available; both are
        checked before rendering starts.

    render_video.py --self-test
        Validate a tiny in-memory generic storyboard against the embedded
        schema and exercise draw_scene on an offscreen figure for several
        progress values. Encodes no movie and writes no file.

Stable interface (used by the contract tests and by adapted copies):

    validate_storyboard(data, schema) -> None
        Raises a readable ValueError naming the offending field or id for
        schema violations and for the cross-field rules JSON Schema cannot
        express: non-finite, zero, or negative scene durations; duplicate
        scene ids; claim_ids entries that do not resolve into brief.claims;
        and a total duration above 60 seconds. Returns None when valid.

    draw_scene(ax, scene, progress, brief) -> None
        Draws the generic placeholder scene: run-title header, centered
        on_screen_text with a smoothstep fade-in over roughly the first
        0.4 s of the scene, and neutral rounded boxes whose count follows
        the scene's claim count. progress is clamped to [0, 1]. A scene's
        optional data field is ignored here; adapted copies use it.

    main(argv=None) -> int
        Parses arguments, runs exactly one mode, and returns the process
        exit code (argparse usage errors exit 2 by default).

Storyboard fields are data and are never evaluated as code. The template is
self-contained: it imports only numpy, matplotlib, and jsonschema plus the
standard library, reads no other file from the installed skill package, and
embeds the exact storyboard schema used for validation (--schema overrides
the embedded copy for development).
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from bisect import bisect_right
from pathlib import Path

import jsonschema
import matplotlib
import numpy as np

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

plt.rcParams["mathtext.fontset"] = "cm"  # Computer Modern for any mathtext

# Generic visual language; see references/video-style.md in this package.
# Nothing here assumes a topic: an adapted copy replaces draw_scene only.
W, H = 12.8, 7.2                # inches at dpi 100 -> exactly 1280x720 pixels
DEFAULT_FPS = 30                # v0.1 fixed frame rate
BG = "#16161d"                  # background
BLUE, YELLOW, GREEN = "#58C4DD", "#F4D345", "#83C167"
RED, GREY, WHITE = "#FC6255", "#9AA0A6", "#EBEBEB"
CELL_DARK = "#26313d"           # inset / box fill base
ACCENTS = (BLUE, YELLOW, GREEN, RED)

FADE_SECONDS = 0.4              # smoothstep fade window (~12 frames at 30 fps)
POP_STAGGER = 0.35              # seconds between staggered pop-ins
POP_SECONDS = 0.35              # duration of each pop-in grow
MAX_TOTAL_SECONDS = 60.0        # storyboard-level duration ceiling

# Exact copy of the parsed contents of assets/storyboard.schema.json
# (storyboard contract version 1.0). Embedding it keeps a copied template
# reproducible anywhere without the installed skill package; --schema PATH
# overrides it when explicitly supplied.
EMBEDDED_SCHEMA: dict = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
 '$id': 'storyboard.schema.json',
 'title': 'Explainify storyboard',
 'description': 'Version 1.0 of the Explainify storyboard contract. This schema '
                'describes teaching intent and timing for a short silent explainer '
                'video; it is NOT a drawing language - the generator assigns drawing '
                'operations, and storyboard fields are data that is never evaluated as '
                'code. The schema alone is intentionally insufficient: three '
                'cross-field constraints cannot be expressed in JSON Schema and are '
                "enforced programmatically by the renderer's validate_storyboard "
                'function: (1) scene ids must be unique across the storyboard, (2) '
                "every entry in a scene's claim_ids must reference an id that exists "
                'in brief.claims, and (3) the sum of all scene duration_seconds must '
                'be at most 60 seconds. All fields are topic-neutral: the generic '
                'contract must never require attention tokens, attention weights, '
                'attention matrices, or any other machine-learning-specific concept; '
                "such topic-specific values may appear only inside a scene's optional "
                'data field.',
 'type': 'object',
 'additionalProperties': False,
 'required': ['schema_version', 'brief', 'render', 'scenes'],
 'properties': {'schema_version': {'const': '1.0',
                                   'description': 'Storyboard contract version; fixed '
                                                  'to "1.0" for v0.1.'},
                'brief': {'type': 'object',
                          'additionalProperties': False,
                          'required': ['title',
                                       'source',
                                       'audience',
                                       'learning_objective',
                                       'prerequisites',
                                       'terms',
                                       'core_claim',
                                       'mechanism',
                                       'claims',
                                       'example',
                                       'analogy',
                                       'must_preserve',
                                       'omissions'],
                          'description': 'Shared teaching brief: what is taught, from '
                                         'which source, and which facts must survive '
                                         'formatting. Absent example or analogy is '
                                         'null.',
                          'properties': {'title': {'type': 'string',
                                                   'minLength': 1,
                                                   'description': 'Title of the '
                                                                  'explanation.'},
                                         'source': {'type': 'object',
                                                    'additionalProperties': False,
                                                    'required': ['kind',
                                                                 'retrieval_status'],
                                                    'description': 'Provenance of the '
                                                                   'material behind '
                                                                   'the explanation. A '
                                                                   'partially or '
                                                                   'unavailable source '
                                                                   'must not silently '
                                                                   'become a '
                                                                   'model-knowledge '
                                                                   'explanation of the '
                                                                   'same subject.',
                                                    'properties': {'kind': {'enum': ['topic',
                                                                                     'url',
                                                                                     'text',
                                                                                     'file'],
                                                                            'description': 'How '
                                                                                           'the '
                                                                                           'source '
                                                                                           'was '
                                                                                           'supplied '
                                                                                           'or '
                                                                                           'resolved.'},
                                                                   'requested_location': {'type': ['string',
                                                                                                   'null'],
                                                                                          'description': 'URL '
                                                                                                         'or '
                                                                                                         'path '
                                                                                                         'the '
                                                                                                         'user '
                                                                                                         'asked '
                                                                                                         'to '
                                                                                                         'use, '
                                                                                                         'when '
                                                                                                         'applicable; '
                                                                                                         'otherwise '
                                                                                                         'null. '
                                                                                                         'A '
                                                                                                         'user-provided '
                                                                                                         'local '
                                                                                                         'path '
                                                                                                         'is '
                                                                                                         'kept '
                                                                                                         'out '
                                                                                                         'of '
                                                                                                         'web '
                                                                                                         'citations.'},
                                                                   'resolved_location': {'type': ['string',
                                                                                                  'null'],
                                                                                         'description': 'Location '
                                                                                                        'actually '
                                                                                                        'used '
                                                                                                        'after '
                                                                                                        'redirects '
                                                                                                        'or '
                                                                                                        'mirror '
                                                                                                        'resolution, '
                                                                                                        'when '
                                                                                                        'applicable; '
                                                                                                        'otherwise '
                                                                                                        'null.'},
                                                                   'source_title': {'type': ['string',
                                                                                             'null'],
                                                                                    'description': 'Title '
                                                                                                   'of '
                                                                                                   'the '
                                                                                                   'retrieved '
                                                                                                   'source '
                                                                                                   'when '
                                                                                                   'one '
                                                                                                   'is '
                                                                                                   'identifiable; '
                                                                                                   'otherwise '
                                                                                                   'null.'},
                                                                   'retrieval_status': {'enum': ['complete',
                                                                                                 'partial',
                                                                                                 'unavailable',
                                                                                                 'not-applicable'],
                                                                                        'description': 'How '
                                                                                                       'much '
                                                                                                       'of '
                                                                                                       'the '
                                                                                                       'requested '
                                                                                                       'source '
                                                                                                       'was '
                                                                                                       'actually '
                                                                                                       'retrieved.'},
                                                                   'retrieved_at': {'type': ['string',
                                                                                             'null'],
                                                                                    'format': 'date',
                                                                                    'description': 'ISO-8601 '
                                                                                                   'calendar '
                                                                                                   'date '
                                                                                                   '(YYYY-MM-DD) '
                                                                                                   'on '
                                                                                                   'which '
                                                                                                   'web '
                                                                                                   'material '
                                                                                                   'was '
                                                                                                   'retrieved; '
                                                                                                   'null '
                                                                                                   'when '
                                                                                                   'retrieval '
                                                                                                   'did '
                                                                                                   'not '
                                                                                                   'occur.'}}},
                                         'audience': {'type': 'string',
                                                      'minLength': 1,
                                                      'description': 'Who the '
                                                                     'explanation is '
                                                                     'for.'},
                                         'learning_objective': {'type': 'string',
                                                                'minLength': 1,
                                                                'description': 'What '
                                                                               'the '
                                                                               'learner '
                                                                               'should '
                                                                               'understand '
                                                                               'afterward.'},
                                         'prerequisites': {'type': 'array',
                                                           'items': {'type': 'string'},
                                                           'description': 'Knowledge '
                                                                          'the '
                                                                          'explanation '
                                                                          'assumes and '
                                                                          'introduces '
                                                                          'before '
                                                                          'use.'},
                                         'terms': {'type': 'array',
                                                   'items': {'type': 'object',
                                                             'additionalProperties': False,
                                                             'required': ['term',
                                                                          'definition'],
                                                             'properties': {'term': {'type': 'string',
                                                                                     'description': 'The '
                                                                                                    'domain '
                                                                                                    'term '
                                                                                                    'being '
                                                                                                    'defined.'},
                                                                            'definition': {'type': 'string',
                                                                                           'description': 'Definition '
                                                                                                          'used '
                                                                                                          'consistently '
                                                                                                          'throughout '
                                                                                                          'the '
                                                                                                          'explanation.'}}},
                                                   'description': 'Domain terms with '
                                                                  'consistent '
                                                                  'definitions.'},
                                         'core_claim': {'type': 'string',
                                                        'minLength': 1,
                                                        'description': 'The essential '
                                                                       'claim the '
                                                                       'explanation '
                                                                       'teaches.'},
                                         'mechanism': {'type': 'array',
                                                       'items': {'type': 'object',
                                                                 'additionalProperties': False,
                                                                 'required': ['step',
                                                                              'description'],
                                                                 'properties': {'step': {'type': 'integer',
                                                                                         'minimum': 1,
                                                                                         'description': 'Position '
                                                                                                        'of '
                                                                                                        'this '
                                                                                                        'step '
                                                                                                        'in '
                                                                                                        'the '
                                                                                                        'ordered '
                                                                                                        'causal '
                                                                                                        'chain.'},
                                                                                'description': {'type': 'string',
                                                                                                'description': 'What '
                                                                                                               'happens '
                                                                                                               'in '
                                                                                                               'this '
                                                                                                               'causal '
                                                                                                               'step.'}}},
                                                       'description': 'Ordered causal '
                                                                      'steps of the '
                                                                      'mechanism.'},
                                         'claims': {'type': 'array',
                                                    'items': {'type': 'object',
                                                              'additionalProperties': False,
                                                              'required': ['id',
                                                                           'statement',
                                                                           'origin'],
                                                              'properties': {'id': {'$ref': '#/$defs/claim-id',
                                                                                    'description': 'Stable '
                                                                                                   'identifier '
                                                                                                   'referenced '
                                                                                                   'by '
                                                                                                   'scenes.'},
                                                                             'statement': {'type': 'string',
                                                                                           'minLength': 1,
                                                                                           'description': 'The '
                                                                                                          'claim '
                                                                                                          'itself.'},
                                                                             'origin': {'enum': ['provided-source',
                                                                                                 'retrieved-source',
                                                                                                 'model-knowledge',
                                                                                                 'illustrative'],
                                                                                        'description': 'Where '
                                                                                                       'the '
                                                                                                       'claim '
                                                                                                       'comes '
                                                                                                       'from; '
                                                                                                       'a '
                                                                                                       'model-knowledge '
                                                                                                       'claim '
                                                                                                       'is '
                                                                                                       'never '
                                                                                                       'presented '
                                                                                                       'as '
                                                                                                       'a '
                                                                                                       'quotation '
                                                                                                       'from '
                                                                                                       'an '
                                                                                                       'unavailable '
                                                                                                       'source.'},
                                                                             'qualifications': {'type': 'array',
                                                                                                'items': {'type': 'string'},
                                                                                                'description': 'Conditions, '
                                                                                                               'uncertainty, '
                                                                                                               'or '
                                                                                                               'limits '
                                                                                                               'that '
                                                                                                               'must '
                                                                                                               'be '
                                                                                                               'preserved '
                                                                                                               'with '
                                                                                                               'the '
                                                                                                               'claim.'}}},
                                                    'description': 'Factual claims '
                                                                   'with honest '
                                                                   'origins and '
                                                                   'required '
                                                                   'qualifications.'},
                                         'example': {'type': ['object', 'null'],
                                                     'additionalProperties': False,
                                                     'required': ['summary',
                                                                  'value_origin'],
                                                     'description': 'Optional worked '
                                                                    'example; null '
                                                                    'when absent.',
                                                     'properties': {'summary': {'type': 'string',
                                                                                'description': 'What '
                                                                                               'the '
                                                                                               'example '
                                                                                               'shows.'},
                                                                    'value_origin': {'enum': ['illustrative',
                                                                                              'measured',
                                                                                              'derived'],
                                                                                     'description': 'Kind '
                                                                                                    'of '
                                                                                                    'values '
                                                                                                    'used, '
                                                                                                    'so '
                                                                                                    'illustrative '
                                                                                                    'numbers '
                                                                                                    'are '
                                                                                                    'never '
                                                                                                    'mistaken '
                                                                                                    'for '
                                                                                                    'measurements.'},
                                                                    'detail': {'type': 'string',
                                                                               'description': 'Additional '
                                                                                              'detail '
                                                                                              'about '
                                                                                              'the '
                                                                                              'example.'},
                                                                    'calculation': {'type': 'string',
                                                                                    'description': 'Enough '
                                                                                                   'of '
                                                                                                   'the '
                                                                                                   'calculation '
                                                                                                   'to '
                                                                                                   'check '
                                                                                                   'consistency.'}}},
                                         'analogy': {'type': ['object', 'null'],
                                                     'additionalProperties': False,
                                                     'required': ['description',
                                                                  'stops_matching'],
                                                     'description': 'Optional analogy '
                                                                    'used only when '
                                                                    'helpful; null '
                                                                    'when absent.',
                                                     'properties': {'description': {'type': 'string',
                                                                                    'description': 'The '
                                                                                                   'analogy '
                                                                                                   'itself.'},
                                                                    'stops_matching': {'type': 'string',
                                                                                       'description': 'Where '
                                                                                                      'the '
                                                                                                      'analogy '
                                                                                                      'stops '
                                                                                                      'matching '
                                                                                                      'the '
                                                                                                      'mechanism.'}}},
                                         'must_preserve': {'type': 'array',
                                                           'items': {'type': 'string'},
                                                           'description': 'Negation, '
                                                                          'dates, '
                                                                          'uncertainty, '
                                                                          'conditions, '
                                                                          'and other '
                                                                          'facts '
                                                                          'simplification '
                                                                          'must '
                                                                          'retain.'},
                                         'omissions': {'type': 'array',
                                                       'items': {'type': 'string'},
                                                       'description': 'Deliberate '
                                                                      'exclusions and '
                                                                      'source-coverage '
                                                                      'limitations.'}}},
                'render': {'type': 'object',
                           'additionalProperties': False,
                           'required': ['width', 'height', 'fps', 'title'],
                           'description': 'Output configuration. Width, height, and '
                                          'fps are fixed v0.1 defaults, encoded as '
                                          'constants rather than defaults.',
                           'properties': {'width': {'const': 1280,
                                                    'description': 'Video width in '
                                                                   'pixels; fixed for '
                                                                   'v0.1.'},
                                          'height': {'const': 720,
                                                     'description': 'Video height in '
                                                                    'pixels; fixed for '
                                                                    'v0.1.'},
                                          'fps': {'const': 30,
                                                  'description': 'Frames per second; '
                                                                 'fixed for v0.1.'},
                                          'title': {'type': 'string',
                                                    'minLength': 1,
                                                    'description': 'Topic title shown '
                                                                   'in the video.'}}},
                'scenes': {'type': 'array',
                           'minItems': 1,
                           'description': 'Ordered scenes covering the learning '
                                          'objective; planning roughly 6-8 scenes is a '
                                          'guideline, not a rule. Uniqueness of scene '
                                          'ids and the 60-second total-duration limit '
                                          'are enforced programmatically by the '
                                          'renderer, not by this schema.',
                           'items': {'type': 'object',
                                     'additionalProperties': False,
                                     'required': ['id',
                                                  'duration_seconds',
                                                  'purpose',
                                                  'on_screen_text',
                                                  'visual_intent',
                                                  'claim_ids'],
                                     'description': 'One scene of teaching intent and '
                                                    'timing; the generator decides the '
                                                    'actual drawing operations.',
                                     'properties': {'id': {'type': 'string',
                                                           'minLength': 1,
                                                           'description': 'Scene '
                                                                          'identifier; '
                                                                          'must be '
                                                                          'unique '
                                                                          'across '
                                                                          'scenes '
                                                                          '(enforced '
                                                                          'programmatically).'},
                                                    'duration_seconds': {'type': 'number',
                                                                         'exclusiveMinimum': 0,
                                                                         'description': 'Scene '
                                                                                        'duration '
                                                                                        'in '
                                                                                        'seconds, '
                                                                                        'greater '
                                                                                        'than '
                                                                                        '0. '
                                                                                        "JSON's "
                                                                                        'number '
                                                                                        'type '
                                                                                        'is '
                                                                                        'finite '
                                                                                        'by '
                                                                                        'specification '
                                                                                        '(NaN '
                                                                                        'and '
                                                                                        'Infinity '
                                                                                        'are '
                                                                                        'not '
                                                                                        'valid '
                                                                                        'JSON), '
                                                                                        'so '
                                                                                        'a '
                                                                                        'strictly '
                                                                                        'parsed '
                                                                                        'document '
                                                                                        'never '
                                                                                        'contains '
                                                                                        'non-finite '
                                                                                        'values; '
                                                                                        'the '
                                                                                        'renderer '
                                                                                        'additionally '
                                                                                        'rejects '
                                                                                        'non-finite '
                                                                                        'Python '
                                                                                        'floats.'},
                                                    'purpose': {'type': 'string',
                                                                'minLength': 1,
                                                                'description': 'Teaching '
                                                                               'role '
                                                                               'of '
                                                                               'this '
                                                                               'scene.'},
                                                    'on_screen_text': {'type': 'string',
                                                                       'description': 'Text '
                                                                                      'shown '
                                                                                      'on '
                                                                                      'screen '
                                                                                      'during '
                                                                                      'this '
                                                                                      'scene; '
                                                                                      'may '
                                                                                      'be '
                                                                                      'empty '
                                                                                      'when '
                                                                                      'the '
                                                                                      'visual '
                                                                                      'alone '
                                                                                      'carries '
                                                                                      'the '
                                                                                      'state, '
                                                                                      'but '
                                                                                      'the '
                                                                                      'field '
                                                                                      'itself '
                                                                                      'is '
                                                                                      'required.'},
                                                    'visual_intent': {'type': 'string',
                                                                      'minLength': 1,
                                                                      'description': 'What '
                                                                                     'the '
                                                                                     'animation '
                                                                                     'should '
                                                                                     'show; '
                                                                                     'the '
                                                                                     'generator '
                                                                                     'assigns '
                                                                                     'concrete '
                                                                                     'drawing '
                                                                                     'operations.'},
                                                    'claim_ids': {'type': 'array',
                                                                  'minItems': 1,
                                                                  'items': {'$ref': '#/$defs/claim-id'},
                                                                  'description': 'Non-empty '
                                                                                 'list '
                                                                                 'of '
                                                                                 'claims '
                                                                                 'this '
                                                                                 'scene '
                                                                                 'teaches; '
                                                                                 'each '
                                                                                 'must '
                                                                                 'exist '
                                                                                 'in '
                                                                                 'brief.claims '
                                                                                 '(enforced '
                                                                                 'programmatically).'},
                                                    'data': {'description': 'Optional '
                                                                            'topic-specific '
                                                                            'payload: '
                                                                            'any JSON '
                                                                            'value the '
                                                                            "scene's "
                                                                            'generated '
                                                                            'drawing '
                                                                            'code '
                                                                            'needs. '
                                                                            'This is '
                                                                            'the only '
                                                                            'open '
                                                                            'field in '
                                                                            'the '
                                                                            'schema; '
                                                                            'the '
                                                                            'generic '
                                                                            'contract '
                                                                            'never '
                                                                            'requires '
                                                                            'particular '
                                                                            'domain '
                                                                            'concepts '
                                                                            'here.'}}}}},
 '$defs': {'claim-id': {'type': 'string',
                        'pattern': '^[a-z0-9]+(?:-[a-z0-9]+)*$',
                        'description': 'Stable lowercase identifier: lowercase letters '
                                       'and digits in hyphen-separated groups, for '
                                       'example "claim-1".'}}}


# ---------------------------------------------------------------------------
# Small generic helpers
# ---------------------------------------------------------------------------

def _clamp01(value: float) -> float:
    """Clamp to [0, 1]; non-finite values collapse to 0 so drawing never raises."""
    if not math.isfinite(value):
        return 0.0
    return min(max(value, 0.0), 1.0)


def _ease(value: float) -> float:
    """Smoothstep easing u*u*(3-2*u) for u clamped to [0, 1]."""
    u = _clamp01(value)
    return u * u * (3.0 - 2.0 * u)


def _mix(color_a, color_b, t: float):
    """Linear interpolation between two colors, t clamped to [0, 1]."""
    a = np.array(matplotlib.colors.to_rgb(color_a))
    b = np.array(matplotlib.colors.to_rgb(color_b))
    return tuple(a + (b - a) * _clamp01(t))


def _text(ax, x, y, s, *, size=14, color=WHITE, alpha=1.0, ha="center",
          va="center", weight="normal", style="normal", linespacing=1.2):
    ax.text(x, y, s, size=size, color=color, alpha=alpha, ha=ha, va=va,
            weight=weight, style=style, linespacing=linespacing, zorder=10)


def _rounded_box(ax, x, y, w, h, fc, ec, *, lw=1.2, alpha=1.0, rounding=0.08):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.02,rounding_size={rounding}",
        fc=fc, ec=ec, lw=lw, alpha=alpha, mutation_aspect=1,
    ))


def _format_path(items) -> str:
    """Render a jsonschema error path as a readable 'a.b[2].c' location."""
    parts = [f"[{item}]" if isinstance(item, int) else f".{item}" for item in items]
    return ("storyboard" + "".join(parts)) if parts else "storyboard root"


def _describe_offending_value(instance) -> str:
    """Name the offending value when it is a short scalar, else stay quiet."""
    if instance is None or isinstance(instance, bool):
        return f" (got {instance!r})"
    if isinstance(instance, (int, float, str)):
        text = repr(instance)
        if len(text) > 80:
            text = text[:77] + "..."
        return f" (got {text})"
    return ""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_storyboard(data: dict, schema: dict) -> None:
    """Validate a storyboard dict against a storyboard schema dict.

    Layer 1: jsonschema Draft 2020-12 validation; failures are re-raised as a
    ValueError whose message lists each offending location and message
    (capped at 12 lines, with a count of the remainder).

    Layer 2: cross-field rules the schema cannot express:
      - every duration_seconds must be a finite number greater than 0;
      - scene ids must be unique across the storyboard;
      - every claim_ids entry must exist in brief.claims;
      - the sum of duration_seconds must be at most 60.0 seconds.

    Returns None when valid; raises ValueError with a readable message
    naming the offending field or id otherwise.
    """
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(data),
        key=lambda err: [str(item) for item in err.absolute_path],
    )
    if errors:
        shown = errors[:12]
        lines = [f"  - {_format_path(err.absolute_path)}: "
                 f"{err.message}{_describe_offending_value(err.instance)}"
                 for err in shown]
        hidden = len(errors) - len(shown)
        if hidden > 0:
            lines.append(f"  - ... and {hidden} more schema problem(s)")
        raise ValueError("storyboard fails schema validation:\n" + "\n".join(lines))

    scenes = data["scenes"]
    known_claim_ids = {claim.get("id") for claim in data["brief"]["claims"]}

    seen_ids: dict[str, int] = {}
    for index, scene in enumerate(scenes):
        scene_id = str(scene.get("id", f"<scene {index}>"))
        duration = scene.get("duration_seconds")
        if (isinstance(duration, bool)
                or not isinstance(duration, (int, float))
                or not math.isfinite(duration)):
            raise ValueError(
                f"scene '{scene_id}' (index {index}) has a non-finite "
                f"duration_seconds value ({duration!r}); scene duration must "
                "be a finite number greater than 0"
            )
        if duration <= 0:
            raise ValueError(
                f"scene '{scene_id}' (index {index}) has duration_seconds "
                f"{duration}; scene duration must be greater than 0"
            )
        if scene_id in seen_ids:
            raise ValueError(
                f"duplicate scene id '{scene_id}' is used by scene index "
                f"{seen_ids[scene_id]} and scene index {index}; scene ids "
                "must be unique across the storyboard"
            )
        seen_ids[scene_id] = index

    for index, scene in enumerate(scenes):
        scene_id = str(scene.get("id", f"<scene {index}>"))
        for claim_id in scene.get("claim_ids", []):
            if claim_id not in known_claim_ids:
                raise ValueError(
                    f"scene '{scene_id}' (index {index}) references claim id "
                    f"'{claim_id}', which is not present in brief.claims"
                )

    total = math.fsum(float(scene["duration_seconds"]) for scene in scenes)
    if total > MAX_TOTAL_SECONDS:
        raise ValueError(
            f"total duration {total:g} s across {len(scenes)} scenes exceeds "
            f"the {MAX_TOTAL_SECONDS:g} s maximum; shorten or remove scenes"
        )


# ---------------------------------------------------------------------------
# Generic scene drawing (the part adapters replace)
# ---------------------------------------------------------------------------

def draw_scene(ax, scene: dict, progress: float, brief: dict) -> None:
    """Draw one generic placeholder scene on *ax* (fully owns the axes).

    Layout: a small run-title header with a thin divider, the scene's
    on_screen_text centered with a smoothstep fade-in over roughly the first
    0.4 s of the scene, neutral rounded placeholder boxes whose count follows
    the scene's claim count (staggered pop-in, ~0.35 s apart, growing from
    60% size), a small scene-id tag, and a thin scene progress bar.

    This function is topic-neutral on purpose: no field other than the
    storyboard contract fields listed above is read, a scene's optional
    ``data`` payload is ignored, and nothing here raises for any
    schema-valid scene. ``progress`` is clamped to [0, 1]. Adapted copies
    replace this with topic-specific art while keeping the same signature.
    """
    u = _clamp01(float(progress))
    try:
        duration = float(scene.get("duration_seconds", 1.0))
    except (TypeError, ValueError):
        duration = 1.0
    if not math.isfinite(duration) or duration <= 0.0:
        duration = 1.0
    elapsed = u * duration

    ax.clear()
    ax.set_xlim(0.0, W)
    ax.set_ylim(0.0, H)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(BG)

    fade = _ease(elapsed / FADE_SECONDS)

    # Header: run title from the brief, small and quiet, with a divider.
    title = str(brief.get("title") or "").strip() or "Explanation"
    _text(ax, 0.42, H - 0.40, title, size=13, color=GREY,
          alpha=0.85 * fade, ha="left")
    ax.plot([0.42, W - 0.42], [H - 0.72, H - 0.72], color=GREY, lw=0.8,
            alpha=0.30 * fade, zorder=1)

    # Centered on-screen text (the scene's teaching text), smoothstep fade-in.
    raw_lines = str(scene.get("on_screen_text") or "").splitlines()
    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    if raw_lines:
        size = 27 if len(raw_lines) <= 2 else 22
        _text(ax, W / 2.0, H * 0.62, "\n".join(raw_lines), size=size,
              color=WHITE, alpha=fade, linespacing=1.25)

    # Neutral placeholder visual: rounded boxes, one per referenced claim.
    # An adapter replaces this block with the scene's real illustration.
    claim_ids = [str(claim_id) for claim_id in (scene.get("claim_ids") or [])]
    count = max(1, len(claim_ids))
    box_w, box_h, gap = 1.75, 1.10, 0.35
    row_w = count * box_w + (count - 1) * gap
    max_row = W - 1.6
    if row_w > max_row:
        box_w *= max_row / row_w
        gap *= max_row / row_w
        row_w = max_row
    x0 = (W - row_w) / 2.0
    y_center = H * 0.335
    show_labels = box_w >= 1.0
    for i in range(count):
        grow = _ease((elapsed - (0.45 + POP_STAGGER * i)) / POP_SECONDS)
        if grow <= 0.0:
            continue
        scale = 0.6 + 0.4 * grow
        accent = ACCENTS[i % len(ACCENTS)]
        center_x = x0 + i * (box_w + gap) + box_w / 2.0
        bw, bh = box_w * scale, box_h * scale
        _rounded_box(ax, center_x - bw / 2.0, y_center - bh / 2.0, bw, bh,
                     fc=_mix(CELL_DARK, accent, 0.20 * grow), ec=accent,
                     lw=1.4, alpha=grow, rounding=0.10)
        if show_labels and i < len(claim_ids):
            _text(ax, center_x, y_center, claim_ids[i], size=11,
                  color=GREY, alpha=grow)

    # Small scene tag (metadata) and a thin scene progress bar (pacing cue).
    scene_id = str(scene.get("id") or "").strip()
    if scene_id:
        _text(ax, 0.42, 0.36, scene_id, size=10, color=GREY,
              alpha=0.5 * fade, ha="left")
    bar_y = 0.20
    ax.plot([0.42, W - 0.42], [bar_y, bar_y], color=GREY, lw=2.0,
            alpha=0.22 * fade, zorder=1)
    if u > 0.0:
        ax.plot([0.42, 0.42 + (W - 0.84) * u], [bar_y, bar_y], color=BLUE,
                lw=2.0, alpha=0.85 * fade, zorder=2)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path, kind: str) -> dict:
    """Load a JSON object from *path* with readable ValueError failures."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise ValueError(f"{kind} file not found: {path}") from None
    except IsADirectoryError:
        raise ValueError(f"{kind} path is a directory, not a file: {path}") from None
    except OSError as exc:
        raise ValueError(f"could not read {kind} file {path}: {exc}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{kind} file is not valid JSON: {path} "
            f"(line {exc.lineno}, column {exc.colno}: {exc.msg})"
        ) from None
    if not isinstance(data, dict):
        raise ValueError(
            f"{kind} file must contain a JSON object at the top level: {path}"
        )
    return data


def _find_h264_encoder(ffmpeg_path: str) -> str | None:
    """Return the name of an available H.264 encoder, or None (with a message)."""
    try:
        proc = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=60, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Error: could not run ffmpeg to list encoders ({exc}).")
        return None
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[:400]
        print(f"Error: ffmpeg failed to list encoders "
              f"(exit {proc.returncode}): {detail}")
        return None
    for line in (proc.stdout + "\n" + proc.stderr).splitlines():
        fields = line.split()
        if len(fields) >= 2 and "h264" in fields[1].lower():
            return fields[1]
    return None


def _self_test_fixture() -> dict:
    """A tiny generic storyboard used only by --self-test (never encoded)."""
    return {
        "schema_version": "1.0",
        "brief": {
            "title": "Template self-test",
            "source": {"kind": "topic", "retrieval_status": "not-applicable"},
            "audience": "A reader new to the topic.",
            "learning_objective": (
                "Confirm the template validates and draws scenes from "
                "storyboard data."
            ),
            "prerequisites": [],
            "terms": [],
            "core_claim": "The renderer draws each scene from storyboard data.",
            "mechanism": [
                {"step": 1,
                 "description": "The renderer reads the storyboard and its brief."},
                {"step": 2,
                 "description": "It draws each scene's text and placeholder layout."},
            ],
            "claims": [
                {"id": "claim-1",
                 "statement": "Scenes are drawn from storyboard data.",
                 "origin": "illustrative"},
            ],
            "example": None,
            "analogy": None,
            "must_preserve": [],
            "omissions": [],
        },
        "render": {"width": 1280, "height": 720, "fps": 30,
                   "title": "Template self-test"},
        "scenes": [
            {
                "id": "scene-1",
                "duration_seconds": 0.5,
                "purpose": "Show the first placeholder state.",
                "on_screen_text": "First self-test scene",
                "visual_intent": "Placeholder boxes sized by the claim count.",
                "claim_ids": ["claim-1"],
            },
            {
                "id": "scene-2",
                "duration_seconds": 0.5,
                "purpose": "Show the second placeholder state.",
                "on_screen_text": "Second self-test scene",
                "visual_intent": "Placeholder boxes sized by the claim count.",
                "claim_ids": ["claim-1"],
            },
        ],
    }


def _run_self_test() -> int:
    """Validate the fixture and exercise drawing in memory; write nothing."""
    fixture = _self_test_fixture()
    validate_storyboard(fixture, EMBEDDED_SCHEMA)
    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    try:
        for scene in fixture["scenes"]:
            for progress in (-0.5, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5):
                draw_scene(ax, scene, progress, fixture["brief"])
        fig.canvas.draw()  # force one offscreen rasterization; writes no file
    finally:
        plt.close(fig)
    print("self-test OK: embedded-schema fixture validated and generic scenes "
          "drawn in memory (no movie encoded)")
    return 0


def _render_storyboard(storyboard: dict, output_path: Path, ffmpeg_path: str,
                       encoder_name: str) -> int:
    """Render a validated storyboard to a silent H.264 MP4; return exit code."""
    render_cfg = storyboard["render"]
    brief = storyboard["brief"]
    scenes = storyboard["scenes"]
    fps = int(render_cfg["fps"])
    width_px, height_px = int(render_cfg["width"]), int(render_cfg["height"])

    # Frame schedule: round each scene to whole frames; track cumulative starts.
    schedule: list[tuple[int, int]] = []
    total_frames = 0
    for scene in scenes:
        scene_frames = max(1, int(round(float(scene["duration_seconds"]) * fps)))
        schedule.append((total_frames, scene_frames))
        total_frames += scene_frames
    scene_starts = [start for start, _ in schedule]

    matplotlib.rcParams["animation.ffmpeg_path"] = ffmpeg_path
    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])

    def draw_frame(frame_index: int):
        scene_index = min(max(bisect_right(scene_starts, frame_index) - 1, 0),
                          len(scenes) - 1)
        start, scene_frames = schedule[scene_index]
        progress = (frame_index - start) / scene_frames
        draw_scene(ax, scenes[scene_index], progress, brief)
        if (frame_index % 150 == 0 or frame_index == total_frames - 1) \
                and frame_index != draw_frame.last_reported:
            draw_frame.last_reported = frame_index
            print(f"  frame {frame_index + 1}/{total_frames} "
                  f"(scene {scene_index + 1}/{len(scenes)})", flush=True)
        return ()

    draw_frame.last_reported = -1

    animation = FuncAnimation(fig, draw_frame, frames=total_frames,
                              cache_frame_data=False)
    writer = FFMpegWriter(
        fps=fps, codec="h264",
        extra_args=["-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20"],
        metadata={"title": str(render_cfg.get("title", ""))},
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Rendering {total_frames} frames at {fps} fps "
              f"({width_px}x{height_px}, silent H.264 via '{encoder_name}') "
              f"to {output_path}", flush=True)
        animation.save(str(output_path), writer=writer)
    except Exception as exc:
        print(f"Error: video encoding failed while writing {output_path}: "
              f"{type(exc).__name__}: {exc}", flush=True)
        print("Fix the cause and render again; treat any partially written "
              "file as invalid.", flush=True)
        return 1
    finally:
        plt.close(fig)
    print(f"Wrote {output_path} ({total_frames} frames, "
          f"{total_frames / fps:.2f} s, silent).", flush=True)
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run exactly one mode, and return the exit code."""
    parser = argparse.ArgumentParser(
        prog="render_video.py",
        description="Render (or validate) an explainify explainer-video "
                    "storyboard as a silent 1280x720 30 fps H.264 MP4.",
    )
    parser.add_argument("--storyboard", metavar="PATH",
                        help="storyboard JSON file (required for --check-only "
                             "and --output)")
    parser.add_argument("--schema", metavar="PATH",
                        help="optional JSON schema overriding the embedded "
                             "storyboard schema")
    parser.add_argument("--check-only", action="store_true",
                        help="validate the storyboard and exit without rendering")
    parser.add_argument("--output", metavar="PATH", default=None,
                        help="render the video to this new MP4 path")
    parser.add_argument("--overwrite", action="store_true",
                        help="allow replacing an existing output file "
                             "(explicit user request only)")
    parser.add_argument("--self-test", action="store_true",
                        help="run the in-memory template self-test; encodes "
                             "nothing")
    args = parser.parse_args(argv)

    chosen = sum(1 for flag in (args.self_test, args.check_only,
                                bool(args.output)) if flag)
    if chosen != 1:
        parser.error("choose exactly one mode: --self-test, --check-only, "
                     "or --output PATH")
    if args.self_test:
        return _run_self_test()
    if not args.storyboard:
        parser.error("--storyboard PATH is required with --check-only "
                     "and --output")

    storyboard_path = Path(args.storyboard).expanduser()
    schema_path = Path(args.schema).expanduser() if args.schema else None

    if args.check_only:
        try:
            schema = _load_json(schema_path, "schema") if schema_path \
                else EMBEDDED_SCHEMA
            storyboard = _load_json(storyboard_path, "storyboard")
            validate_storyboard(storyboard, schema)
        except ValueError as exc:
            print(f"Storyboard validation failed: {exc}")
            return 1
        total_seconds = math.fsum(
            float(scene["duration_seconds"]) for scene in storyboard["scenes"])
        source = f"--schema {schema_path}" if schema_path else "the embedded schema"
        print(f"Storyboard OK ({storyboard_path}): "
              f"{len(storyboard['scenes'])} scene(s), "
              f"{total_seconds:.2f} s total, validated against {source}.")
        return 0

    # Render mode. Order matters: output guard, then encoder preflight, then
    # storyboard loading and validation, and only then any encoding work.
    output_path = Path(args.output).expanduser()
    if output_path.exists() and not args.overwrite:
        print(f"Error: output file already exists: {output_path}")
        print("No rendering was done and the existing file was left untouched; "
              "pass --overwrite only when replacing it was explicitly "
              "requested.")
        return 1

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        print("Error: ffmpeg was not found on PATH; install ffmpeg "
              "(preferably a build with libx264) before rendering.")
        return 1
    encoder_name = _find_h264_encoder(ffmpeg_path)
    if encoder_name is None:
        print(f"Error: ffmpeg at {ffmpeg_path} exposes no usable H.264 "
              "encoder; install a build with libx264 or another h264 "
              "encoder.")
        return 1

    try:
        schema = _load_json(schema_path, "schema") if schema_path \
            else EMBEDDED_SCHEMA
        storyboard = _load_json(storyboard_path, "storyboard")
        validate_storyboard(storyboard, schema)
    except ValueError as exc:
        print(f"Error: storyboard validation failed: {exc}")
        print("Nothing was rendered.")
        return 1

    return _render_storyboard(storyboard, output_path, ffmpeg_path,
                              encoder_name)


if __name__ == "__main__":
    raise SystemExit(main())
