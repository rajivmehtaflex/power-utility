# Focused teaching brief — long input (C7 part A)

Run: `explainify-output/long-input-writing-20261003-083800/` (2026-10-03). This brief is
the first artifact of the writing workflow's long-input path: the 2,116-word source
below was distilled into one focused brief before any explanation was written. In a
normal writing run the brief stays internal; it is retained here as a file because the
C7 evaluation explicitly asks for the focused brief and the record of omissions
(equivalent to `retain_brief`).

## Source provenance

- Source kind: `.md` file (`kind: file`), path `long-input-source.md` in this run
  directory.
- Provenance: survey text authored for this evaluation fixture ("Pumped-storage
  hydropower: a survey", 12 sections, 2,116 words, generated 2026-10-03 for C7 part A).
- Retrieval status: `not-applicable` (local file; read completely).
- Claim origins: all claims below trace to the supplied file (`origin:
  provided-source`); the file itself is an authored evaluation fixture, and the
  deliverable attributes its facts to that supplied text only.

## Focus selection (one focus, per the long-input rule)

**Selected focus:** how a pumped-storage plant stores energy and gives it back — the
two-mode mechanism (pump uphill / generate downhill) and the mass-times-height energy
relation that explains why the reservoirs matter.

**Why this focus:** it is the source's central mechanism (§2 and the physics of §3);
every other section depends on it, so it is the natural single teaching objective.

**Audience:** a curious reader unfamiliar with pumped storage.
**Learning objective:** after reading, the learner can explain how the plant moves
energy in time using water, and why the amount of water and the height difference set
how much energy is stored.

## Brief fields

- **Prerequisites:** electricity can power motors; water flowing downhill can spin a
  turbine; energy cannot be created, only converted.
- **Terms:** *reservoir* — a large store of water; *waterway* — the large pipe between
  the reservoirs; *pump-turbine* — one reversible machine that pumps in one rotation
  direction and generates in the other; *potential energy* — energy stored by height.
- **Core claim:** a pumped-storage plant is a storage device, not an energy source; it
  stores grid electricity as lifted water and returns most of it later.
- **Mechanism (ordered):**
  1. Surplus electricity drives the machine as a pump.
  2. The pump pushes water up the waterway into the upper reservoir.
  3. The lifted water holds potential energy.
  4. When power is needed, water is released down the same waterway.
  5. The machine runs the other way as a turbine; a generator sends electricity to
     the grid.
  6. The water waits in the lower reservoir, ready for the next cycle.
- **Claims:**
  - `claim-1` — the plant is a storage device, not a primary energy source
    (`provided-source`; keep the negation).
  - `claim-2` — pumping mode stores energy as lifted water; generating mode returns it
    (`provided-source`).
  - `claim-3` — stored energy equals mass × gravity × height; doubling mass or height
    doubles it (`provided-source`).
  - `claim-4` — the water is never used up by the cycle (`provided-source`; keep the
    negation).
  - `claim-5` — mode changes are not instant; the machine must stop and restart in the
    other direction (`provided-source`; keep the negation).
  - `claim-6` — the plant always returns less energy than it consumed pumping
    (`provided-source`; keep the negation; details of losses are out of focus).
  - `claim-7` — power (delivery speed, set by machines) differs from stored energy
    (amount, set by reservoirs) (`provided-source`).
- **Example:** illustrative only — 1,000,000 kg lifted 100 m stores
  1,000,000 × 9.81 × 100 = 981 MJ ≈ 272.5 kWh before losses. Values marked
  `illustrative` (the source marks them illustrative too); arithmetic re-checked:
  9.81e8 J ÷ 3.6e6 J/kWh = 272.5 kWh.
- **must_preserve:** "not a source of primary energy"; "the water is never used up";
  "the change between modes is not instant"; "always returns less energy than it
  consumed"; illustrative label on the example values; power-vs-energy distinction.
- **Omissions:** see the next section — the deliverable's scope-limitations section
  lists them in full.

## Record of what was omitted (by source section)

| Source section | Disposition |
|---|---|
| §1 What pumped storage is | used only for the storage-not-source claim and the cycle idea; the market framing ("buy cheap, sell dear") omitted |
| §2 The basic mechanism | **covered** (focus) |
| §3 Energy, power, and the height relation | **covered** (focus; incl. illustrative example, power-vs-energy) |
| §4 Round-trip efficiency and losses | omitted (only claim-6's "returns less" pointer retained) |
| §5 History (1880s Alps, 1929+, Ludington 1973, Bath County 1985) | omitted entirely |
| §6 Open-loop and closed-loop plants | omitted entirely |
| §7 Siting and geography (incl. snow/ice paragraph) | omitted entirely |
| §8 Environmental effects | omitted entirely |
| §9 Economics and market role | omitted entirely |
| §10 Comparison with batteries | omitted entirely |
| §11 Open questions | omitted entirely |
| §12 Response speed and operating habits | omitted entirely |

Omission rule followed: the explanation covers the selected focus only; a reader who
needs the omitted sections can request a longer or multi-part follow-up rather than
getting them squeezed in.
