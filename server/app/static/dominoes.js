"use strict";
/* Jamaican partner dominoes. Server owns rules, shuffled hands and scoring. */
function dominoAction(kind, fields={}) {
  if (!snap || !ws || ws.readyState!==WebSocket.OPEN) return;
  ws.send(JSON.stringify({type:"dominoes",kind,...fields,
    expected_version:snap.version, request_id:crypto.randomUUID()}));
}
function boneEl(tile) {
  const b=document.createElement("span"); b.className="domino-bone";
  for (const n of tile) {
    const half=document.createElement("span");half.className="domino-half";
    half.textContent=String(n);half.setAttribute("aria-label",n+" pips");b.appendChild(half);
  }
  return b;
}
function renderDominoes(g) {
  el("domino-room").textContent=snap.room_id;
  const done=g.phase==="FINISHED",handover=g.stage==="HAND_OVER";
  const mine=seatIndex===g.actor&&!done&&!handover&&!g.is_spectator;
  const names=snap.players||[];
  const cutthroat=g.mode==="cutthroat";
  el("domino-mode-label").textContent=cutthroat?"Cut Throat · free-for-all":"Partner · 2 vs 2";
  const teamNames=[0,1].map(t=>(names[t]?.name||"Seat "+(t+1))+" & "+(names[t+2]?.name||"Seat "+(t+3)));
  el("domino-score").textContent=cutthroat
    ?g.scores.map((s,i)=>(names[i]?.name||"Player "+(i+1))+": "+s).join(" · ")+" (first to 6)"
    :teamNames[0]+": "+g.scores[0]+"  •  "+teamNames[1]+": "+g.scores[1]+" (Six Love: reach 6 points in an uninterrupted run; opponent wins reset the run)";
  el("domino-turn").textContent=done
    ?(cutthroat?(names[g.winner_player]?.name||"Player")+" wins Cut Throat!":teamNames[g.winner_team]+" wins Six Love!")
    :handover?"Hand finished — "+g.event
    :mine?"Your turn — play a matching tile or pass when blocked"
    :(names[g.actor]?.name||"Player")+" to play";
  el("domino-event").textContent=namedGameEvent(g.event);
  el("domino-hand-counts").replaceChildren(...g.hand_counts.map((count,i)=>{
    const label=document.createElement("div");label.className="domino-player";
    label.textContent=(names[i]?.name||"Seat "+(i+1))+(i===seatIndex?" (you)":"")+(cutthroat?"":" · Team "+((i%2)+1))+" · "+count+" "+(count===1?"tile":"tiles");
    return label;
  }));
  const chain=el("domino-chain");chain.replaceChildren(...g.chain.map(boneEl));
  if(!g.chain.length){chain.textContent="Double-six starts the table"; }
  const [left,right]=g.ends;
  el("domino-ends").textContent=g.chain.length?"Open ends: "+left+" and "+right:"Waiting for opening tile";
  const hand=el("domino-hand");hand.replaceChildren();
  const myHand=g.hand||[];
  el("domino-hand-total").textContent="("+myHand.length+" "+(myHand.length===1?"tile":"tiles")+" remaining)";
  const plays=new Map((g.legal?.plays||[]).map(x=>[x.index,x.sides]));
  myHand.forEach((tile,i)=>{
    const wrapper=document.createElement("div");wrapper.className="domino-choice";
    wrapper.append(boneEl(tile));
    const sides=plays.get(i)||[];
    if(sides.length){
      for(const side of sides){
        const btn=document.createElement("button");
        btn.type="button";btn.className="btn btn-primary domino-play";
        btn.textContent=g.chain.length?(side==="left"?"Play left":"Play right"):"Play";
        btn.setAttribute("aria-label","Play "+tile.join("-")+" "+side);
        btn.onclick=()=>dominoAction("play",{index:i,side});
        wrapper.appendChild(btn);
      }
    }
    hand.appendChild(wrapper);
  });
  el("domino-pass").classList.toggle("hidden",!(g.legal?.pass));
  el("domino-next").classList.toggle("hidden",!(g.legal?.next_hand));
  el("domino-next").textContent=g.next_pose_team===null?"Deal again (double-six opens)":"Deal again — pose for Team "+(g.next_pose_team+1);
  el("domino-rematch").classList.toggle("hidden",!done);
  el("domino-rematch").textContent=cutthroat?"Play Cut Throat again":"Play Six Love again";
  el("domino-rematch").disabled=(snap.rematch_votes||[]).includes(seatIndex);
  el("domino-switch").classList.toggle("hidden",!(done&&seatIndex===snap.host_seat));
  el("domino-reactions").replaceChildren(...REACTIONS.map(emoji=>{
    const b=document.createElement("button");b.type="button";b.textContent=emoji;
    b.onclick=()=>sendRoomAction("reaction",{emoji});return b;
  }));
  const pending=snap.pending_joiners||[];
  el("domino-join-prompt").classList.toggle("hidden",!(seatIndex===snap.host_seat&&pending.length&&!done));
  el("domino-join-names").textContent=pending.map(i=>names[i]?.name||"Friend").join(", ");
}
el("domino-pass").onclick=()=>dominoAction("pass");
el("domino-next").onclick=()=>dominoAction("next_hand");
el("domino-rematch").onclick=()=>sendRoomAction("rematch");
el("domino-refresh").onclick=refreshGame;
el("domino-open-rules").onclick=openRules;
el("domino-rules-back").onclick=()=>show(screenBeforeRules);
el("domino-switch").onclick=()=>sendRoomAction("return_lobby");
el("domino-home").onclick=()=>el("main-menu").click();
el("domino-restart").onclick=()=>sendRoomAction("host_join_decision",{decision:"restart_now"});
el("domino-finish").onclick=()=>sendRoomAction("host_join_decision",{decision:"finish_current"});
