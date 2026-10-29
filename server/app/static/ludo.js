"use strict";
/* Independent Ludo presentation: the server owns dice and token movement. */
const LUDO_TRACK = [
[6,1],[6,2],[6,3],[6,4],[6,5],[5,6],[4,6],[3,6],[2,6],[1,6],[0,6],[0,7],[0,8],
[1,8],[2,8],[3,8],[4,8],[5,8],[6,9],[6,10],[6,11],[6,12],[6,13],[6,14],[7,14],
[8,14],[8,13],[8,12],[8,11],[8,10],[8,9],[9,8],[10,8],[11,8],[12,8],[13,8],[14,8],
[14,7],[14,6],[13,6],[12,6],[11,6],[10,6],[9,6],[8,5],[8,4],[8,3],[8,2],[8,1],[8,0],[7,0],[6,0]];
const LUDO_STARTS = {red:0,green:13,yellow:26,blue:39};
const LUDO_LANES = {
  red:[[7,1],[7,2],[7,3],[7,4],[7,5]],
  green:[[1,7],[2,7],[3,7],[4,7],[5,7]],
  yellow:[[7,13],[7,12],[7,11],[7,10],[7,9]],
  blue:[[13,7],[12,7],[11,7],[10,7],[9,7]]
};
const LUDO_BASES = {
  red:[[2,2],[2,3],[3,2],[3,3]],
  green:[[2,11],[2,12],[3,11],[3,12]],
  yellow:[[11,11],[11,12],[12,11],[12,12]],
  blue:[[11,2],[11,3],[12,2],[12,3]]
};
function sendLudo(kind, token = null) {
  if (!snap || !ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({type:"ludo",kind,token,expected_version:snap.version,
                          request_id:crypto.randomUUID()}));
}
function renderLudo(g) {
  const pending = snap.pending_joiners || [];
  el("ludo-join-prompt").classList.toggle("hidden",
    !(seatIndex === snap.host_seat && pending.length && g.phase !== "FINISHED"));
  el("ludo-join-names").textContent = pending.map(i=>snap.players[i]?.name||"Friend").join(", ");
  const players = el("ludo-players");
  players.replaceChildren();
  g.players.forEach(p=>{
    const card=document.createElement("div");
    card.className="ludo-player"+(g.actor===p.seat&&g.phase!=="FINISHED"?" active":"");
    const dot=document.createElement("span");dot.className="dot "+p.color;
    const name=document.createElement("span");name.className="name";
    name.textContent=snap.players[p.seat]?.name || ("Player "+(p.seat+1));
    const progress=document.createElement("span");progress.className="progress";
    progress.textContent=p.tokens.filter(t=>t===56).length+"/4 home";
    card.append(dot,name,progress);players.appendChild(card);
  });
  const choices=el("ludo-move-options");
  const legal=g.your_legal_tokens||[];
  choices.classList.toggle("hidden",legal.length===0);
  choices.replaceChildren();
  if(legal.length){
    const heading=document.createElement("strong");heading.textContent="Choose a token to move:";
    choices.appendChild(heading);
    legal.forEach(index=>{
      const btn=document.createElement("button");btn.type="button";
      btn.textContent="Token "+(index+1);btn.onclick=()=>sendLudo("move",index);
      choices.appendChild(btn);
    });
  }
  const board = el("ludo-board");
  board.replaceChildren();
  const cells = Array.from({length:15},()=>Array(15).fill(null));
  function paint(row,col,kind,color) { cells[row][col]={kind,color}; }
  for (let r=0;r<6;r++) for(let c=0;c<6;c++) paint(r,c,"base","red");
  for (let r=0;r<6;r++) for(let c=9;c<15;c++) paint(r,c,"base","green");
  for (let r=9;r<15;r++) for(let c=9;c<15;c++) paint(r,c,"base","yellow");
  for (let r=9;r<15;r++) for(let c=0;c<6;c++) paint(r,c,"base","blue");
  LUDO_TRACK.forEach(([r,c],i)=>paint(r,c,g.safe_squares.includes(i)?"safe":"track",null));
  Object.entries(LUDO_LANES).forEach(([color,steps])=>steps.forEach(([r,c])=>paint(r,c,"lane",color)));
  Object.entries(LUDO_STARTS).forEach(([color,i])=>{
    const [r,c]=LUDO_TRACK[i];paint(r,c,"start",color);
  });
  for(let r=6;r<9;r++)for(let c=6;c<9;c++)paint(r,c,"center",null);
  const overlays = new Map();
  g.players.forEach(p => {
    p.tokens.forEach((progress,index)=>{
      let pos;
      if(progress===56)return; // Finished pieces belong in the home score, not a pile in the centre.
      if(progress===-1)pos=LUDO_BASES[p.color][index];
      else if(progress>=51)pos=LUDO_LANES[p.color][progress-51];
      else pos=LUDO_TRACK[(LUDO_STARTS[p.color]+progress)%52];
      const key=pos.join(":");
      if(!overlays.has(key))overlays.set(key,[]);
      overlays.get(key).push({color:p.color,index,seat:p.seat});
    });
  });
  for(let row=0;row<15;row++)for(let col=0;col<15;col++){
    const cell=document.createElement("div");
    const config=cells[row][col];
    cell.className="ludo-cell "+(config?.kind||"blank")+" "+(config?.color||"");
    cell.style.gridRow=String(row+1);cell.style.gridColumn=String(col+1);
    if(config?.kind==="safe")cell.textContent="★";
    if(config?.kind==="center")cell.textContent="◆";
    for(const piece of overlays.get(row+":"+col)||[]){
      const btn=document.createElement("button");
      btn.className="ludo-token "+piece.color;
      btn.type="button";
      btn.textContent=String(piece.index+1);
      btn.title=(snap.players[piece.seat]?.name||"Player")+" token "+(piece.index+1);
      const legal=piece.seat===seatIndex&&(g.your_legal_tokens||[]).includes(piece.index);
      btn.disabled=!legal;
      if(legal){btn.classList.add("legal");btn.onclick=()=>sendLudo("move",piece.index);}
      cell.appendChild(btn);
    }
    board.appendChild(cell);
  }
  const mine=g.actor===seatIndex&&!g.is_spectator,over=g.phase==="FINISHED";
  const current=snap.players[g.actor]?.name||"Player";
  el("ludo-turn").textContent=over?(snap.players[g.winner]?.name||"Player")+" wins Ludo!"
    :g.is_spectator?"Waiting for next round":mine?"Your turn":current+"'s turn";
  el("ludo-dice").textContent=g.die||g.last_roll||"⚄";
  el("ludo-event").textContent=g.event;
  el("ludo-roll").classList.toggle("hidden",over||!mine||g.turn_stage!=="ROLL");
  el("ludo-roll").disabled=!(mine&&g.turn_stage==="ROLL");
  el("ludo-rematch").classList.toggle("hidden",!over);
  el("ludo-rematch").disabled=(snap.rematch_votes||[]).includes(seatIndex);
  el("ludo-rematch").textContent=el("ludo-rematch").disabled?"Waiting for rematch votes":"Play again in this room";
  el("ludo-switch").classList.toggle("hidden",!(over&&seatIndex===snap.host_seat));
  el("ludo-reactions").classList.toggle("hidden",over);
  el("ludo-reactions").replaceChildren(...REACTIONS.map(emoji=>{
    const btn=document.createElement("button");btn.type="button";btn.textContent=emoji;
    btn.onclick=()=>sendRoomAction("reaction",{emoji});return btn;
  }));
}
el("ludo-roll").onclick=()=>sendLudo("roll");
el("ludo-restart").onclick=()=>sendRoomAction("host_join_decision",{decision:"restart_now"});
el("ludo-finish").onclick=()=>sendRoomAction("host_join_decision",{decision:"finish_current"});
el("ludo-rematch").onclick=()=>sendRoomAction("rematch");
el("ludo-home").onclick=()=>el("main-menu").click();
