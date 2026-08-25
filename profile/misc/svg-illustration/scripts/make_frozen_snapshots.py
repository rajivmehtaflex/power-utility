#!/usr/bin/env python3
"""
make_frozen_snapshots.py — Frozen-frame verifier for animated SVG with limbs tracking a rotating part.

WHY: `rsvg-convert` renders only t=0, so it cannot show a SMIL animation mid-cycle. To prove a
foot stays glued to a pedal at an arbitrary crank angle, freeze the scene at chosen frame
indices and rasterize those, then vision-check.

WHAT IT DOES:
  - Reads fragment files under --fragdir (each a <g id="..."> block, NOT a full SVG).
  - Reads shared IK values from --ik (JSON: keys "left", "right" = 12 leg-path strings each,
    "keyTimes" = "0;0.09;...") for static leg paths.
  - Reads a shared _shell.txt (defs + <style>) for both master assembly and snapshots.
  - For each frame k in --frames, writes snap_k.svg + snap_k.png:
      * leg paths frozen to static d = (phase A if leg is "front"/in-front, phase B if "behind")
      * crank group gets transform="rotate(k*step_deg cx cy)" and its <animateTransform> stripped
      * wheel <animateTransform> stripped (frozen at t=0, fine for foot check)
  - Prints PNG sizes + return codes so you can confirm render success.

USAGE:
  python3 scripts/make_frozen_snapshots.py \
      --fragdir fragments --ik fragments/ik_values.json \
      --shell fragments/_shell.txt --out snapshots \
      --order background wheels frame frog_body crank fx \
      --legs-behind legs_right_behind --legs-front legs_left_front \
      --cx 460 --cy 380 --step-deg 30 --frames 3 6 9

Then vision_analyze each snap_k.png: "Does the webbed foot sit exactly on the pedal platform,
no gap?" All three should say yes — that proves the baked IK is correct at every angle.
"""
import os, re, json, argparse, subprocess

def grab(block_id, raw):
    m = re.search(r'(<g id="%s">.*?</g>)' % re.escape(block_id), raw, re.S)
    if not m:
        raise SystemExit(f"fragment missing block {block_id}")
    return m.group(1).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragdir", required=True)
    ap.add_argument("--ik", required=True)
    ap.add_argument("--shell", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--order", nargs="+", required=True,
                    help="z-order fragment ids (without .svg), back-to-front")
    ap.add_argument("--legs-behind", default=None,
                    help="fragment block id that must render BEFORE frog_body")
    ap.add_argument("--legs-front", default=None,
                    help="fragment block id that must render AFTER frog_body")
    ap.add_argument("--frog-body", default="frog_body")
    ap.add_argument("--cx", type=float, required=True)
    ap.add_argument("--cy", type=float, required=True)
    ap.add_argument("--step-deg", type=float, default=30.0,
                    help="crank degrees advanced per IK frame index")
    ap.add_argument("--frames", nargs="+", type=int, default=[3, 6, 9])
    ap.add_argument("--rsvg", default="rsvg-convert")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    ik = json.load(open(args.ik))
    L, R = ik["left"], ik["right"]
    assert len(L) == len(R), "IK left/right length mismatch"
    N = len(L)

    shell = open(args.shell).read()
    frags = {n: open(os.path.join(args.fragdir, n + ".svg")).read() for n in args.order}
    # if legs are inside a combined file (e.g. legs.svg), split them out
    leg_parts = {}
    if args.legs_behind and args.legs_front:
        for n, txt in frags.items():
            if f'id="{args.legs_behind}"' in txt and f'id="{args.legs_front}"' in txt:
                leg_parts[args.legs_behind] = grab(args.legs_behind, txt)
                leg_parts[args.legs_front] = grab(args.legs_front, txt)
                break

    def freeze(k):
        d_left = L[k]
        d_right = R[k]
        rot = k * args.step_deg
        parts = []
        for n in args.order:
            if n == args.legs_behind or n == args.legs_front:
                continue  # handled below, placed around frog_body
            s = frags[n]
            if n == "crank":
                s = s.replace('<g id="crank">',
                              f'<g id="crank" transform="rotate({rot} {args.cx} {args.cy})">', 1)
                s = re.sub(r'<animateTransform[^/]*?/>', '', s)
            elif "wheels" in n:
                s = re.sub(r'<animateTransform[^/]*?/>', '', s)
            parts.append(s)
        # assemble with legs straddling frog_body
        out = []
        for n in args.order:
            if n == args.legs_behind:
                blk = leg_parts.get(args.legs_behind, "")
                blk = re.sub(r'<path fill="none" stroke="#3D7B40"[^>]*>.*?</path>',
                             f'<path fill="none" stroke="#3D7B40" stroke-width="8" '
                             f'stroke-linecap="round" stroke-linejoin="round" d="{d_right}"/>',
                             blk, count=1, flags=re.S)
                out.append(blk)
            elif n == args.frog_body:
                out.append(frags[n])
            elif n == args.legs_front:
                blk = leg_parts.get(args.legs_front, "")
                blk = re.sub(r'<path fill="none" stroke="url\(#frogGreen\)"[^>]*>.*?</path>',
                             f'<path fill="none" stroke="url(#frogGreen)" stroke-width="9" '
                             f'stroke-linecap="round" stroke-linejoin="round" d="{d_left}"/>',
                             blk, count=1, flags=re.S)
                out.append(blk)
            else:
                out.append(parts.pop(0))
        return shell + "\n" + "\n".join(out) + "\n</svg>\n"

    for k in args.frames:
        assert 0 <= k < N, f"frame {k} out of range (N={N})"
        svg = freeze(k)
        p = os.path.join(args.out, f"snap_k{k}.svg")
        with open(p, "w") as f:
            f.write(svg)
        png = os.path.join(args.out, f"snap_k{k}.png")
        r = subprocess.run([args.rsvg, "-w", "800", "-h", "600", p, "-o", png],
                           capture_output=True, text=True)
        print(f"k={k}: svg={len(svg)}B png={os.path.getsize(png) if os.path.exists(png) else 'FAIL'} "
              f"rc={r.returncode} {r.stderr.strip()[:80]}")

if __name__ == "__main__":
    main()
