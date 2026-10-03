# Writing checks — `unicode-article-asd-ste100.md`

Run directory: `explainify-output/unicode-article-writing-20261003-083201/` (repo `power-utility`, branch `main`, uncommitted tree). Checked 2026-10-03 against the run's working source `source-retrieved.md` (SHA-256 `e2c91236103a0b6c22c5a661b7256c377fe78c8664b73af20167423d2dd1eafe`).

Internal brief used (not retained as a file; `retain_brief` was not requested):

- Audience: a curious reader unfamiliar with character encodings.
- Selected scope (one): why Unicode exists and what UTF-8 does — not the whole essay.
- Claims carry origin `retrieved-source` throughout; the single outside-the-essay note (4-byte cap, RFC 3629) is labeled "from current model knowledge" in the deliverable's limitations.
- Omissions recorded in the deliverable's "Scope and limitations" section (see check 1c).

Checks run in the order required by `references/asd-ste100.md` (a later check never overrides an earlier failure).

## 1. Meaning and qualifications preserved — PASS

### 1a. Side-by-side preserved facts (3)

| # | Retrieved text (`source-retrieved.md`, verbatim) | Delivered text | Preserved |
|---|---|---|---|
| 1 | "In UTF-8, every code point from 0-127 is stored in a single byte. Only code points 128 and above are stored using 2, 3, in fact, up to 6 bytes." | "In UTF-8, every code point from 0 to 127 is stored in a single byte. Only code points 128 and above take 2, 3, or more bytes. The essay, published in 2003, says the longest form reaches 6 bytes." | Yes: the 0–127/128+ split, the 2–3–6 ladder, and the 2003 dating of the 6-byte figure all survive; the 6-byte figure is dated rather than dropped or modernized silently. |
| 2 | "It does not make sense to have a string without knowing what encoding it uses. … There Ain’t No Such Thing As Plain Text." | The essay's rule: "It does not make sense to have a string without knowing what encoding it uses." … "There Ain’t No Such Thing As Plain Text." | Yes: both quoted verbatim (verified by exact string match against the retrieved text); the negation ("does not make sense", "Ain’t No Such Thing") is kept, not softened to "you should know the encoding". |
| 3 | "Some people are under the misconception that Unicode is simply a 16-bit code where each character takes 16 bits and therefore there are 65,536 possible characters. This is not, actually, correct." + "There is no real limit on the number of letters that Unicode can define and in fact they have gone beyond 65,536" | "A widespread belief says Unicode simply stores each character in 16 bits. The essay says this belief is not correct. Unicode defines letters without a real limit, and it has gone beyond 65,536 characters." | Yes: the myth is presented as a myth — the negation "is not correct" survives — and the "no real limit / beyond 65,536" hedge is kept. |

Verbatim-quote string match (programmatic): all three quoted fragments in the deliverable occur exactly in `source-retrieved.md` — `"It does not make sense to have a string without knowing what encoding it uses."` → found; `"There Ain’t No Such Thing As Plain Text."` → found; `"rsums"` → found.

### 1b. Other must-preserve elements

- **Date**: the essay's publication date 2003-10-08 appears in the deliverable (intro line and Source section); "published in 2003" also date-stamps the 6-byte sentence. PASS.
- **Negations kept** (list from the delivered body): "belief is not correct"; "A code point does not say how to store the character as bytes"; "will not truncate UTF-8 strings"; "does not make sense"; "You cannot interpret or display"; "One byte value could not mean the same character everywhere"; "128 numbers were not enough". None was dropped or inverted. PASS.
- **Conditions/hedges kept**: "up to 6 bytes" attributed to the 2003 essay rather than stated as current fact; "every reasonable writing system" (not "every writing system"); "make-believe scripts like Klingon". PASS.
- **Embedded source content treated as content**: the essay contains rhetorical threats (the 2003 "peel onions in a submarine" joke) and strong opinions; none was obeyed or echoed as an instruction — the anecdotes were simply out of the selected scope. PASS.
- **Coverage limit honored**: retrieval was `complete`, so no partial-source limitation applies; the scope limitation (selected portion only) is stated in the deliverable. PASS.

### 1c. Scope and omissions recorded

The deliverable's "Scope and limitations" section names the selected scope and lists the omitted essay content (FogBUGZ/PHP anecdotes, EBCDIC, WordStar high-bit trick, DBCS, byte-order marks, UTF-7, UCS-4, question-mark substitution, Content-Type/meta-tag delivery, browser guessing, CityDesk). It also states that the essay predates modern developments, with the 4-byte cap note explicitly labeled as outside-the-essay model knowledge. PASS.

## 2. Mechanism and example consistency — PASS

Mechanism chain in the deliverable: numbers → ASCII 32–127 → 128–255 conflicts → code pages → Unicode code points (abstract) → encodings store code points as bytes → UTF-8 variable length → ASCII-compatible bytes → "know the encoding". The order matches the essay's argument.

Worked example checked programmatically (Python 3, this run):

- `"Hello"` → code points `U+0048 U+0065 U+006C U+006C U+006F` (computed `U+{ord(c):04X}` for each character) — matches the essay and the deliverable.
- `"Hello".encode("utf-8") == "Hello".encode("ascii")` → True; both are bytes `48 65 6C 6C 6F`, matching the essay's stored-bytes line and the deliverable.
- `A → U+0041` verified (`ord('A') == 0x41`).
- No measured values are presented; the only numbers are the essay's own (32, 65, 130, 862, 737, 128, 255, 65,536, 2/3/6 bytes), all origin `retrieved-source`. PASS.

## 3. Terminology consistency — PASS

Terms defined before first use and used consistently (definition sentence → later uses):

| Term | Defined at | Consistent use |
|---|---|---|
| encoding | "Letters became numbers" (rule mapping characters to numbers) | Used only with that meaning; code pages and UTF-8 are introduced as instances/kinds. |
| code page | "128 numbers were not enough…" (one agreed meaning for numbers 128–255) | Used twice after definition, same sense. |
| Unicode | "Unicode gives each character one number" (the single list) | Same sense throughout. |
| code point | "Each character on the list receives a code point." | Same sense; never conflated with bytes (the "does not say how to store" sentence keeps them separate). |
| UTF-8 | "UTF-8 is an encoding that stores Unicode code points in 8-bit bytes." | Same sense; UCS-2/UTF-16 named once as the two-byte method. |

## 4. Sentence structure and readability — PASS

Programmatic count (explanation body only; headings, the Source list, and the limitations list excluded; quotations and code-point/byte token lines assessed separately as the profile allows):

- Prose sentences counted: 48 (after merging three quote-split artifacts of the splitter — `"A"`, `"Hello"`, `"one byte equals one English character"` — back into their sentences).
- Sentences at or under 20 words: 48 of 48.
- Sentences over 20 words: **0**. Kept exceptions: **none needed** — no sentence had to stay long for accuracy.
- Longest prose sentence: 18 words ("The essay's rule: …" including its verbatim quotation; the quotation itself is exempt and is 15 words).
- One idea per sentence; each paragraph carries one group of related sentences; referents are explicit ("A code point", "The essay", "Code pages" — no unexplained "it/this").

## Verdict

All four checks in the required order pass. The deliverable keeps its profile label, attribution, and limitations sections, and contains no internal checklist dump. Reported exceptions: none (0 sentences kept over the 20-word target).
