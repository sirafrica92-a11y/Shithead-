"use strict";

// Local preview only. Session credentials stay in this browser tab, never in URLs.
const el = id => document.getElementById(id);
const KEY = "shithead-local-seat-v1";
let ws, seatToken, seatIndex = -1, snap = null, roomId = "", reconnects = 0;
let selection = new Set();
let intentionalClose = false;
function status(message) { el("status").textContent = message; }
function loadSeat() {
  try {
    const s = JSON.parse(sessionStorage.getItem(KEY) || "null");
    if(s && typeof s.room === "string" && typeof s.token === "string"
       && typeof s.seat === "number") return s;
  } catch (_) { /* storage may be blocked */ }
  return null;
}
function saveSeat(room, token, seat, name) {
  try { sessionStorage.setItem(KEY, JSON.stringify({room,token,seat,name})); }
  catch (_) { status("Browser session storage blocked; do not refresh during the match."); }
}
function render(x) {
  if(!x || x.type !== "room_state") return;
  if(snap && snap.room_id === x.room_id && x.version < snap.version) return;
  snap = x;
  if(typeof x.you === "number") seatIndex = x.you;
  el("lobby").hidden = false;
  el("room-label").textContent = x.room_id;
  const ul = el("players"); ul.replaceChildren();
  x.players.forEach((p,i) => {
    const li = document.createElement("li");
    li.textContent = (i+1)+". "+p.name+(p.ready?" — Ready":" — Not ready")+
      (p.connected?" • Online":" • Offline")+(i===seatIndex?" (you)":"");
    ul.appendChild(li);
  });
  el("phase").textContent = x.game ? "Match started" :
    (x.all_ready ? "All players ready." : "Waiting for "+x.capacity+" players");
  el("ready").disabled = !(ws && ws.readyState === WebSocket.OPEN && seatIndex >= 0) || !!x.game;
  el("ready").textContent = x.players[seatIndex]?.ready ? "Not ready" : "Ready";
  if(x.game) renderGame(x.game);
  else el("game-panel").hidden = true;
}
function cardName(c) {
  return c.rank === 0 ? "Joker" :
    ({11:"J",12:"Q",13:"K",14:"A"}[c.rank] || String(c.rank))+" "+(c.suit || "");
}
function sendGame(kind, fields={}) {
  if(!snap || !ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({
    type:"game",kind,expected_version:snap.version,
    request_id:crypto.randomUUID(),...fields
  }));
}
function renderGame(g) {
  el("game-panel").hidden = false;
  selection = new Set();
  const mine = g.actor === seatIndex, pending = g.phase === "PILE_PASS_DECISION";
  el("turn-label").textContent = g.phase === "FINISHED" ?
    "Match finished — seat "+(g.loser + 1)+" loses" :
    "Seat "+(g.actor + 1)+" to act"+(mine?" (YOU)":"");
  el("pile-label").textContent = "Pile: "+(g.pile.length ? g.pile.map(cardName).join(", ") : "empty")+
    " · Stock "+g.deck_count+" · Burned "+g.burned_count+(g.locked?" · SEVEN LOCK":"");
  const counts = el("player-counts"); counts.replaceChildren();
  g.players.forEach(p=>{
    const label = document.createElement("p");
    label.textContent="Seat "+(p.seat+1)+": "+p.hand_count+" in hand, "+
      p.face_up.map(cardName).join(" / ")+", "+p.face_down_count+" face-down"+
      (p.finished?" — finished":"");
    counts.appendChild(label);
  });
  const cardList = g.your_zone === "hand" ? g.hand :
    g.your_zone === "face_up" ? g.your_face_up :
    Array(g.players[seatIndex]?.face_down_count || 0).fill(null);
  const holder = el("my-cards");holder.replaceChildren();
  (cardList || []).forEach((card,i)=>{
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = card ? cardName(card) : "Face-down "+(i+1);
    button.setAttribute("aria-pressed","false");
    button.onclick = () => {
      if(selection.has(i)) selection.delete(i);
      else selection.add(i);
      button.setAttribute("aria-pressed",selection.has(i)?"true":"false");
      button.style.background = selection.has(i)?"#f38a3e":"#aebec0";
    };
    button.style.background="#aebec0";
    holder.appendChild(button);
  });
  const target=el("target"); target.replaceChildren();
  g.players.forEach(p=>{
    if(p.seat === seatIndex || p.finished)return;
    const option=document.createElement("option");
    option.value=String(p.seat); option.textContent="Seat "+(p.seat+1);
    target.appendChild(option);
  });
  el("action-hint").textContent = g.your_blind_power ?
    "Blind 3/Joker revealed — choose a target if the pile exists." :
    mine ? (pending?"Accept the pile or counter with a 3/Joker.":"Select a card and play, or pick up if forced.") :
    "Wait for your turn.";
  const playing=mine && !pending && g.phase !== "FINISHED";
  const buttons={
    "play-card":playing && g.your_zone !== "face_down" && !g.your_blind_power,
    "use-power":playing && (g.your_zone !== "face_down" || !!g.your_blind_power),
    "flip-card":playing && g.your_zone === "face_down" && !g.your_blind_power,
    "pickup":playing && g.pile.length > 0 && !g.your_blind_power,
    "counter":mine && pending && g.your_zone !== "face_down",
    "accept":mine && pending
  };
  Object.entries(buttons).forEach(([id,show])=>el(id).hidden=!show);
  target.parentElement.hidden=!mine || (g.pile.length === 0 && !pending);
}
el("play-card").onclick=()=>sendGame("play",{indices:[...selection].sort((a,b)=>a-b)});
el("use-power").onclick=()=>sendGame("power",{
  index:[...selection][0]??null,
  indices:[...selection].sort((a,b)=>a-b),
  target:el("target").value===""?null:Number(el("target").value)
});
el("flip-card").onclick=()=>sendGame("flip",{index:[...selection][0]??0});
el("pickup").onclick=()=>sendGame("pickup");
el("counter").onclick=()=>sendGame("counter",{
  index:[...selection][0]??null,
  target:el("target").value===""?null:Number(el("target").value)
});
el("accept").onclick=()=>sendGame("accept");
async function request(path,data) {
  const response=await fetch(path,{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify(data)
  });
  const obj=await response.json();
  if(!response.ok)throw Error(typeof obj.detail==="string"?obj.detail:"Request failed");
  return obj;
}
function connect(room,token,retry=0) {
  if(ws) {
    ws.onclose=null;
    if(ws.readyState !== WebSocket.CLOSED)ws.close();
  }
  roomId=room;seatToken=token; snap=null;
  intentionalClose=false;
  const socket=new WebSocket((location.protocol==="https:"?"wss://":"ws://")+
    location.host+"/ws/"+encodeURIComponent(room));
  ws=socket;
  socket.onopen=()=>{
    socket.send(JSON.stringify({type:"auth",token}));
    status("Connected to room.");
    reconnects=0;
  };
  socket.onmessage=message=>{
    if(ws!==socket)return;
    let x;
    try {x=JSON.parse(message.data);}catch(_){status("Invalid server response.");return;}
    if(x.type==="error") {
      if(x.stateSnapshot)render(x.stateSnapshot);
      status(x.message||"Action rejected: "+x.reasonCode);
    } else render(x);
  };
  socket.onclose=event=>{
    if(ws!==socket)return;
    el("ready").disabled=true;
    if(event.code===1008){
      status("Room or seat credential no longer valid; start a new room if the server restarted.");
      return;
    }
    if(retry>=5){
      status("Connection lost. Refresh this tab to restore your existing seat.");
      return;
    }
    status("Disconnected; restoring the same seat…");
    const next=retry+1;
    setTimeout(()=>{
      if(ws===socket)connect(room,token,next);
    },Math.min(8000,500*Math.pow(2,next)));
  };
  socket.onerror=()=>{status("Could not reach the local server.");};
}
el("create").onclick=async()=>{
  try {
    const r=await request("/api/rooms",{capacity:Number(el("capacity").value),password:el("create-password").value.trim()||null});
    el("room").value=r.room_id;
    el("join-password").value=r.room_password;
    el("invite").hidden=false;
    el("invite").textContent="Invite code: "+r.room_id+" · Room password: "+r.room_password+" — Share both privately.";
    status("Room created! Join below, and send your friend the room code and password.");
  } catch(e){status(e.message);}
};
el("join").onclick=async()=>{
  try {
    const room=el("room").value.trim(),name=el("name").value.trim();
    if(!room||!name){status("Enter your name and the room code.");return;}
    const saved=loadSeat();
    if(saved?.room===room){
      seatIndex=saved.seat;
      connect(room,saved.token);
      return;
    }
    const password=el("join-password").value;
    if(!password){status("Enter the room password shared by the host.");return;}
    const r=await request("/api/rooms/"+encodeURIComponent(room)+"/join",{name,password});
    seatIndex=r.seat;
    saveSeat(room,r.token,r.seat,name);
    connect(room,r.token);
  }catch(e){status(e.message);}
};
el("ready").onclick=()=>{
  if(!snap||!ws||ws.readyState!==WebSocket.OPEN)return;
  ws.send(JSON.stringify({
    type:"ready",ready:!snap.players[seatIndex]?.ready,
    expected_version:snap.version,request_id:crypto.randomUUID()
  }));
};
// Refresh and network reconnect use the original seat token, not a second Join.
const saved=loadSeat();
if(saved){
  el("room").value=saved.room;
  el("name").value=saved.name||"Player";
  seatIndex=saved.seat;
  connect(saved.room,saved.token);
}
