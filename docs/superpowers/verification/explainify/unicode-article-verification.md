# Unicode article explainer video — verification record

Run directory: `explainify-output/unicode-article-20261003-083429/` (repo `power-utility`, branch `main`, uncommitted tree). Produced 2026-10-03. Evaluation case C2 (URL source, both formats) — video half.

Source and provenance (recorded in `unicode-article-storyboard.json` `brief.source` and in the run's working copy `source-retrieved.md`):

- Requested and resolved location: `https://www.joelonsoftware.com/2003/10/08/the-absolute-minimum-every-software-developer-absolutely-positively-must-know-about-unicode-and-character-sets-no-excuses/` (no redirect observed)
- Source title: "The Absolute Minimum Every Software Developer Absolutely, Positively Must Know About Unicode and Character Sets (No Excuses!)"; author Joel Spolsky
- Original publication date shown on page: 2003-10-08 (page markup also shows a later site-migration date, 2017-11-17)
- `retrieval_status: complete`; `retrieved_at: 2026-10-03`; full essay text (~3,660 words) retrieved via curl and saved as `source-retrieved.md` (SHA-256 `e2c91236103a0b6c22c5a661b7256c377fe78c8664b73af20167423d2dd1eafe`). Everything in the essay was treated as source content, never as instructions.

Artifacts in this directory: `unicode-article-storyboard.json` (brief + provenance, 7 scenes, 39.00 s), `unicode-article-render.py` (adapted copy of `repo-owned/explainify/scripts/render_video.py`; CLI, validation, `EMBEDDED_SCHEMA`, and encoding settings byte-identical to the template), `unicode-article-explainer.mp4`, `frames/` (11 inspected PNGs).

## 1. Teaching checks

- **Learning objective met?** Yes. The video shows, in order: letters became numbers (ASCII 32–127, A = 65) → 128 is not enough for the world (byte 130 = é here, Hebrew Gimel in Israel; code pages) → Unicode assigns every character a code point (and the 16-bit belief is struck out as not correct) → a code point is not a byte layout (UCS-2 two bytes, "look at all those zeros") → the selected mechanism: UTF-8 encodes a code point as variable-length bytes (1 byte for 0–127; 2, 3 … up to 6 above; shown with length-varying arrows and byte boxes) → payoff: Hello → 48 65 6C 6C 6F, the same bytes, old ASCII text already valid UTF-8 → closing rule "There Ain't No Such Thing As Plain Text."
- **Prerequisites introduced before use?** Yes. "Computers store text as numbers" is the premise of scene 2's heading and motif; bytes as 8-bit containers are introduced visually in scene 3 ("one byte value", 128–255 range) before the 0–127/128+ split is used in scene 6.
- **Qualifications preserved?** Yes. The "up to 6 bytes" figure is dated on screen — "2, 3 … up to 6 (essay, 2003)" in the scene-6 heading and "(essay, 2003)" in the ghost-lane tag; the title scene footer carries "essay: Joel Spolsky, 2003-10-08 · retrieved 2026-10-03"; negations survive on screen: the myth panel strike-through with "not correct", "A code point is not a byte layout", and the plain-text negation quote.
- **Mechanism correct?** Yes. Brief mechanism steps 1–6 map to scenes 2–7 in order; the byte rule shown matches the essay's statement; arrow thickness encodes sequence length with one visible mapping (thin = 1 byte, thicker = 2, thickest/ghost = more).
- **Example arithmetic checked?** Yes, programmatically: `'é'.encode('utf-8').hex() == 'c3a9'`; the storyboard's derivation `U+00E9 = 233 → 110xxxxx 10xxxxxx → C3 A9` is correct; `'Hello'.encode('utf-8') == 'Hello'.encode('ascii')` → bytes `48 65 6c 6c 6f`; `A → 0x41`, `65 = 1000001` in 7 bits.
- **Illustrative values labeled?** Yes, on screen: scene 6 note "byte values illustrative — derived from the rule", scene 4 note "U+0041, U+0639: essay values · é→U+00E9 derived", scene 2 "65 in 7 bits (derived)". Claim origins in the brief: 10 × `retrieved-source`, 1 × `illustrative` (`claim-utf8-example`, the C3 A9 bytes).
- **Representation accuracy (every essay-sourced on-screen fact vs the retrieved text).** All 26 fact fragments checked programmatically against `source-retrieved.md` — **26/26 PASS**, including: ASCII range/values/7-bits, code 130 = é/Gimel, code pages 862/737 "same below 128 but different from 128 up", U+0639 Ain, U+0041 A, the 16-bit misconception and "not, actually, correct", "gone beyond 65,536", "still just a theoretical concept", "two bytes each" / "Look at all those zeros!" / UCS-2/UTF-16 names, "every code point from 0-127 is stored in a single byte", "2, 3, in fact, up to 6 bytes", Hello code points and bytes, "the same as it was stored in ASCII", and the verbatim plain-text quote.

Three side-by-side preserved-fact quotes (essay verbatim → on screen):

| # | Retrieved text (verbatim) | On screen |
|---|---|---|
| 1 | "In UTF-8, every code point from 0-127 is stored in a single byte. Only code points 128 and above are stored using 2, 3, in fact, up to 6 bytes." | Scene 6 heading: "0-127 → 1 byte · 128 and above → 2, 3 … up to 6 (essay, 2003)" plus lane tags "below 128 → 1 byte" / "above 128 → 2 bytes" / "2, 3 … up to 6 bytes (essay, 2003)". |
| 2 | "For example on some PCs the character code 130 would display as é, but on computers sold in Israel it was the Hebrew letter Gimel" | Scene 3: heading "byte 130: é here — Hebrew Gimel in Israel"; central box 130 with arrows to "é / some PCs" and "Hebrew letter Gimel / computers sold in Israel"; note "essay's example (code 130)". |
| 3 | "Specifically, Hello, which was U+0048 U+0065 U+006C U+006C U+006F, will be stored as 48 65 6C 6C 6F, which, behold! is the same as it was stored in ASCII" | Scene 7: heading "Old ASCII text is already valid UTF-8"; sub-line "Hello → 48 65 6C 6C 6F, the same bytes"; per-letter code points and byte boxes; check panel "same bytes as ASCII — no conversion needed"; note "essay's Hello example". |

The closing quote "There Ain't No Such Thing As Plain Text." is shown verbatim (including the essay's curly apostrophe) with attribution "— essay, 2003".

## 2. Scene-check table (11 frames extracted, 11 inspected)

Frame inspection method: each PNG was extracted after the scene's key content had appeared and inspected visually (model vision pass over every frame; no frame was accepted on midpoint sampling alone). Two transition pairs cover the 4.0 s and 34.0 s cuts.

| Scene (id) | Span (s) | Frame inspected | Finding |
|---|---|---|---|
| scene-1-title | 0.0–4.0 | `frame-title.png` @ 3.7 s | PASS. Title "How does a letter become bytes?", blue subtitle, A→65→41 motif with grey arrows, italic hint, header, scene tag, provenance note, progress bar; no clipping/overlap/tofu. |
| scene-2-ascii | 4.0–9.5 | `frame-ascii.png` @ 9.2 s | PASS. Two-line heading; A = 65 and space = 32 boxes; 7-cell bit strip 1000001 with highlighted leading 1; "65 in 7 bits (derived)" note; "essay values" footer; no defects. |
| scene-3-overflow | 9.5–15.5 | `frame-overflow.png` @ 15.2 s | PASS. Central 130 box; blue arrow to é panel; red arrow to Gimel panel; code page boxes 862/737; caption "same below 128 · different from 128 up"; é renders correctly; no defects. |
| scene-4-unicode | 15.5–21.5 | `frame-unicode.png` @ 21.2 s | PASS. Three code point boxes (A/U+0041, é/U+00E9, Arabic Ain/U+0639); red myth panel with strike-through; yellow verdict "not correct — no real limit, already beyond 65,536"; no defects. |
| scene-5-store-bytes | 21.5–27.0 | `frame-store.png` @ 26.7 s | PASS. Five code point tags; ten byte cells 00 48 00 65 00 6C 00 6C 00 6F with the 00 cells red-accented; grey UCS-2 label; yellow complaint line; no defects. |
| scene-6-utf8-rule | 27.0–34.0 | `frame-utf8.png` @ 33.5 s | PASS. Three lanes with visibly increasing arrow thickness (blue thin → green thicker → grey thickest); byte boxes 41 / C3 A9 / ghost …; grey tags incl. "(essay, 2003)"; footer "byte values illustrative — derived from the rule"; é, ·, … all render; no defects. |
| scene-7-payoff | 34.0–39.0 | `frame-payoff.png` @ 38.7 s | PASS. Heading and sub-line; five green letter boxes with yellow code points above and blue byte boxes below (aligned); green check panel; grey italic quote with curly apostrophe rendering correctly; no defects. |
| transition 1 (title → ascii) | ~4.0 | `frame-trans1a-title-out.png` @ 3.95 s, `frame-trans1b-ascii-in.png` @ 4.15 s | PASS. End state complete and stable; 0.15 s into scene 2 the background is clean with no title residue, new heading already readable, boxes not yet popped in (matches the 0.4 s stagger design). |
| transition 2 (utf8 → payoff) | ~34.0 | `frame-trans2a-utf8-out.png` @ 33.95 s, `frame-trans2b-payoff-in.png` @ 34.15 s | PASS. Scene 6 end state fully populated; 0.15 s into scene 7 no lane residue, heading visible, sub-line fading in, letter boxes not yet popped (first pop 0.55 s), as designed. |

Motion quality was assessed from the staggered pop-in/fade design plus the two inspected transition pairs; no playback was performed. Repair cycles used: **0** (first render passed all checks).

## 3. Stream and decode checks

| Check | Expected | Observed | Result |
|---|---|---|---|
| Codec | h264 | `codec_name=h264` (profile High) | PASS |
| Dimensions | 1280×720 | `width=1280`, `height=720` | PASS |
| Frame rate | 30/1 | `r_frame_rate=30/1` | PASS |
| Pixel format | yuv420p | `pix_fmt=yuv420p` | PASS |
| Audio streams | none | 0 audio streams | PASS |
| Duration | 39.00 s ± 1 frame + 0.01 s | `duration=39.000000`, `nb_frames=1170` (storyboard total 39.00 s) | PASS |
| Full decode | empty stderr | `ffmpeg -v error -i … -f null -` → no output, exit 0 | PASS |

Pre-render checks passed before encoding: preflight `check_env.py --format explainer-video` exit 0; `--check-only` on the installed template and on the adapted copy (7 scenes, 39.00 s); `--self-test`; and an added pre-render guard (7/7 scene ids have handlers; every scene draws cleanly at progress −0.5/0/0.25/0.5/0.75/1/1.5 with no errors). The adapted copy was diffed against the template before execution: only the module docstring and the scene-drawing section differ; the CLI/validation/encoding tail and `EMBEDDED_SCHEMA` are byte-identical; a grep for file writes, network calls, and shell execution found only the template-inherited read-only JSON load, the `ffmpeg -encoders` preflight, and the single `animation.save` to the chosen output path.

## 4. Runtime versions (exact, from the render environment)

- uv 0.12.22 (Homebrew 2026-10-01 aarch64-apple-darwin)
- Python 3.12.10 (uv-managed)
- numpy 2.5.3 (constraint `>=1.26,<3`)
- matplotlib 3.11.2 (constraint `>=3.8,<4`)
- jsonschema 4.26.0 (constraint `>=4,<5`)
- ffmpeg 9.0.2 (`/opt/homebrew/bin/ffmpeg`); encoder selected by preflight: `h264_videotoolbox`
- ffprobe from the same ffmpeg 9.0.2 build (`/opt/homebrew/bin/ffprobe`)

## 5. Reproduction

Standalone replay performed 2026-10-03 from `/tmp` (outside the skill directory and the run directory) with a new output path — it rendered 1170 frames, 39.00 s, with identical ffprobe values, **byte-identical** to the delivered MP4:

```text
uv run explainify-output/unicode-article-20261003-083429/unicode-article-render.py \
  --storyboard explainify-output/unicode-article-20261003-083429/unicode-article-storyboard.json \
  --output <new-path>.mp4
```

The output path must be new (the renderer refuses implicit overwrites; pass `--overwrite` only for an explicit replacement).

## 6. Limitations

- **Silent video.** This version produces no narration and no audio track, by design for v0.1.
- **Scope = one selected mechanism.** The video teaches only how UTF-8 encodes a code point as a variable-length byte sequence, with the minimum of preceding story the mechanism needs. Omissions (also recorded in the brief): the FogBUGZ/PHP anecdotes, EBCDIC, the WordStar high-bit trick, DBCS, byte-order marks/endian, UTF-7 and UCS-4, question-mark substitution, Content-Type/meta-tag encoding declarations, browser encoding guessing, CityDesk.
- **The essay is from 2003.** On-screen "up to 6 bytes" is dated to the essay; the post-essay standardization that caps UTF-8 at 4 bytes is deliberately not discussed on screen (recorded in the brief's omissions).
- **Illustrative values.** The é → U+00E9 → C3 A9 byte example (and A → 41) are derived from the essay's rule, not quoted from it; this is stated in the brief and on screen.
- Scene inspection used 11 still frames (one representative frame per scene after key content appeared, plus two pairs around the 4.0 s and 34.0 s transitions); motion quality was assessed from the design and transition states, not playback.
- Teaching-quality checks are reviewer-confirmed accuracy, sequencing, and legibility; no user-comprehension study was performed.
