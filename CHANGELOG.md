# Changelog

<!--
The GitHub release body is the first "## " section of this file only, so it
always shows the version being released and nothing else. Add new versions on
top, under this line. Older sections are safe to delete once released.
-->

## 2.5 - The shadows were one-sided and the cards had none at all

### The card shadow was covered
`NeumoCard` packed its content Frame with `fill="both", expand=True`, edge to
edge, with `bg=SURFACE`. That flat background covered the entire card,
including the shadow ring the Canvas underneath was rendering. The cards were
never showing a shadow; they were rectangles of flat base colour with a
hairline where the image ended. The content frame is now inset by the shadow
margin, so the ring is visible.

### The highlight was being cancelled by the shadow
Measured on a card against a base of 224: the dark shadow reached -37 and the
light highlight only +7. The cause was `depth=3` with `blur=5`. The dark
shadow is the silhouette offset down-right, and with a 5px sigma its falloff
reached 10px back across the surface, landing on top of the light shadow's
own band and subtracting most of it. The lift was one-sided, so the cards
read as flat on the top and left.

Measured across parameter sets rather than guessed:

| depth | blur | highlight | shadow | ratio |
|---|---|---|---|---|
| 3 | 5 | +7 | -36 | 5.1 (rejected) |
| 4 | 4 | +15 | -45 | 3.0 |
| 5 | 3 | +26 | -42 | 1.6 (chosen) |

Now `SHADOW_DEPTH=5`, `SHADOW_BLUR=3`. Card and button measure +20 / -53,
compact controls +19 / -49, inset wells -43 / +26.

### Shadows now derive from the surface they sit on
Fixed shadow colours only work on a light base. On the accent fill the dark
shadow colour was lighter than the fill itself, so it measured -1 against a
base of 123 while the white highlight measured +116: a flat slab with a glow.
The renderer now derives both from the base colour, so the pair stays
symmetric on any fill. The primary button also became a surface pill with
accent text, which is what the reference does; a solid accent slab is the one
thing that cannot read as neumorphic.

### Shadows composite additively
The highlight and the shadow are separate light contributions, so they are
composed into one RGBA layer rather than pasted one over the other onto the
base.

### Size
Cards grew 22px once the content frame stopped covering the shadow margin.
The window is now 560x540. All four cards verified to contain their content,
and the action bar verified inside the window bounds.

Build stamp is now `v2.5 build 05376d9a`.
