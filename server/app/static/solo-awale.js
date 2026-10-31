"use strict";
const el=id=>document.getElementById(id);
let session=null,busy=false;
function showError(msg){el("error").textContent=msg;}
async function api(url,opts={}){
 const response=await fetch(url,{cache:"no-store",...opts});
 let json;try{json=await response.json();}catch{throw Error("Server response unavailable");}
 if(!response.ok){const err=new Error(typeof json.detail==="string"?json.detail:"Request rejected");err.status=response.status;throw err;}
 return json;
}
function saved(){try{const x=JSON.parse(sessionStorage.getItem("shithead-solo-awale"));return x?.id&&x?.token?x:null;}catch{return null;}}
function remember(){try{if(session)sessionStorage.setItem("shithead-solo-awale",JSON.stringify({id:session.id,token:session.token}));}catch{}}
function forget(){try{sessionStorage.removeItem("shithead-solo-awale");}catch{}}
function render(){
 if(!session)return;
 const g=session.game,over=g.phase==="FINISHED",mine=g.actor===0;
 el("score-you").textContent=g.captured[0];el("score-computer").textContent=g.captured[1];
 el("turn").textContent=over?(g.winner===null?"Awalé ends in a draw":g.winner===0?"You win!":"Computer wins!"):(mine?"Your turn · choose a house":"Computer's turn");
 el("event").textContent=g.event||"";
 el("again").classList.toggle("hidden",!over);
 const legal=mine&&!over&&!busy?g.your_legal_pits||[]:[];
 const board=el("board");board.replaceChildren();
 for(const indexes of [[11,10,9,8,7,6],[0,1,2,3,4,5]]){
   const row=document.createElement("div");row.className="row";
   for(const index of indexes){
     const b=document.createElement("button");b.type="button";
     b.className="house"+(legal.includes(index)?" legal":"")+(g.last_pit===index?" last":"");
     b.disabled=!legal.includes(index);
     b.setAttribute("aria-label","House "+(index+1)+": "+g.pits[index]+" seeds");
     b.title="House "+(index+1);
     const seeds=document.createElement("span");seeds.className="seeds";
     for(let i=0;i<Math.min(g.pits[index],12);i++){const grain=document.createElement("span");grain.className="grain";seeds.append(grain);}
     const number=document.createElement("strong");number.textContent=String(g.pits[index]);
     b.append(seeds,number);
     if(legal.includes(index))b.onclick=()=>sow(index);
     row.append(b);
   }
   board.append(row);
 }
}
async function start(){
 if(busy)return;busy=true;el("new").disabled=true;showError("");
 try{
   if(session?.id&&session?.token){
     try{
       const update=await api("/api/solo/awale/"+encodeURIComponent(session.id)+"/reset",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:session.token,version:session.version})});
       session={...session,...update};
     }catch(e){
       if(e.status!==404)throw e;
       session=await api("/api/solo/awale",{method:"POST"});
     }
   }else session=await api("/api/solo/awale",{method:"POST"});
   remember();
 }catch(e){showError(e.message);}
 finally{busy=false;el("new").disabled=false;render();}
}
async function refresh(){
 if(!session)return;
 const update=await api("/api/solo/awale/"+encodeURIComponent(session.id),{headers:{"X-Solo-Token":session.token}});
 session={...session,...update};remember();
}
async function sow(index){
 if(!session||busy)return;busy=true;showError("");render();
 try{
   const update=await api("/api/solo/awale/"+encodeURIComponent(session.id),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:session.token,version:session.version,pit:index})});
   session={...session,...update};remember();
 }catch(e){
   showError(e.message);
   if(e.status===409){try{await refresh();}catch(err){showError("Could not refresh the board. "+err.message);}}
 }finally{busy=false;render();}
}
async function resume(){
 const old=saved();if(!old||busy||session)return;
 try{
   const update=await api("/api/solo/awale/"+encodeURIComponent(old.id),{headers:{"X-Solo-Token":old.token}});
   if(!busy&&!session){session={...old,...update};render();}
 }catch(e){
   if(busy||session)return;
   if(e.status===404){forget();showError("Previous Solo Play game expired. Start a new game.");}
   else showError("Could not reconnect. Check your connection and reload.");
 }
}
el("new").onclick=start;el("again").onclick=start;resume();
