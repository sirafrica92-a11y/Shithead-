"""Independent two-player Dara (5x6, twelve pieces each) rules engine.

Chosen documented variant: no triples during placement; orthogonal one-step
movement to a free square; new exact triple captures one opponent piece;
a four/five line is illegal; protected opponent triples are only removable if
there is no unprotected piece; immobilisation or fewer than three pieces loses.
Threefold identical positions in movement phase are declared drawn.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

ROWS, COLS, CELLS = 5, 6, 30
STONES = 12


class IllegalDaraMove(ValueError):
    pass


@dataclass(frozen=True)
class DaraMatch:
    cells: tuple[int, ...] = (0,) * CELLS
    placed: tuple[int, int] = (0, 0)
    phase: str = "PLACE"
    actor: int = 0
    winner: int | None = None
    finished: bool = False
    pending_capture: bool = False
    turn_number: int = 0
    event: str = ""
    history: tuple[str, ...] = ()


def make_dara_match() -> DaraMatch:
    return DaraMatch(event="Place a piece on an empty square.")


def _lines(cells: tuple[int, ...], seat: int, size: int) -> set[tuple[int, ...]]:
    found = set()
    for r in range(ROWS):
        for c in range(COLS - size + 1):
            line = tuple(r * COLS + c + k for k in range(size))
            if all(cells[i] == seat + 1 for i in line):
                found.add(line)
    for c in range(COLS):
        for r in range(ROWS - size + 1):
            line = tuple((r+k) * COLS+c for k in range(size))
            if all(cells[i] == seat + 1 for i in line):
                found.add(line)
    return found


def _neighbours(i: int) -> tuple[int, ...]:
    r,c=divmod(i,COLS)
    return tuple(nr*COLS+nc for nr,nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))
                 if 0 <= nr < ROWS and 0 <= nc < COLS)


def _moves(match: DaraMatch, seat: int) -> tuple[tuple[int, int], ...]:
    return tuple((i,j) for i,v in enumerate(match.cells) if v == seat+1
                 for j in _neighbours(i) if match.cells[j] == 0
                 and _move_is_valid(match.cells, seat, i, j))


def _move_is_valid(cells: tuple[int, ...], seat: int, src: int, dst: int) -> bool:
    next_cells=list(cells);next_cells[dst]=seat+1;next_cells[src]=0
    return not _lines(tuple(next_cells), seat, 4)


def _capturable(match: DaraMatch, seat: int) -> tuple[int,...]:
    targets=[i for i,v in enumerate(match.cells) if v == 2-seat]
    protected={i for line in _lines(match.cells,1-seat,3) for i in line}
    exposed=[i for i in targets if i not in protected]
    return tuple(exposed if exposed else targets)


def legal_dara_moves(match: DaraMatch, seat: int) -> dict[str, Any]:
    if match.finished or type(seat) is not int or seat != match.actor:
        return {"places":[],"moves":[],"captures":[]}
    if match.pending_capture:
        return {"places":[],"moves":[],"captures":list(_capturable(match,seat))}
    if match.phase == "PLACE":
        places=[]
        if match.placed[seat] < STONES:
            for i,v in enumerate(match.cells):
                if v: continue
                c=list(match.cells);c[i]=seat+1
                if not _lines(tuple(c),seat,3):
                    places.append(i)
        return {"places":places,"moves":[],"captures":[]}
    return {"places":[],"moves":[list(m) for m in _moves(match,seat)],"captures":[]}


def _sig(m: DaraMatch) -> str:
    return "".join(str(x) for x in m.cells)+":"+str(m.actor)


def _finish_if_needed(m: DaraMatch) -> DaraMatch:
    if m.pending_capture or m.phase != "MOVE":return m
    total=[m.cells.count(1),m.cells.count(2)]
    if min(total) < 3:
        loser = 0 if total[0]<3 else 1
        return replace(m,finished=True,winner=1-loser,event=f"Player {2-loser} wins: opponent below three pieces.")
    if not _moves(m,m.actor):
        return replace(m,finished=True,winner=1-m.actor,event=f"Player {2-m.actor} wins: opponent cannot move.")
    signature=_sig(m)
    hist=m.history+(signature,)
    if hist.count(signature)>=3:
        return replace(m,finished=True,winner=None,history=hist,event="Threefold repetition: draw.")
    return replace(m,history=hist)


def _advance_placement(match: DaraMatch) -> DaraMatch:
    """Avoid a placement-phase deadlock when a no-three rule blocks all squares.

    Skip only a seat without a legal placement. If both are blocked, draw.
    Never invent extra stones or permit three-in-a-row placements.
    """
    if match.phase != "PLACE":
        return _finish_if_needed(match)
    if legal_dara_moves(match,match.actor)["places"]:
        return match
    other=1-match.actor
    if legal_dara_moves(replace(match,actor=other),other)["places"]:
        return replace(match,actor=other,event=match.event+" Opponent has no legal placement and passes.")
    return replace(match,finished=True,winner=None,
                   event=match.event+" No legal placement remains: drawn game.")


def apply_dara_action(match: DaraMatch, seat: int, kind: str, *, index: object=None,
                      source: object=None, destination: object=None) -> DaraMatch:
    legal=legal_dara_moves(match,seat)
    if match.finished or seat != match.actor or type(seat) is not int:
        raise IllegalDaraMove("It is not your turn or Dara has finished")
    if kind=="place":
        if type(index) is not int or index not in legal["places"]:
            raise IllegalDaraMove("Choose an empty legal square; triples cannot form during placement")
        c=list(match.cells);c[index]=seat+1
        p=list(match.placed);p[seat]+=1
        placing=p[0]<STONES or p[1]<STONES
        result=replace(match,cells=tuple(c),placed=tuple(p),
                       phase="PLACE" if placing else "MOVE",actor=1-seat,
                       turn_number=match.turn_number+1,
                       event=f"Player {seat+1} placed a piece.")
        return _advance_placement(result)
    if kind=="move":
        if (type(source) is not int or type(destination) is not int or
            [source,destination] not in legal["moves"]):
            raise IllegalDaraMove("Move one piece to an adjacent legal square")
        before=_lines(match.cells,seat,3)
        c=list(match.cells);c[destination]=seat+1;c[source]=0
        new_lines=_lines(tuple(c),seat,3)-before
        capture=bool(new_lines)
        result=replace(match,cells=tuple(c),pending_capture=capture,
                       actor=seat if capture else 1-seat,
                       turn_number=match.turn_number+1,
                       event=f"Player {seat+1} formed a three: capture a piece." if capture
                             else f"Player {seat+1} moved.")
        return result if capture else _finish_if_needed(result)
    if kind=="capture":
        if type(index) is not int or index not in legal["captures"]:
            raise IllegalDaraMove("Choose an opposing unprotected piece")
        c=list(match.cells);c[index]=0
        result=replace(match,cells=tuple(c),pending_capture=False,actor=1-seat,
                       turn_number=match.turn_number+1,
                       event=f"Player {seat+1} captured a piece.")
        return _finish_if_needed(result)
    raise IllegalDaraMove("Unknown Dara action")


def assert_dara_invariants(m: DaraMatch) -> None:
    if (len(m.cells)!=CELLS or any(type(v) is not int or v not in (0,1,2) for v in m.cells)
        or len(m.placed)!=2 or any(type(v) is not int or not 0<=v<=STONES for v in m.placed)
        or m.cells.count(1)>m.placed[0] or m.cells.count(2)>m.placed[1]
        or m.phase not in ("PLACE","MOVE") or m.actor not in (0,1)
        or m.winner not in (0,1,None) or (m.winner is not None and not m.finished)
        or (m.phase=="MOVE" and m.placed!=(STONES,STONES))):
        raise ValueError("Invalid Dara match")


def public_dara_view(m: DaraMatch) -> dict[str,Any]:
    return {"game_type":"dara","phase":"FINISHED" if m.finished else "PLAYING",
            "stage":m.phase,"cells":list(m.cells),"placed":list(m.placed),
            "actor":m.actor,"winner":m.winner,"pending_capture":m.pending_capture,
            "turn_number":m.turn_number,"event":m.event}


def private_dara_view(m: DaraMatch,seat: int)->dict[str,Any]:
    out=public_dara_view(m);out["legal"]=legal_dara_moves(m,seat);return out


def dump_dara(m: DaraMatch)->dict[str,Any]:
    return asdict(m)


def restore_dara(data:dict[str,Any])->DaraMatch:
    m=DaraMatch(cells=tuple(data["cells"]),placed=tuple(data["placed"]),
       phase=data["phase"],actor=data["actor"],winner=data.get("winner"),
       finished=data.get("finished",False),pending_capture=data.get("pending_capture",False),
       turn_number=data.get("turn_number",0),event=data.get("event",""),
       history=tuple(data.get("history",[])))
    assert_dara_invariants(m)
    return m
