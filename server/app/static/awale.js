"use strict";
/* Awalé UI, independent of card and dice renderers. Server decides moves. */
function sendAwale(pit) {
  if (!snap || !ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({
    type:"awale",kind:"sow",pit,expected_version:snap.version,
    request_id:crypto.randomUUID()
  }));
}
function renderAwale(g) {
  el("awale-room").textContent=snap.room_id;
  const done=g.phase==="FINISHED";
  const mine=g.actor===seatIndex && !g.is_spectator && !done;
  const winner=g.winner;
  el("awale-turn").textContent=done
    ?winner===null?"Awalé ends in a draw":
      (snap.players[winner]?.name||"Player")+" wins Awalé!"
    :g.is_spectator?"Waiting for the next round":
     mine?"Your turn — choose a house":
     (snap.players[g.actor]?.name||"Player")+"'s turn";
  el("awale-score").textContent=
    (snap.players[0]?.name||"Player 1")+": "+g.captured[0]+
    " captured  ·  "+(snap.players[1]?.name||"Player 2")+": "+g.captured[1]+" captured";
  el("awale-event").textContent=done && winner!==null
    ?(snap.players[winner]?.name||"Winner")+" won with "+g.captured[winner]+" captured seeds ("+g.captured.join("–")+")."
    :namedGameEvent(g.event);
  el("awale-board").replaceChildren();
  const legal=g.your_legal_pits||[];
  for (const row of [[11,10,9,8,7,6],[0,1,2,3,4,5]]) {
    const boardRow=document.createElement("div");boardRow.className="awale-row";
    for(const index of row){
      const btn=document.createElement("button");
      btn.className="awale-house"+(legal.includes(index)?" legal":"")+
        (g.last_pit===index?" last":"");
      btn.type="button";btn.disabled=!legal.includes(index);
      btn.setAttribute("aria-label","House "+(index+1)+": "+g.pits[index]+" seeds");
      btn.title="House "+(index+1);
      const grains=document.createElement("span");grains.className="awale-seeds";
      const count=Math.min(g.pits[index],12);
      for(let i=0;i<count;i++){
        const grain=document.createElement("span");
        grain.className="awale-grain";
        grains.appendChild(grain);
      }
      const label=document.createElement("strong");label.textContent=String(g.pits[index]);
      btn.append(grains,label);
      if(legal.includes(index))btn.onclick=()=>sendAwale(index);
      boardRow.appendChild(btn);
    }
    el("awale-board").appendChild(boardRow);
  }
  el("awale-rematch").classList.toggle("hidden",!done);
  el("awale-rematch").disabled=(snap.rematch_votes||[]).includes(seatIndex);
  el("awale-rematch").textContent=el("awale-rematch").disabled
    ?"Waiting for rematch votes":"Play again in this room";
  el("awale-switch").classList.toggle("hidden",!(done&&seatIndex===snap.host_seat));
  el("awale-reactions").classList.toggle("hidden",done);
  el("awale-reactions").replaceChildren(...REACTIONS.map(emoji=>{
    const b=document.createElement("button");b.type="button";b.textContent=emoji;
    b.onclick=()=>sendRoomAction("reaction",{emoji});return b;
  }));
  const pending=snap.pending_joiners||[];
  el("awale-join-prompt").classList.toggle("hidden",
    !(seatIndex===snap.host_seat&&pending.length&&!done));
  el("awale-join-names").textContent=pending.map(i=>snap.players[i]?.name||"Friend").join(", ");
}
el("awale-refresh").onclick=refreshGame;
el("awale-open-rules").onclick=openRules;
el("awale-rules-back").onclick=()=>show(screenBeforeRules);
el("awale-rematch").onclick=()=>sendRoomAction("rematch");
el("awale-switch").onclick=()=>sendRoomAction("return_lobby");
el("awale-home").onclick=()=>el("main-menu").click();
el("awale-restart").onclick=()=>sendRoomAction("host_join_decision",{decision:"restart_now"});
el("awale-finish").onclick=()=>sendRoomAction("host_join_decision",{decision:"finish_current"});
