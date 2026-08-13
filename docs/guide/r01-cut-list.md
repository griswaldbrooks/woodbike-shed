---
page: R01
title: Reference — cut list
prev: 16-troubleshooting.md
next: r02-sources.md
---

# Reference — cut list

> **Goal:** look up any framing part's count, lumber, and cut length while you are at the saw.

Framing only. The finish cuts (siding, trim, doors) and the per-board stock packing that
turns these lengths into the order quantities live in `CUT_LIST.md` at the repo root —
its FINISH sections and its "Stock-length order list" are the authority, and this page
mirrors the framing tables for scanning. Actual dimensions, no kerf; the packing adds
⅛″ per cut.

Lengths below are rounded to the nearest ⅛″. Where a part is not an exact eighth
(the rake studs, rake plates, rafters), the exact value is in `CUT_LIST.md` — mark it
from the exact number, not this table.

## Skids

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 2 | skid | 4×4 PT | 16′ |

## Floor

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 2 | rim joist | 2×6 PT | 16′ |
| 14 | floor joist | 2×6 PT | 5′ 9″ |
| 4 | sub floor osb | OSB ¾″ half sheet | 6′ × 4′ |

## Back wall

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 1 | back wall bottom plate | 2×4 KD | 16′ |
| 1 | back wall top plate | 2×4 KD | 16′ |
| 1 | back wall double top plate short | 2×4 KD | 15′ 5″ |
| 13 | back wall studs | 2×4 KD | 7′ 8⅝″ |

## Front wall

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 1 | front wall bottom plate | 2×4 KD | 16′ |
| 1 | front wall top plate | 2×4 KD | 16′ |
| 1 | front wall double top plate | 2×4 KD | 16′ |
| 1 | front wall king studs | 2×4 KD | 10′ |
| 8 | front wall king studs | 2×4 KD | 9′ 10½″ |
| 2 | front wall jack studs | 2×4 KD | 7′ |
| 2 | front wall jack studs | 2×4 KD | 6′ 10½″ |
| 3 | front wall headers | 2×4 KD | 6′ 3″ |
| 3 | front wall headers | 2×4 KD | 3′ 3″ |
| 6 | front wall cripple studs | 2×4 KD | 2′ 7″ |

## Left wall

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 5 | left side wall studs | 2×4 KD | 7′ 8⅝″ |
| 1 | left wall double top plate | 2×4 KD | 5′ 8½″ |
| 1 | left side wall bottom plate | 2×4 KD | 5′ 5″ |
| 1 | left wall top plate | 2×4 KD | 5′ 5″ |

## Right wall

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 5 | right wall studs | 2×4 KD | 7′ 8⅝″ |
| 2 | right wall jack studs | 2×4 KD | 6′ 10½″ |
| 1 | right wall double top plate | 2×4 KD | 5′ 8½″ |
| 1 | right wall top plate | 2×4 KD | 5′ 5″ |
| 3 | right wall headers | 2×4 KD | 3′ 3″ |
| 1 | right wall bottom plate long | 2×4 KD | 1′ 8½″ |
| 1 | right wall bottom plate short | 2×4 KD | 8½″ |
| 2 | right wall cripple studs | 2×4 KD | 5⅛″ |

## Left rake wall

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 1 | left rake wall top plate | 2×4 KD | 5′ 9⅜″ |
| 1 | left rake wall studs | 2×4 KD | 1′ 10¾″ |
| 1 | left rake wall studs | 2×4 KD | 1′ 5″ |
| 1 | left rake wall studs | 2×4 KD | 11″ |
| 1 | left rake wall studs | 2×4 KD | 5″ |

## Right rake wall

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 1 | right rake wall top plate | 2×4 KD | 5′ 9⅜″ |
| 1 | right rake wall studs | 2×4 KD | 1′ 10¾″ |
| 1 | right rake wall studs | 2×4 KD | 1′ 5″ |
| 1 | right rake wall studs | 2×4 KD | 11″ |
| 1 | right rake wall studs | 2×4 KD | 5″ |

## Roof

| Qty | Part | Lumber | Length |
|---:|---|---|---:|
| 1 | back fascia | 2×6 KD | 18′ |
| 1 | front fascia | 2×6 KD | 18′ |
| 1 | left rake board | 2×6 KD | 9′ 7⅜″ |
| 13 | rafter | 2×6 KD | 9′ 7⅜″ |
| 1 | right rake board | 2×6 KD | 9′ 7⅜″ |

## Finish cuts and stock packing

Not repeated here. `CUT_LIST.md` at the repo root carries:

- the FINISH siding, trim, door, and hardware tables (the finish order),
- the framing and finish "Stock-length order list" — which part comes off which bought board, with waste per board,
- the order quantities these tables pack into ([P02](02-order-framing.md) and [P03](03-order-finish.md)).

## Before you move on

- [ ] Any length that is not an exact ⅛″ on this page was marked from `CUT_LIST.md`'s exact value, checked at the saw.
- [ ] The loaded lumber ticks off against `order_list.csv` (framing) — the sheet, not memory.
