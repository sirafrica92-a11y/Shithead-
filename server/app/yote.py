"""Yoté: West African two-player tactical game (5x6, 12 stones each).

A turn either places a reserve stone or moves one stone orthogonally to a
vacant adjacent square. Captures jump an adjacent opponent to the next empty
square in the same direction, remove the jumped stone, and permit removing
one additional opposing stone. Captures don't chain automatically. The last
player with stones or legal turns wins. This variant is kept isolated.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, replace
from typing import Any

ROWS,COLS,N,RESERVE=5,6,30,12
class IllegalYoteMove(ValueError):pass

@dataclass(frozen=True)
class YoteMatch:
    cells:tuple[int,...]=(0,)*N
    reserves:tuple[int,int]=(RESERVE,RESERVE)
    actor:int=0
    pending_bonus:bool=False
    winner:int|None=None
    finished:bool=False
    turn_number:int=0
    event:str=""
    history:tuple[str,...]=()

def make_yote_match()->YoteMatch:
    return YoteMatch(event="Place a stone or move one already on the board.")

def _step(i,dr,dc):
    r,c=divmod(i,COLS);r+=dr;c+=dc
    return r*COLS+c if 0<=r<ROWS and 0<=c<COLS else None

def legal_yote_moves(m:YoteMatch,seat:int)->dict[str,Any]:
    empty={"places":[],"steps":[],"jumps":[],"bonuses":[]}
    if m.finished or type(seat) is not int or m.actor!=seat:return empty
    enemy=2-seat
    if m.pending_bonus:
        empty["bonuses"]=[i for i,x in enumerate(m.cells) if x==enemy]
        return empty
    if m.reserves[seat]:
        empty["places"]=[i for i,x in enumerate(m.cells) if x==0]
    for i,x in enumerate(m.cells):
        if x!=seat+1:continue
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            mid=_step(i,dr,dc)
            if mid is None:continue
            if m.cells[mid]==0:empty["steps"].append([i,mid])
            elif m.cells[mid]==enemy:
                end=_step(mid,dr,dc)
                if end is not None and m.cells[end]==0:
                    empty["jumps"].append([i,end,mid])
    return empty

def _signature(m):
    return "".join(str(x) for x in m.cells)+":"+str(m.actor)+":"+str(m.reserves)

def _settle(m:YoteMatch)->YoteMatch:
    if m.pending_bonus:return m
    own=m.cells.count(m.actor+1)+m.reserves[m.actor]
    other=1-m.actor
    if own==0:return replace(m,finished=True,winner=other,event="Player "+str(other+1)+" wins.")
    legal=legal_yote_moves(m,m.actor)
    if not (legal["places"] or legal["steps"] or legal["jumps"]):
        return replace(m,finished=True,winner=other,event="Opponent cannot move; Player "+str(other+1)+" wins.")
    sig=_signature(m);hist=m.history+(sig,)
    if hist.count(sig)>=3:return replace(m,finished=True,winner=None,event="Repeated position: draw.",history=hist)
    return replace(m,history=hist)

def apply_yote_action(m:YoteMatch,seat:int,kind:str,*,index:object=None,source:object=None,destination:object=None)->YoteMatch:
    if type(seat) is not int or m.actor!=seat or m.finished:raise IllegalYoteMove("Not your turn")
    legal=legal_yote_moves(m,seat)
    c=list(m.cells);res=list(m.reserves)
    if kind=="place" and type(index) is int and index in legal["places"]:
        c[index]=seat+1;res[seat]-=1
        return _settle(replace(m,cells=tuple(c),reserves=tuple(res),actor=1-seat,turn_number=m.turn_number+1,event=f"Player {seat+1} placed a stone."))
    if kind=="move" and type(source) is int and type(destination) is int and [source,destination] in legal["steps"]:
        c[source]=0;c[destination]=seat+1
        return _settle(replace(m,cells=tuple(c),actor=1-seat,turn_number=m.turn_number+1,event=f"Player {seat+1} moved."))
    if kind=="jump" and type(source) is int and type(destination) is int:
        matching=[move for move in legal["jumps"] if move[:2]==[source,destination]]
        if matching:
            mid=matching[0][2];c[source]=0;c[mid]=0;c[destination]=seat+1
            bonus=any(v==2-seat for v in c)
            result=replace(m,cells=tuple(c),pending_bonus=bonus,actor=seat if bonus else 1-seat,
                           turn_number=m.turn_number+1,event=f"Player {seat+1} jumped and captured. Choose a bonus capture." if bonus else "Jump captured the final enemy piece.")
            return result if bonus else _settle(result)
    if kind=="bonus" and type(index) is int and index in legal["bonuses"]:
        c[index]=0
        return _settle(replace(m,cells=tuple(c),pending_bonus=False,actor=1-seat,
                               turn_number=m.turn_number+1,event=f"Player {seat+1} removed a bonus piece."))
    raise IllegalYoteMove("Select a legal Yoté action")

def assert_yote_invariants(m:YoteMatch)->None:
    if (len(m.cells)!=N or any(type(v) is not int or v not in (0,1,2) for v in m.cells)
        or len(m.reserves)!=2 or any(type(n) is not int or not 0<=n<=RESERVE for n in m.reserves)
        or any(m.cells.count(i+1)+m.reserves[i]>RESERVE for i in (0,1))
        or type(m.actor) is not int or m.actor not in (0,1)
        or m.winner not in (0,1,None) or (m.winner is not None and not m.finished)):
        raise ValueError("Invalid Yoté state")

def public_yote_view(m:YoteMatch)->dict[str,Any]:
    return {"game_type":"yote","phase":"FINISHED" if m.finished else "PLAYING","cells":list(m.cells),
            "reserves":list(m.reserves),"actor":m.actor,"pending_bonus":m.pending_bonus,
            "winner":m.winner,"turn_number":m.turn_number,"event":m.event}

def private_yote_view(m:YoteMatch,seat:int)->dict[str,Any]:
    v=public_yote_view(m);v["legal"]=legal_yote_moves(m,seat);return v

def dump_yote(m:YoteMatch)->dict[str,Any]:return asdict(m)
def restore_yote(d:dict[str,Any])->YoteMatch:
    m=YoteMatch(cells=tuple(d["cells"]),reserves=tuple(d["reserves"]),actor=d["actor"],
       pending_bonus=d.get("pending_bonus",False),winner=d.get("winner"),finished=d.get("finished",False),
       turn_number=d.get("turn_number",0),event=d.get("event",""),history=tuple(d.get("history",[])))
    assert_yote_invariants(m);return m
