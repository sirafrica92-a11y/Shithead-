"use strict";
const el=id=>document.getElementById(id);
let session=null,busy=false,selected=-1;
function message(s){el("error").textContent=s;}
async function api(path,opts={}){
 const r=await fetch(path,{cache:"no-store",...opts});
 let data;try{data=await r.json();}catch{throw Error("Server response unavailable");}
 if(!r.ok){const e=new Error(typeof data.detail==="string"?data.detail:"Request rejected");e.status=r.status;throw e;}
 return data;
}
function saved(){try{const s=JSON.parse(sessionStorage.getItem("shithead-solo-dara"));return s?.id&&s?.token?s:null;}catch{return null;}}
function remember(){try{if(session)sessionStorage.setItem("shithead-solo-dara",JSON.stringify({id:session.id,token:session.token}));}catch{}}
function forget(){try{sessionStorage.removeItem("shithead-solo-dara");}catch{}}
function render(){
 if(!session)return;
 const g=session.game,done=g.phase==="FINISHED",mine=g.actor===0&&!done;
 const legal=mine&&!busy?g.legal||{places:[],moves:[],captures:[]}:{places:[],moves:[],captures:[]};
 const sources=new Set(legal.moves.map(m=>m[0]));
 if(!sources.has(selected))selected=-1;
 const targets=new Set(legal.moves.filter(m=>m[0]===selected).map(m=>m[1]));
 el("turn").textContent=done?(g.winner===null?"Draw":g.winner===0?"You win!":"Computer wins!"):(mine?(g.pending_capture?"Capture an opponent's stone":g.stage==="PLACE"?"Place a stone":"Move a stone"):"Computer's turn");
 el("stage").textContent=g.stage==="PLACE"?"Placement round · "+g.placed[0]+"/12 placed":"Movement round · select a stone, then its destination";
 el("you-count").textContent=g.cells.filter(v=>v===1).length+"/12";
 el("bot-count").textContent=g.cells.filter(v=>v===2).length+"/12";
 el("event").textContent=g.event||"";
 el("again").classList.toggle("hidden",!done);
 const frag=document.createDocumentFragment();
 for(let i=0;i<30;i++){
   const btn=document.createElement("button");btn.type="button";btn.className="square";
   let action=null;
   if(legal.places.includes(i))action=()=>act("place",{index:i});
   else if(legal.captures.includes(i))action=()=>act("capture",{index:i});
   else if(targets.has(i))action=()=>{const source=selected;selected=-1;act("move",{source,destination:i});};
   else if(sources.has(i))action=()=>{selected=selected===i?-1:i;render();};
   if(action){btn.classList.add("legal");btn.onclick=action;}
   if(selected===i)btn.classList.add("selected");
   btn.disabled=!action;
   btn.setAttribute("aria-label","Square "+(i+1)+": "+(g.cells[i]===0?"empty":g.cells[i]===1?"your stone":"computer stone"));
   if(g.cells[i]){const piece=document.createElement("span");piece.className="stone "+(g.cells[i]===1?"you":"computer");btn.append(piece);}
   frag.append(btn);
 }
 el("board").replaceChildren(frag);
}
async function begin(){
 if(busy)return;busy=true;el("new").disabled=true;message("");
 try{
   let updated;
   if(session?.id&&session?.token){
     try{updated=await api("/api/solo/dara/"+encodeURIComponent(session.id)+"/reset",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:session.token,version:session.version})});session={...session,...updated};}
     catch(e){if(e.status!==404)throw e;session=await api("/api/solo/dara",{method:"POST"});}
   }else session=await api("/api/solo/dara",{method:"POST"});
   selected=-1;remember();
 }catch(e){message(e.message);}
 finally{busy=false;el("new").disabled=false;render();}
}
async function fetchLatest(){
 const data=await api("/api/solo/dara/"+encodeURIComponent(session.id),{headers:{"X-Solo-Token":session.token}});
 session={...session,...data};selected=-1;remember();
}
async function act(kind,fields){
 if(!session||busy)return;busy=true;message("");render();
 try{
   const data=await api("/api/solo/dara/"+encodeURIComponent(session.id),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:session.token,version:session.version,kind,...fields})});
   session={...session,...data};selected=-1;remember();
 }catch(e){message(e.message);if(e.status===409){try{await fetchLatest();}catch(err){message("Could not refresh board: "+err.message);}}}
 finally{busy=false;render();}
}
async function resume(){
 const old=saved();if(!old||busy||session)return;
 try{
   const data=await api("/api/solo/dara/"+encodeURIComponent(old.id),{headers:{"X-Solo-Token":old.token}});
   if(!busy&&!session){session={...old,...data};render();}
 }catch(e){if(busy||session)return;if(e.status===404){forget();message("Previous match expired. Start a new game.");}else message("Could not reconnect. Check your connection and reload.");}
}
el("new").onclick=begin;el("again").onclick=begin;resume();
