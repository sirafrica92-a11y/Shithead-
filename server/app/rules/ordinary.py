"""W3 — ordinary turns and finish logic for custom Shithead (foundation rules v0.1).

Scope (frozen 2026-05-10; owner rulings 2026-05-14):
- Rank order 3(low)..A(high); normal play must be >= effective top rank; same-rank multiples.
- 7 imposes seven-lock (next ordinary play <= 7); 10 clears pile + lock, same actor again;
  2 clears the comparison (next play free) AND cancels the lock; pickup clears the lock.
- Four-of-a-kind: four consecutive pile cards of the same rank clear the pile; contributors
  may differ; same-rank groups count; 2s count toward the streak. No same-actor bonus.
- Refill to 3 after the full action resolves, only while the deck is non-empty.
- Zone order hand -> face-up -> face-down (strict); face-down flips are blind; on flip
  failure the flipper picks up pile + flipped card.
- Finished players leave rotation; the game continues until exactly one player remains.

Out of scope: pile-pass powers (W2), attack/stack/chains (W2/worlds.py), dealing,
turn-loop orchestration (W4), "Shit Face" overlay.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List, Optional, Sequence, Tuple

from app.game.deck import Card, JOKER
from app.rules.pile_pass import has_power
from app.rules.turns import Rank, compare_ranks


TOP_ZONE = "hand"
MIDDLE_ZONE = "face_up"
BOTTOM_ZONE = "face_down"

_ZONE_ORDER = (TOP_ZONE, MIDDLE_ZONE, BOTTOM_ZONE)
_RANK_INDEX = {rank: i for i, rank in enumerate(Rank.play_order())}


def rank_index(rank: Rank) -> int:
    return _RANK_INDEX[rank]


def _rank_leq(a: Rank, b: Rank) -> bool:
    return rank_index(a) <= rank_index(b)


def effective_top_rank(pile: Sequence[Card]) -> Optional[Rank]:
    """Rank the next ordinary play must meet/beat. None = free play."""
    for card in reversed(pile):
        if card.rank is Rank.TWO:
            return None
        return card.rank
    return None


def four_of_a_kind_streak(pile: Sequence[Card]) -> bool:
    """True iff the pile ends with >=4 consecutive same-rank cards."""
    if len(pile) < 4:
        return False
    last4 = pile[-4:]
    rank = last4[0].rank
    return all(c.rank is rank for c in last4)


def current_zone(player: "PlayerState") -> str:
    if player.hand:
        return TOP_ZONE
    if player.face_up:
        return MIDDLE_ZONE
    return BOTTOM_ZONE


def zone_cards(player: "PlayerState", zone: str) -> Tuple[Card, ...]:
    if zone == TOP_ZONE:
        return player.hand
    if zone == MIDDLE_ZONE:
        return player.face_up
    return player.face_down


def _clear_zone(state: "GameState", player: "PlayerState", zone: str) -> None:
    if zone == TOP_ZONE:
        player.hand = []
    elif zone == MIDDLE_ZONE:
        player.face_up = []
    else:
        player.face_down = []
        if player.id in state.face_down_flips:
            del state.face_down_flips[player.id]


def is_finished(player: "PlayerState") -> bool:
    return not (player.hand or player.face_up or player.face_down)


@dataclass
class PlayerState:
    id: int
    hand: List[Card]
    face_up: List[Card]
    face_down: List[Card]


@dataclass
class GameState:
    players: List[PlayerState]
    deck: List[Card]
    pile: List[Card]
    current_player_index: int
    direction: int = 1
    seven_lock: bool = False
    finished_player_ids: Tuple[int, ...] = ()
    face_down_flips: dict = None

    def __post_init__(self) -> None:
        if self.face_down_flips is None:
            self.face_down_flips = {}


def _replace_player(state: GameState, player: PlayerState) -> None:
    state.players = [player if p.id == player.id else p for p in state.players]


def _player_by_id(state: GameState, player_id: int) -> PlayerState:
    for p in state.players:
        if p.id == player_id:
            return p
    raise KeyError(f"unknown player id: {player_id}")


def _remaining_count(state: GameState) -> int:
    return len(state.players) - len(state.finished_player_ids)


def _next_unfinished(state: GameState, index: int) -> int:
    n = len(state.players)
    for step in range(1, n + 1):
        nxt = (index + step * state.direction) % n
        if state.players[nxt].id not in state.finished_player_ids:
            return nxt
    raise RuntimeError("no unfinished player found")


def _finish_turn(state: GameState, player: PlayerState) -> None:
    _replace_player(state, player)
    if is_finished(player):
        if player.id not in state.finished_player_ids:
            state.finished_player_ids = state.finished_player_ids + (player.id,)
        if _remaining_count(state) == 1:
            loser = next(
                p for p in state.players if p.id not in state.finished_player_ids
            )
            state.current_player_index = state.players.index(loser)
            return
    state.current_player_index = _next_unfinished(
        state, state.players.index(player)
    )


def _resolve_successful_play(state: GameState, player: PlayerState) -> None:
    played_rank = state.pile[-1].rank
    if played_rank is Rank.SEVEN:
        state.seven_lock = True
    elif played_rank is not Rank.TEN:
        state.seven_lock = False

    if played_rank is Rank.TEN or four_of_a_kind_streak(state.pile):
        state.pile = []
        state.seven_lock = False
        if is_finished(player):
            _finish_turn(state, player)
        else:
            _replace_player(state, player)
        return

    _finish_turn(state, player)


def _refill_hand(state: GameState, player: PlayerState) -> None:
    if current_zone(player) is not TOP_ZONE:
        return
    while len(player.hand) < 3 and state.deck:
        player.hand.append(state.deck.pop(0))


def _apply_play_cards(state: GameState, player_id: int, card_ids: Sequence[str]) -> GameState:
    player = _player_by_id(state, player_id)
    if player.id != state.players[state.current_player_index].id:
        raise ValueError("not this player's turn")
    zone = current_zone(player)
    if zone is BOTTOM_ZONE:
        raise ValueError("face-down cards must be played via play_face_down")
    available = zone_cards(player, zone)
    by_id = {c.id: c for c in available}
    try:
        chosen = [by_id[i] for i in card_ids]
    except KeyError as exc:
        raise ValueError(f"card not in current zone: {exc}") from exc
    if not chosen:
        raise ValueError("must play at least one card")
    if any(has_power(c) for c in chosen):
        raise ValueError("power cards (3/Joker) are pile-pass cards, not ordinary plays")
    first_rank = chosen[0].rank
    if any(c.rank is not first_rank for c in chosen):
        raise ValueError("an ordinary play must be a single rank (1-4 cards)")

    top = effective_top_rank(state.pile)
    if state.seven_lock:
        if top is None or not _rank_leq(first_rank, Rank.SEVEN):
            raise ValueError(
                "seven-lock: next ordinary play must be rank <= 7 (or a 2/10)"
            )
    elif top is not None and compare_ranks(first_rank, top) < 0:
        raise ValueError(f"rank {first_rank.value} is below effective top {top.value}")

    _clear_zone(state, player, zone)
    remaining = [c for c in available if c.id not in {ch.id for ch in chosen}]
    if zone is TOP_ZONE:
        player.hand = remaining
    else:
        player.face_up = remaining
    state.pile = state.pile + list(chosen)
    _refill_hand(state, player)
    _resolve_successful_play(state, player)
    return state


def _apply_play_face_down(state: GameState, player_id: int) -> GameState:
    player = _player_by_id(state, player_id)
    if player.id != state.players[state.current_player_index].id:
        raise ValueError("not this player's turn")
    if current_zone(player) is not BOTTOM_ZONE:
        raise ValueError("play_face_down only when hand and face-up are empty")
    if not player.face_down:
        raise ValueError("no face-down cards remain")

    card = player.face_down.pop(0)
    if player.id in state.face_down_flips:
        del state.face_down_flips[player.id]

    top = effective_top_rank(state.pile)
    if has_power(card):
        raise ValueError(
            "face-down flip revealed a power card (3/Joker): OPEN at W3 - "
            "pile-pass power handling on blind flips is unresolved"
        )
    ok = False
    if state.seven_lock:
        ok = top is not None and _rank_leq(card.rank, Rank.SEVEN)
    elif top is None:
        ok = True
    else:
        ok = compare_ranks(card.rank, top) >= 0

    state.pile = state.pile + [card]
    if ok:
        _resolve_successful_play(state, player)
    else:
        player = replace(player, hand=player.hand + state.pile)
        state.pile = []
        state.seven_lock = False
        _finish_turn(state, player)
    return state


def _apply_pick_up(state: GameState, player_id: int) -> GameState:
    player = _player_by_id(state, player_id)
    if player.id != state.players[state.current_player_index].id:
        raise ValueError("not this player's turn")
    if current_zone(player) is not TOP_ZONE:
        raise ValueError("cannot pick up while in face-up/face-down zones")
    player = replace(player, hand=player.hand + state.pile)
    state.pile = []
    state.seven_lock = False
    _finish_turn(state, player)
    return state


def apply_action(state: GameState, player_id: int, action: str,
                 card_ids: Sequence[str] = ()) -> GameState:
    """Dispatch an ordinary-turn action. `action` is play_cards | play_face_down | pick_up."""
    if action == "play_cards":
        return _apply_play_cards(state, player_id, card_ids)
    if action == "play_face_down":
        return _apply_play_face_down(state, player_id)
    if action == "pick_up":
        return _apply_pick_up(state, player_id)
    raise ValueError(f"unknown action: {action!r}")


def can_apply(state: GameState, player_id: int, action: str,
              card_ids: Sequence[str] = ()) -> bool:
    """Non-mutating legality check for UI/hints: same rules, no state change."""
    probe = GameState(
        players=[PlayerState(p.id, list(p.hand), list(p.face_up), list(p.face_down))
                 for p in state.players],
        deck=list(state.deck),
        pile=list(state.pile),
        current_player_index=state.current_player_index,
        direction=state.direction,
        seven_lock=state.seven_lock,
        finished_player_ids=tuple(state.finished_player_ids),
        face_down_flips=dict(state.face_down_flips),
    )
    try:
        apply_action(probe, player_id, action, card_ids)
    except _IllegalActionError:
        return False
    return True


class _IllegalActionError(ValueError):
    """Internal marker so can_apply only swallows legality errors."""
