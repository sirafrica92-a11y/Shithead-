"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

// Exercise the ACTUAL client transport code, not a copied approximation.
// Stub only the browser and WebSocket environment, not the recovery functions.
const client = fs.readFileSync(path.join(__dirname, "../app/static/client.js"), "utf8");
const prefix = "function stopTransportTimers() {";
const suffix = "/* ------------------------------------------------------------ home flow */";
assert.equal(client.split(prefix).length, 2);
const source = prefix + client.split(prefix)[1].split(suffix)[0];
assert.ok(source.includes("function recoverLiveSeat()"));

function setup() {
  let now = 1000;
  let nextTimer = 1;
  const timers = new Map(), sockets = [], events = new Map();
  const statuses = [], views = [];
  const ready = { disabled: false };
  const setTimer = (fn, delay, repeat) => {
    const id = nextTimer++, period = Math.max(Number(delay) || 1, 1);
    timers.set(id, {fn, at: now + period, repeat, period});
    return id;
  };
  const advance = ms => {
    const target = now + ms;
    for (let steps = 0; steps < 10000; steps++) {
      let chosen, timer;
      for (const [id, entry] of timers) {
        if (entry.at <= target && (!timer || entry.at < timer.at)) {
          chosen = id; timer = entry;
        }
      }
      if (!timer) { now = target; return; }
      now = timer.at;
      if (timer.repeat) timer.at += timer.period;
      else timers.delete(chosen);
      timer.fn();
    }
    throw Error("Runaway timers");
  };
  class Socket {
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSED = 3;
    constructor(url) {
      this.url = url;
      this.sent = [];
      this.readyState = 0;
      sockets.push(this);
    }
    open() { this.readyState = 1; this.onopen?.(); }
    send(value) {
      assert.equal(this.readyState, 1);
      this.sent.push(JSON.parse(value));
    }
    emit(value) { this.onmessage?.({data: JSON.stringify(value)}); }
    close(code = 1006) {
      if (this.readyState === 3) return;
      this.readyState = 3;
      this.onclose?.({code});
    }
  }
  const context = {
    WebSocket: Socket, Date: {now: () => now},
    location: {protocol: "https:", host: "play.example.test"},
    window: {addEventListener: (name, fn) => events.set(name, fn)},
    document: {hidden: false, addEventListener: (name, fn) => events.set(name, fn)},
    status: value => statuses.push(value),
    tableStatus: value => statuses.push(value),
    render: value => views.push(value),
    noteSnapshot: () => {},
    el: () => ready,
    setTimeout: (fn, ms) => setTimer(fn, ms, false),
    setInterval: (fn, ms) => setTimer(fn, ms, true),
    clearTimeout: id => timers.delete(id),
    clearInterval: id => timers.delete(id),
  };
  const harness =
    'let ws, seatToken, seatIndex=-1, snap=null, roomId="";' +
    'let reconnectTimer=null, heartbeatTimer=null;' +
    'let lastStateAt=0, heartbeatSentAt=0, socketOpenAt=0;' +
    'let sessionRevoked=false, intentionalClose=false;' +
    'const SYNC_INTERVAL_MS=45000, SYNC_TIMEOUT_MS=20000, RETRY_MAX_MS=30000;\n' +
    source +
    '\nglobalThis.testAPI={connect,recoverLiveSeat,state:()=>({roomId,seatToken,sessionRevoked,hasHeartbeat:heartbeatTimer!==null}),' +
    'leave:()=>{intentionalClose=true;stopTransportTimers();ws?.close(1000)}}';
  vm.runInNewContext(harness, context, {filename: "client-transport-simulator.js"});
  return {api: context.testAPI, advance, sockets, events, statuses, views, timers};
}

const sampleState = {type: "room_state", room_id: "ABCD", version: 1, players: []};

test("recovers original room and token after more than five disconnects", () => {
  const h = setup();
  h.api.connect("ABCD", "secret-seat");
  for (let n = 0; n < 8; n++) {
    h.sockets.at(-1).close(1006);
    h.advance(31000);
    assert.equal(h.sockets.length, n + 2);
    assert.equal(h.api.state().roomId, "ABCD");
    assert.equal(h.api.state().seatToken, "secret-seat");
  }
  h.sockets.at(-1).open();
  assert.deepEqual(JSON.parse(JSON.stringify(h.sockets.at(-1).sent[0])), {type: "auth", token: "secret-seat"});
  assert.ok(h.sockets.every(s => s.url.endsWith("/ws/ABCD")));
});

test("silent connected socket requests read-only sync and then reconnects", () => {
  const h = setup();
  h.api.connect("ABCD", "token");
  const old = h.sockets[0];
  old.open();
  old.emit(sampleState);
  h.advance(50000);
  assert.ok(old.sent.some(x => x.type === "sync"));
  assert.ok(old.sent.every(x => ["auth", "sync"].includes(x.type)));
  h.advance(25000);
  assert.equal(old.readyState, 3);
  h.advance(1000);
  assert.equal(h.sockets.length, 2);
  h.sockets[1].open();
  assert.equal(h.sockets[1].sent[0].token, "token");
});

test("socket open without authentication response triggers retry", () => {
  const h = setup();
  h.api.connect("ABCD", "token");
  h.sockets[0].open();
  h.advance(26000);
  assert.equal(h.sockets[0].readyState, 3);
  h.advance(1000);
  assert.equal(h.sockets.length, 2);
});

test("1008 refusal never retries even after browser focus or online event", () => {
  const h = setup();
  h.api.connect("ABCD", "invalid");
  h.sockets[0].open();
  h.sockets[0].close(1008);
  h.advance(200000);
  h.events.get("focus")();
  h.events.get("online")();
  assert.equal(h.api.state().sessionRevoked, true);
  assert.equal(h.sockets.length, 1);
  assert.equal(h.api.state().hasHeartbeat, false);
});

test("visibility/focus uses sync while connected, same-seat reauth after close", () => {
  const h = setup();
  h.api.connect("ABCD", "original");
  h.sockets[0].open();
  h.sockets[0].emit(sampleState);
  h.events.get("focus")();
  assert.equal(h.sockets.length, 1);
  assert.equal(h.sockets[0].sent.at(-1).type, "sync");
  h.sockets[0].emit(sampleState);
  h.sockets[0].close(1006);
  h.events.get("online")();
  assert.equal(h.sockets.length, 2);
  h.sockets[1].open();
  assert.equal(h.sockets[1].sent[0].token, "original");
  h.api.leave();
  h.advance(200000);
  assert.equal(h.sockets.length, 2);
});
