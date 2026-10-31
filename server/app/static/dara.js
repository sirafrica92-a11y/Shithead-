"use strict";
/* Dara visual renderer. The server owns every legal placement and capture. */
let daraSelected=-1;
function daraAction(kind,fields={}){
  if(!snap||!ws||ws.readyState!==WebSocket.OPEN)return;
  ws.send(JSON.stringify({type:"dara",kind,...fields,expected_version:snap.version,request_id:crypto.randomUUID()}));
}
function renderDara(g){
  el("dara-room").textContent=snap.room_id;
  const done=g.phase==="FINISHED",mine=seatIndex===g.actor&&!done&&!g.is_spectator;
  const legal=g.legal||{places:[],moves:[],captures:[]};
  if(!mine)daraSelected=-1;
  const event=g.event||"";
  el("dara-turn").textContent=done
    ?g.winner===null?"Draw":(snap.players[g.winner]?.name||"Player")+" wins Dara!"
    :mine?(g.pending_capture?"Your capture — remove an opposing piece":g.stage==="PLACE"?"Your turn — place a piece":"Your turn — move a piece")
    :(snap.players[g.actor]?.name||"Player")+"'s turn";
  el("dara-progress").textContent=(snap.players[0]?.name||"Player 1")+" (red): "+g.cells.filter(v=>v===1).length+
      " "+(g.cells.filter(v=>v===1).length===1?"piece":"pieces")+" · "+(snap.players[1]?.name||"Player 2")+" (cream): "+g.cells.filter(v=>v===2).length+
      " "+(g.cells.filter(v=>v===2).length===1?"piece":"pieces")+" · "+(g.stage==="PLACE"?"Placement":"Movement");
  el("dara-event").textContent=namedGameEvent(event);
  const legalSources=new Set(legal.moves.map(m=>m[0]));
  const legalTargets=new Set(legal.moves.filter(m=>m[0]===daraSelected).map(m=>m[1]));
  if(daraSelected>=0&&!legalSources.has(daraSelected))daraSelected=-1;
  const board=el("dara-board");
  board.replaceChildren();
  for(let i=0;i<30;i++){
    const btn=document.createElement("button");btn.type="button";
    btn.className="dara-square"+(g.cells[i]===1?" dara-p1":g.cells[i]===2?" dara-p2":"")+
        (legal.places.includes(i)||legal.captures.includes(i)||legalTargets.has(i)?" legal":"")+
        (daraSelected===i?" selected":"");
    btn.setAttribute("aria-label","Square "+(i+1)+": "+(g.cells[i]===0?"empty":snap.players[g.cells[i]-1]?.name||"occupied"));
    let active=false;
    if(legal.places.includes(i)){
      active=true;btn.onclick=()=>daraAction("place",{index:i});
    }else if(legal.captures.includes(i)){
      active=true;btn.onclick=()=>daraAction("capture",{index:i});
    }else if(legalTargets.has(i)){
      active=true;btn.onclick=()=>{const src=daraSelected;daraSelected=-1;daraAction("move",{source:src,destination:i});};
    }else if(legalSources.has(i)){
      active=true;btn.onclick=()=>{daraSelected=daraSelected===i?-1:i;renderDara(g);};
    }
    btn.disabled=!active;
    if(g.cells[i]){
      const piece=document.createElement("span");piece.className="dara-piece";
      btn.appendChild(piece);
    }
    board.appendChild(btn);
  }
  el("dara-rematch").classList.toggle("hidden",!done);
  el("dara-rematch").disabled=(snap.rematch_votes||[]).includes(seatIndex);
  el("dara-switch").classList.toggle("hidden",!(done&&seatIndex===snap.host_seat));
  el("dara-reactions").replaceChildren(...REACTIONS.map(emoji=>{
    const b=document.createElement("button");b.type="button";b.textContent=emoji;
    b.onclick=()=>sendRoomAction("reaction",{emoji});return b;
  }));
  const pending=snap.pending_joiners||[];
  el("dara-join-prompt").classList.toggle("hidden",!(seatIndex===snap.host_seat&&pending.length&&!done));
  el("dara-join-names").textContent=pending.map(i=>snap.players[i]?.name||"Friend").join(", ");
}
el("dara-refresh").onclick=refreshGame;
el("dara-open-rules").onclick=openRules;
el("dara-rules-back").onclick=()=>show(screenBeforeRules);
el("dara-rematch").onclick=()=>sendRoomAction("rematch");
el("dara-switch").onclick=()=>sendRoomAction("return_lobby");
el("dara-home").onclick=()=>el("main-menu").click();
el("dara-restart").onclick=()=>sendRoomAction("host_join_decision",{decision:"restart_now"});
el("dara-finish").onclick=()=>sendRoomAction("host_join_decision",{decision:"finish_current"});
