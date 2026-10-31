"use strict";
let yoteSelected=-1;
function yoteAction(kind,fields={}){
  if(!snap||!ws||ws.readyState!==WebSocket.OPEN)return;
  ws.send(JSON.stringify({type:"yote",kind,...fields,expected_version:snap.version,request_id:crypto.randomUUID()}));
}
function renderYote(g){
  el("yote-room").textContent=snap.room_id;
  const done=g.phase==="FINISHED",mine=seatIndex===g.actor&&!done&&!g.is_spectator;
  const legal=g.legal||{places:[],steps:[],jumps:[],bonuses:[]};
  if(!mine)yoteSelected=-1;
  const winner=g.winner;
  el("yote-turn").textContent=done?(winner===null?"Yoté draw":(snap.players[winner]?.name||"Player")+" wins Yoté!")
      :mine?(g.pending_bonus?"Remove one bonus opponent stone":"Your turn — place, move or jump")
      :(snap.players[g.actor]?.name||"Player")+"'s turn";
  el("yote-score").textContent=(snap.players[0]?.name||"Player 1")+" (red): "+g.cells.filter(v=>v===1).length+" on board, "+g.reserves[0]+" in reserve · "+
      (snap.players[1]?.name||"Player 2")+" (cream): "+g.cells.filter(v=>v===2).length+" on board, "+g.reserves[1]+" in reserve";
  el("yote-event").textContent=g.event||"";
  const sources=new Set([...legal.steps,...legal.jumps].map(m=>m[0]));
  if(yoteSelected>=0&&!sources.has(yoteSelected))yoteSelected=-1;
  const simple=legal.steps.filter(m=>m[0]===yoteSelected);
  const jumps=legal.jumps.filter(m=>m[0]===yoteSelected);
  const targets=new Map([...simple.map(m=>[m[1],"move"]),...jumps.map(m=>[m[1],"jump"])]);
  const board=el("yote-board");board.replaceChildren();
  for(let i=0;i<30;i++){
    const b=document.createElement("button");b.type="button";
    b.className="yote-square"+(g.cells[i]===1?" yote-p1":g.cells[i]===2?" yote-p2":"");
    b.setAttribute("aria-label","Square "+(i+1)+": "+(g.cells[i]?"occupied":"empty"));
    const canPlace=legal.places.includes(i),canBonus=legal.bonuses.includes(i),canSelect=sources.has(i),action=targets.get(i);
    const active=canPlace||canBonus||canSelect||!!action;
    if(active)b.classList.add("legal");
    if(yoteSelected===i)b.classList.add("selected");
    b.disabled=!active;
    if(canBonus)b.onclick=()=>yoteAction("bonus",{index:i});
    else if(action)b.onclick=()=>{const src=yoteSelected;yoteSelected=-1;yoteAction(action,{source:src,destination:i});};
    else if(canSelect)b.onclick=()=>{yoteSelected=yoteSelected===i?-1:i;renderYote(g);};
    else if(canPlace)b.onclick=()=>yoteAction("place",{index:i});
    if(g.cells[i]){const piece=document.createElement("span");piece.className="yote-piece";b.appendChild(piece);}
    board.appendChild(b);
  }
  el("yote-rematch").classList.toggle("hidden",!done);
  el("yote-rematch").disabled=(snap.rematch_votes||[]).includes(seatIndex);
  el("yote-switch").classList.toggle("hidden",!(done&&seatIndex===snap.host_seat));
  el("yote-reactions").replaceChildren(...REACTIONS.map(emoji=>{
    const b=document.createElement("button");b.type="button";b.textContent=emoji;
    b.onclick=()=>sendRoomAction("reaction",{emoji});return b;
  }));
}
el("yote-refresh").onclick=refreshGame;
el("yote-open-rules").onclick=openRules;
el("yote-rules-back").onclick=()=>show(screenBeforeRules);
el("yote-rematch").onclick=()=>sendRoomAction("rematch");
el("yote-switch").onclick=()=>sendRoomAction("return_lobby");
el("yote-home").onclick=()=>el("main-menu").click();
