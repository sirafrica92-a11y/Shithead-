"""D-024 — optional, newly drawn matching rank after ordinary play."""
from dataclasses import replace
import pytest

from server.app.gameplay import Match, apply_match_action, private_match_view, assert_card_conservation, make_match
from server.app.rules.ordinary import Card, OrdinaryState, PlayerState, IllegalPlay
from server.app.persistence import dump_match, restore_match


def C(rank, uid):
    return Card(rank, "S", uid)


def match_for(hand, stock, *, pile=(), players=2, direction=1):
    seats = (PlayerState(hand=tuple(hand)),) + tuple(
        PlayerState(hand=(C(8, f"opp{i}"),)) for i in range(1, players)
    )
    return Match(OrdinaryState(players=seats, deck=tuple(stock),
                               pile=tuple(pile), direction=direction))


def test_new_jack_offers_choice_and_keep_preserves_it():
    original = match_for([C(11,"oldJ"), C(9,"nine"), C(8,"eight")], [C(11,"newJ")])
    after = apply_match_action(original, 0, "play", indices=[0])
    assert after.state.current == 0
    assert after.refill_choice.actor == 0
    assert after.refill_choice.eligible_indices == (2,)
    assert after.refill_choice.next_actor == 1
    assert private_match_view(after,0)["your_refill_indices"] == [2]
    assert private_match_view(after,1)["your_refill_indices"] == []
    assert original.refill_choice is None
    kept = apply_match_action(after,0,"keep_drawn")
    assert kept.state.current == 1
    assert kept.refill_choice is None
    assert [c.id for c in kept.state.players[0].hand] == ["nine","eight","newJ"]
    assert [c.id for c in kept.state.pile] == ["oldJ"]


def test_optional_matching_jack_play_keeps_original_turn_order():
    after = apply_match_action(
        match_for([C(11,"oldJ"),C(9,"nine"),C(8,"eight")],[C(11,"newJ")]),
        0,"play",indices=[0])
    result = apply_match_action(after,0,"play_drawn",indices=[2])
    assert result.refill_choice is None
    assert result.state.current == 1
    assert [c.id for c in result.state.pile] == ["oldJ","newJ"]
    assert [c.id for c in result.state.players[0].hand] == ["nine","eight"]


def test_already_held_matching_cards_cannot_join_and_invalid_choice_is_atomic():
    after = apply_match_action(
        match_for([C(11,"oldJ"),C(11,"heldJ"),C(8,"eight")],[C(11,"newJ")]),
        0,"play",indices=[0])
    for kind, indices in (("play_drawn",[0]),("play_drawn",[1]),("pickup",None),("power",None)):
        with pytest.raises(IllegalPlay):
            apply_match_action(after,0,kind,indices=indices)
        assert after.refill_choice is not None


def test_drawn_card_does_not_trigger_a_choice_if_rank_differs():
    result = apply_match_action(
        match_for([C(11,"oldJ"),C(9,"nine"),C(8,"eight")],[C(12,"queen")]),
        0,"play",indices=[0])
    assert result.refill_choice is None
    assert result.state.current == 1


def test_drawn_matching_seven_can_be_kept_or_played_and_relocks():
    result = apply_match_action(
        match_for([C(7,"old7"),C(9,"nine"),C(8,"eight")],[C(7,"new7")]),
        0,"play",indices=[0])
    assert result.refill_choice is not None and result.state.locked
    continued = apply_match_action(result,0,"play_drawn",indices=[2])
    assert continued.state.locked
    assert continued.refill_choice is None and continued.state.current == 1


@pytest.mark.parametrize("seats",range(2,7))
@pytest.mark.parametrize("direction",[-1,1])
def test_turn_anchor_preserved_for_all_player_counts(seats,direction):
    result = apply_match_action(
        match_for([C(11,"oldJ"),C(9,"nine"),C(8,"eight")],
                  [C(11,"newJ")],players=seats,direction=direction),
        0,"play",indices=[0])
    kept = apply_match_action(result,0,"keep_drawn")
    assert kept.state.current == direction % seats


def test_choice_survives_persistence_and_finishes_same_way():
    result = apply_match_action(
        match_for([C(11,"oldJ"),C(9,"nine"),C(8,"eight")],[C(11,"newJ")]),
        0,"play",indices=[0])
    recovered = restore_match(dump_match(result))
    assert recovered.refill_choice == result.refill_choice
    assert apply_match_action(recovered,0,"keep_drawn").state.current == 1


def test_matching_draw_cannot_continue_after_four_of_kind_clear():
    result = apply_match_action(
        match_for([C(11,"fourth"),C(9,"nine"),C(8,"eight")],
                  [C(11,"newJ")],pile=[C(11,"one"),C(11,"two"),C(11,"three")]),
        0,"play",indices=[0])
    assert result.state.pile == () and result.refill_choice is None
    assert result.state.current == 0


def test_matching_draw_after_multi_card_group_is_optional():
    result = apply_match_action(
        match_for([C(11,"first"),C(11,"second"),C(8,"eight")],
                  [C(11,"newJ1"),C(11,"newJ2")]),
        0,"play",indices=[0,1])
    assert result.refill_choice.eligible_indices == (1,2)
    continued = apply_match_action(result,0,"play_drawn",indices=[1])
    assert continued.refill_choice is not None
    assert continued.refill_choice.eligible_indices == (1,)
    kept = apply_match_action(continued,0,"keep_drawn")
    assert kept.state.current == 1


def test_drawn_option_only_after_stock_refill_not_faceup_absorption():
    first=PlayerState(hand=(C(11,"oldJ"),C(8,"eight")),face_up=(C(11,"upJ"),))
    st=OrdinaryState(players=(first,PlayerState(hand=(C(9,"other"),))),deck=())
    result=apply_match_action(Match(st),0,"play",indices=[0])
    assert result.refill_choice is None
