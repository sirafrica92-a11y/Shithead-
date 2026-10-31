"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.join(__dirname, "../app/static");
const file = name => fs.readFileSync(path.join(root, name), "utf8");

test("changing screens always hides Shithead table and the setup page", () => {
  const js = file("client.js");
  const first = js.indexOf("function show(screen) {");
  const last = js.indexOf("function openRules()", first);
  assert.ok(first >= 0 && last > first);
  const source = js.slice(first, last);
  const changes = new Map();
  const context = {
    el: name => ({classList: {toggle: (nameOfClass, isHidden) => {
      if (nameOfClass === "hidden") changes.set(name, isHidden);
    }}}),
  };
  vm.runInNewContext(source + "\nglobalThis.setScreen = show;", context);
  context.setScreen("screen-setup");
  assert.equal(changes.get("screen-home"), true);
  assert.equal(changes.get("screen-table"), true);
  assert.equal(changes.get("screen-setup"), false);
  context.setScreen("screen-table");
  assert.equal(changes.get("screen-table"), false);
  assert.equal(changes.get("screen-setup"), true);
  context.setScreen("screen-ludo");
  assert.equal(changes.get("screen-table"), true);
  assert.equal(changes.get("screen-ludo"), false);
  assert.ok(js.includes('show("screen-setup")'));
  assert.ok(js.includes('el("setup-game-name").textContent'));
});

for(const name of ["solo-ludo.js","solo-awale.js"]){
  test(name+" preserves a working API helper with validated errors", async () => {
    const js=file(name);
    assert.equal((js.match(/async function api\(/g)||[]).length,1);
    const begin=js.indexOf("async function api(");
    const end=js.indexOf("function saved(){",begin);
    assert.ok(begin>=0 && end>begin);
    const requests=[];
    let response={ok:true,status:200,json:async()=>({id:"MATCH",token:"TOKEN",version:1})};
    const context={
      fetch:async(url,options)=>{requests.push({url,options});return response;},
      Error,
    };
    vm.runInNewContext(js.slice(begin,end)+"\nglobalThis.callApi=api;",context);
    const ok=await context.callApi("/api/solo/test",{method:"POST"});
    assert.equal(ok.id,"MATCH");
    assert.equal(requests.length,1);
    assert.equal(requests[0].options.cache,"no-store");
    assert.equal(requests[0].options.method,"POST");
    response={ok:false,status:409,json:async()=>({detail:"stale turn"})};
    await assert.rejects(context.callApi("/api/solo/test"),e=>e.status===409&&e.message==="stale turn");
    response={ok:true,status:200,json:async()=>{throw Error("invalid response")}};
    await assert.rejects(context.callApi("/api/solo/test"),/Server/);
    assert.ok(js.includes("await showComputerTurns"));
    assert.ok(js.includes('displayFrame=step.game'));
    assert.ok(js.includes('id') || js.includes("session"));
  });
}
