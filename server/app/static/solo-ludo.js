"use strict";
const $=id=>document.getElementById(id);
const track=[[6,1],[6,2],[6,3],[6,4],[6,5],[5,6],[4,6],[3,6],[2,6],[1,6],[0,6],[0,7],[0,8],[1,8],[2,8],[3,8],[4,8],[5,8],[6,9],[6,10],[6,11],[6,12],[6,13],[6,14],[7,14],[8,14],[8,13],[8,12],[8,11],[8,10],[8,9],[9,8],[10,8],[11,8],[12,8],[13,8],[14,8],[14,7],[14,6],[13,6],[12,6],[11,6],[10,6],[9,6],[8,5],[8,4],[8,3],[8,2],[8,1],[8,0],[7,0],[6,0]];
const bases={red:[[2,2],[2,3],[3,2],[3,3]],yellow:[[11,11],[11,12],[12,11],[12,12]]};
const lanes={red:[[7,1],[7,2],[7,3],[7,4],[7,5]],yellow:[[7,13],[7,12],[7,11],[7,10],[7,9]]};
const starts={red:0,yellow:26};
let session=null,busy=false;
function put(text){$("error").textContent=text;}
async function api(url,options={}){
 const response=await fetch(url,{cache:"no-store",...options});
 let body;try{body=await response.json();}catch{throw Error("Server did not respond correctly");}
 if(!response.ok)throw Error(typeof body.detail==="string"?body.detail:"Server rejected that request");
 return body;
}
function saved(){try{const s=JSON.parse(sessionStorage.getItem("shithead-solo-ludo"));return s?.id&&s?.token?s:null;}catch{return null;}}
function remember(){if(session)sessionStorage.setItem("shithead-solo-ludo",JSON.stringify({id:session.id,token:session.token}));}
async function start(){
 if(busy)return;busy=true;$("new").disabled=true;put("");
 try{session=await api("/api/solo/ludo",{method:"POST"});remember();render();}
 catch(e){put(e.message);}finally{busy=false;$("new").disabled=false;}
}
function board(g){
 const cfg=Array.from({length:15},()=>Array.from({length:15},()=>({kind:"empty",color:""})));
 function mark(r,c,kind,color=""){cfg[r][c]={kind,color};}
 for(let r=0;r<6;r++)for(let c=0;c<6;c++)mark(r,c,"base","red");
 for(let r=9;r<15;r++)for(let c=9;c<15;c++)mark(r,c,"base","yellow");
 for(let r=0;r<6;r++)for(let c=9;c<15;c++)mark(r,c,"base","green");
 for(let r=9;r<15;r++)for(let c=0;c<6;c++)mark(r,c,"base","blue");
 track.forEach(([r,c],i)=>mark(r,c,g.safe_squares.includes(i)?"safe":"track"));
 Object.entries(lanes).forEach(([color,coords])=>coords.forEach(([r,c])=>mark(r,c,"lane",color)));
 Object.entries(starts).forEach(([color,i])=>mark(...track[i],"start",color));
 for(let r=6;r<9;r++)for(let c=6;c<9;c++)mark(r,c,"centre");
 const overlay=new Map();
 g.players.forEach(p=>p.tokens.forEach((progress,index)=>{
   if(progress===56)return;
   const loc=progress===-1?bases[p.color][index]:progress>=51?lanes[p.color][progress-51]:track[(starts[p.color]+progress)%52];
   const key=loc.join(":");if(!overlay.has(key))overlay.set(key,[]);
   overlay.get(key).push({color:p.color,index,seat:p.seat});
 }));
 const frag=document.createDocumentFragment();
 for(let row=0;row<15;row++)for(let col=0;col<15;col++){
   const cell=document.createElement("div"),item=cfg[row][col];cell.className="cell "+item.kind+" "+item.color;
   if(item.kind==="safe")cell.textContent="★";
   if(item.kind==="centre")cell.textContent="◆";
   for(const token of overlay.get(row+":"+col)||[]){
     const btn=document.createElement("button");btn.type="button";btn.className="piece "+token.color;
     const legal=token.seat===0&&(g.your_legal_tokens||[]).includes(token.index)&&!busy;
     if(legal)btn.classList.add("legal");
     btn.disabled=!legal;btn.textContent=String(token.index+1);btn.title=(token.seat===0?"Your":"Computer")+" token "+(token.index+1);
     if(legal)btn.onclick=()=>act("move",token.index);
     cell.appendChild(btn);
   }frag.appendChild(cell);
 }
 $("board").replaceChildren(frag);
}
function render(){
 if(!session)return;
 const g=session.game,over=g.phase==="FINISHED",mine=g.actor===0;
 $("turn").textContent=over?(g.winner===0?"You won! 🎉":"Computer wins!"):(mine?"Your turn":"Computer's turn");
 $("die").textContent=g.die??g.last_roll??"⚄";
 $("event").textContent=g.event;
 $("you-progress").textContent=g.players[0].tokens.filter(x=>x===56).length+"/4 home";
 $("bot-progress").textContent=g.players[1].tokens.filter(x=>x===56).length+"/4 home";
 $("roll").disabled=busy||over||!mine||g.turn_stage!=="ROLL";
 $("again").classList.toggle("hidden",!over);
 const legal=mine&&!over&&!busy?(g.your_legal_tokens||[]):[];
 $("moves").replaceChildren(...legal.map(i=>{
   const b=document.createElement("button");b.textContent="Move token "+(i+1);b.onclick=()=>act("move",i);return b;
 }));
 board(g);
}
async function act(action,piece=null){
 if(!session||busy)return;busy=true;put("");render();
 try{
   const updated=await api("/api/solo/ludo/"+encodeURIComponent(session.id),{
     method:"POST",headers:{"Content-Type":"application/json"},
     body:JSON.stringify({token:session.token,version:session.version,action,piece})
   });
   session={...session,...updated};
 }catch(e){put(e.message);if(e.message.includes("Board changed"))await resume();}
 finally{busy=false;render();}
}
async function resume(){
 const old=saved();if(!old)return;
 try{session={...old,...await api("/api/solo/ludo/"+encodeURIComponent(old.id)+"?token="+encodeURIComponent(old.token))};render();}
 catch{session=null;sessionStorage.removeItem("shithead-solo-ludo");}
}
$("new").onclick=start;$("again").onclick=start;$("roll").onclick=()=>act("roll");
resume();
