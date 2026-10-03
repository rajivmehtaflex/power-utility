# How pumped storage stores and returns energy — STE-inspired explanation

**STE-inspired simplified English — approximate, not validated for ASD-STE100 conformity**

## The explanation

Pumped storage stores energy by moving water between two reservoirs at different
heights. A pumped-storage plant is a storage device, not a source of primary energy.
The plant has two modes.

In pumping mode, the plant takes surplus electricity from the grid. This electricity
drives the plant's machine as a pump. The pump pushes water uphill through a large
pipe. This pipe is called the waterway. In generating mode, the plant releases water
from the upper reservoir. The water flows down the same waterway and spins the
machine as a turbine. A generator then converts this rotation into electricity for
the grid. Many modern plants use one reversible machine, a pump-turbine. This machine
pumps in one rotation direction and generates in the other direction. The change
between modes is not instant. The machine must slow, stop, and restart in the other
direction.

Lifted water holds stored energy, called potential energy. The stored energy equals
the mass of the water, times gravity, times the height of the lift.

Illustrative example (values are illustrative, not measured on a real plant):

- Water lifted: 1,000,000 kg
- Height: 100 m
- Stored energy: 1,000,000 × 9.81 × 100 ≈ 981 MJ ≈ 272.5 kWh, before losses

Doubling the height doubles the stored energy. Doubling the mass also doubles the
stored energy. The height difference is therefore the most important design choice.
Power and stored energy are different quantities. Power is how fast the plant can
deliver the stored energy. The machine size sets the power. The reservoir size sets
the stored energy.

The plant always returns less energy than it consumed while pumping. The water itself
is never used up. After each cycle, the water waits in the lower reservoir, ready to
be lifted again.

## Source attribution

- Source kind: `.md` file (`kind: file`), `long-input-source.md` — a 2,116-word,
  12-section survey, "Pumped-storage hydropower: a survey", supplied as the long input
  for this run (authored evaluation fixture, C7 part A).
- Retrieval status: `not-applicable` (local file, read completely).
- Claim origins: every factual statement above comes from the supplied survey
  (`origin: provided-source`), sections 2 and 3 only. No web source was consulted and
  no citation was invented. The worked example's values are illustrative, exactly as
  the source marks them.

## Material scope limitations (long input — one focus only)

This explanation covers the selected focus only: the two-mode mechanism and the
mass-times-height energy relation (source §2 and §3). The source's other sections were
deliberately omitted:

- §1 market framing of pumped storage ("buy cheap energy, sell it later")
- §4 round-trip efficiency and losses (only the pointer "returns less than consumed"
  was kept)
- §5 history (1880s Alpine plants, growth after the late 1920s, Ludington 1973, Bath
  County 1985)
- §6 open-loop versus closed-loop plant types
- §7 siting and geography, including snow and ice constraints
- §8 environmental effects
- §9 economics and market role
- §10 comparison with batteries
- §11 open questions
- §12 response speed and operating habits

If you need the omitted sections, ask for a longer or multi-part follow-up; they were
left out to keep this output focused, not because they were judged unimportant.
