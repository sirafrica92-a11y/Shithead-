"use strict";
// Owner-only page. All values are aggregates delivered by a protected API.
// Use DOM textContent, never HTML assembled from externally supplied values.
const el=id=>document.getElementById(id);
const fmt=new Intl.NumberFormat("en-GB");
function add(parent,tag,text,css) {
  const node=document.createElement(tag);
  if(css)node.className=css;
  node.textContent=String(text);
  parent.appendChild(node);return node;
}
function empty(node){node.replaceChildren();}
function rows(target, data, keys) {
  const body=el(target);empty(body);
  if(!data.length){
    const tr=document.createElement("tr"),td=document.createElement("td");
    td.colSpan=keys.length;td.textContent="No data yet";tr.appendChild(td);body.appendChild(tr);
    return;
  }
  for(const item of data){
    const tr=document.createElement("tr");
    for(const key of keys)add(tr,"td",typeof item[key]==="number"?fmt.format(item[key]):item[key]||"—");
    body.appendChild(tr);
  }
}
function bars(target,items,nameKey,countKey){
  const root=el(target);empty(root);
  const max=Math.max(1,...items.map(x=>x[countKey]||0));
  for(const item of items){
    const section=add(root,"div","","barrow");
    const title=add(section,"div","","barheader");
    add(title,"span",item[nameKey]||"Unknown");
    add(title,"b",fmt.format(item[countKey]||0));
    const track=add(section,"div","","bartrack");
    const bar=add(track,"div","","barfill");
    bar.style.width=((item[countKey]||0)/max*100)+"%";
  }
}
function render(data) {
  const overview=data.overview;
  el("capacity-rejections").textContent=fmt.format(overview.capacity_rejections||0);
  el("views").textContent=fmt.format(overview.page_views);
  el("rooms").textContent=fmt.format(overview.rooms_created);
  el("starts").textContent=fmt.format(overview.matches_started);
  el("ends").textContent=fmt.format(overview.matches_completed);
  el("live-rooms").textContent=fmt.format(data.live.active_rooms);
  el("live-seats").textContent=fmt.format(data.live.connected_seats);
  el("allocated-rooms").textContent=fmt.format(data.live.rooms_in_memory);
  el("room-limit").textContent=fmt.format(data.live.room_limit);
  bars("ranking",data.games,"name","matches_started");
  rows("game-table",data.games,["name","rooms_created","matches_started","matches_completed","capacity_rejections"]);
  rows("daily-table",data.daily.slice(-31).reverse(),["date","page_views","rooms_created","matches_started","matches_completed","capacity_rejections"]);
  bars("sources",data.sources,"source","page_views");
  const domino=data.games.find(g=>g.key==="dominoes");
  const modes=domino?Object.entries(domino.modes).map(([key,v])=>({
    name:key==="partner"?"Partner (teams)":"Cut Throat (individual)",
    matches_started:v.matches_started,rooms_created:v.rooms_created
  })):[];
  bars("domino-modes",modes.length?modes:[
    {name:"Partner (teams)",matches_started:0},
    {name:"Cut Throat (individual)",matches_started:0},
  ],"name","matches_started");
  el("status").classList.remove("error");
  el("status").textContent="Updated · "+new Date().toLocaleString("en-GB")+
    " · Reporting dates in UTC · "+
    (data.available_from?"Earliest recorded day: "+data.available_from:"No analytics events recorded yet");
}
async function load(){
  el("status").classList.remove("error");
  el("status").textContent="Updating…";
  try{
    const days=el("period").value;
    const response=await fetch("/owner/api/analytics?days="+encodeURIComponent(days),{
      credentials:"same-origin",cache:"no-store",headers:{"Accept":"application/json"}
    });
    if(!response.ok)throw new Error(response.status===503?
      "Analytics storage is unavailable; gameplay is unaffected.":
      "Unable to load owner analytics (HTTP "+response.status+").");
    render(await response.json());
  }catch(error){
    el("status").classList.add("error");
    el("status").textContent=error.message||"Analytics not available";
  }
}
el("refresh").addEventListener("click",load);
el("period").addEventListener("change",load);
el("export").addEventListener("click",()=>{
  // Same-origin, owner-authenticated download; no personal data in CSV.
  window.location.href="/owner/api/analytics.csv?days="+encodeURIComponent(el("period").value);
});
load();