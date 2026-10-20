"use strict";

/* Shithead — mobile client.
   The transport half (seat tokens, reconnect, version guarding, request ids)
   is carried over unchanged from the working preview; only the rendering and
   the input model are new. Session credentials stay in this tab, never in a URL. */

const el = id => document.getElementById(id);
const KEY = "shithead-local-seat-v1";

let ws, seatToken, seatIndex = -1, snap = null, roomId = "", reconnects = 0;
let selection = new Set();        // indices inside the live zone
let targetSeat = null;            // chosen opponent for 3 / Joker and counters
let intentionalClose = false;

const roomCode = value => (value || "").trim().toUpperCase();
function status(message) { el("status").textContent = message; }
function tableStatus(message) { el("table-status").textContent = message; }

let screenBeforeRules = "screen-home";
function show(screen) {
  ["screen-home", "screen-lobby", "screen-table", "screen-rules"].forEach(id =>
    el(id).classList.toggle("hidden", id !== screen));
}
function openRules() {
  screenBeforeRules = ["screen-home", "screen-lobby", "screen-table"]
    .find(id => !el(id).classList.contains("hidden")) || "screen-home";
  show("screen-rules");
  window.scrollTo(0, 0);
}

/* ------------------------------------------------------------- seat store */
function loadSeat() {
  try {
    const s = JSON.parse(sessionStorage.getItem(KEY) || "null");
    if (s && typeof s.room === "string" && typeof s.token === "string"
        && typeof s.seat === "number") return s;
  } catch (_) { /* storage may be blocked */ }
  return null;
}
function saveSeat(room, token, seat, name) {
  try { sessionStorage.setItem(KEY, JSON.stringify({ room, token, seat, name })); }
  catch (_) { status("Browser session storage blocked; do not refresh during the match."); }
}

/* ----------------------------------------------------------- card drawing */
const SUIT_GLYPH = { S: "♠", H: "♥", D: "♦", C: "♣" };
const RANK_LABEL = { 11: "J", 12: "Q", 13: "K", 14: "A" };
const isRed = suit => suit === "H" || suit === "D";

function rankText(card) {
  return card.rank === 0 ? "JOKER" : (RANK_LABEL[card.rank] || String(card.rank));
}
function cardEl(card, small) {
  const d = document.createElement("div");
  d.className = "card " + (small ? "sm " : "") +
    (card.rank === 0 ? "joker black" : (isRed(card.suit) ? "red" : "black"));
  if (card.rank === 0) {
    d.innerHTML = '<div class="centre">JO<br>KER</div>';
    return d;
  }
  const glyph = SUIT_GLYPH[card.suit] || "";
  const label = rankText(card);
  d.innerHTML =
    '<div class="corner tl">' + label + "<small>" + glyph + "</small></div>" +
    '<div class="centre">' + label + "</div>" +
    '<div class="corner br">' + label + "<small>" + glyph + "</small></div>";
  return d;
}
function backEl() {
  const d = document.createElement("div");
  d.className = "card-back";
  return d;
}
function miniBack() {
  const d = document.createElement("div");
  d.className = "mini back";
  return d;
}
function initial(name) { return (name || "?").trim().charAt(0).toUpperCase() || "?"; }

/* ------------------------------------------------------------ room render */
function render(x) {
  if (!x || x.type !== "room_state") return;
  if (snap && snap.room_id === x.room_id && x.version < snap.version) return;
  snap = x;
  if (typeof x.you === "number") seatIndex = x.you;
  roomId = x.room_id;

  const reading = !el("screen-rules").classList.contains("hidden");
  if (x.game) { if (!reading) show("screen-table"); renderGame(x.game); return; }

  if (!reading) show("screen-lobby");
  el("room-label").textContent = x.room_id;
  const ul = el("players");
  ul.replaceChildren();
  x.players.forEach((p, i) => {
    const li = document.createElement("li");
    const av = document.createElement("div");
    av.className = "avatar";
    av.textContent = initial(p.name);
    const nm = document.createElement("div");
    nm.className = "seat-name";
    nm.textContent = p.name + (i === seatIndex ? " (you)" : "");
    const pill = document.createElement("span");
    if (!p.connected) { pill.className = "pill off"; pill.textContent = "Offline"; }
    else if (p.ready) { pill.className = "pill ready"; pill.textContent = "Ready"; }
    else { pill.className = "pill waiting"; pill.textContent = "Waiting"; }
    li.append(av, nm, pill);
    ul.appendChild(li);
  });
  el("phase").textContent = x.all_ready
    ? "All players ready"
    : x.players.length + " of " + x.capacity + " seated";
  const canReady = !!(ws && ws.readyState === WebSocket.OPEN && seatIndex >= 0);
  el("ready").disabled = !canReady;
  el("ready").textContent = x.players[seatIndex]?.ready ? "Not ready" : "Ready";
}

/* ----------------------------------------------------------- table render */
function sendGame(kind, fields = {}) {
  if (!snap || !ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({
    type: "game", kind, expected_version: snap.version,
    request_id: crypto.randomUUID(), ...fields
  }));
}

function renderOpponents(g) {
  const wrap = el("opponents");
  wrap.replaceChildren();
  const names = snap?.players || [];
  g.players.forEach(p => {
    if (p.seat === seatIndex) return;
    const box = document.createElement("div");
    box.className = "opp" + (p.seat === g.actor ? " is-turn" : "") + (p.finished ? " done" : "");

    const head = document.createElement("div");
    head.className = "opp-head";
    const av = document.createElement("div");
    av.className = "avatar";
    av.textContent = initial(names[p.seat]?.name);
    const nm = document.createElement("div");
    nm.className = "opp-name";
    nm.textContent = names[p.seat]?.name || ("Seat " + (p.seat + 1));
    head.append(av, nm);

    const zones = document.createElement("div");
    zones.className = "opp-zones";

    const hand = document.createElement("div");
    hand.className = "mini-stack";
    hand.appendChild(miniBack());
    const hb = document.createElement("span");
    hb.className = "count-badge";
    hb.textContent = p.hand_count;
    hand.appendChild(hb);
    zones.appendChild(hand);

    p.face_up.forEach(c => zones.appendChild(cardEl(c, true)));

    if (p.face_down_count > 0) {
      const down = document.createElement("div");
      down.className = "mini-stack";
      down.appendChild(miniBack());
      const db = document.createElement("span");
      db.className = "count-badge";
      db.textContent = p.face_down_count;
      down.appendChild(db);
      zones.appendChild(down);
    }

    const tag = document.createElement("div");
    tag.className = "zone-tag";
    tag.textContent = p.finished ? "Finished" : (p.hand_count + " in hand");

    box.append(head, zones, tag);

    // Targeting: tap an opponent instead of using a dropdown.
    const canTarget = !p.finished && p.seat !== seatIndex;
    if (canTarget) {
      box.classList.add("targetable");
      if (targetSeat === p.seat) box.classList.add("targeted");
      box.onclick = () => {
        targetSeat = targetSeat === p.seat ? null : p.seat;
        renderOpponents(g);
      };
    }
    wrap.appendChild(box);
  });
}

function renderZone(holder, cards, live, zoneName, faceDownCount) {
  holder.replaceChildren();
  const list = zoneName === "face_down"
    ? Array(faceDownCount || 0).fill(null)
    : (cards || []);
  list.forEach((card, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pick";
    btn.setAttribute("aria-pressed", "false");
    btn.appendChild(card ? cardEl(card) : backEl());
    btn.setAttribute("aria-label", card ? rankText(card) + " " + (card.suit || "") : "Face-down card " + (i + 1));
    btn.disabled = !live;
    if (live) {
      btn.onclick = () => {
        if (selection.has(i)) selection.delete(i); else selection.add(i);
        btn.setAttribute("aria-pressed", selection.has(i) ? "true" : "false");
      };
    }
    holder.appendChild(btn);
  });
}

function renderGame(g) {
  selection = new Set();
  const me = g.players[seatIndex];
  const mine = g.actor === seatIndex;
  const pending = g.phase === "PILE_PASS_DECISION";
  const over = g.phase === "FINISHED";

  el("table-room").textContent = roomId;
  renderOpponents(g);

  // turn banner
  const banner = el("turn-banner");
  banner.classList.toggle("mine", mine && !over);
  banner.classList.toggle("over", over);
  if (over) {
    banner.textContent = g.loser === seatIndex ? "You are the Shithead" : "Seat " + (g.loser + 1) + " is the Shithead";
  } else if (mine) {
    banner.textContent = pending ? "Pile coming your way" : "Your turn";
  } else {
    const nm = snap?.players?.[g.actor]?.name || ("Seat " + (g.actor + 1));
    banner.textContent = nm + "’s turn";
  }

  // stock
  const deckSlot = el("deck-slot");
  deckSlot.replaceChildren();
  if (g.deck_count > 0) {
    const stack = document.createElement("div");
    stack.className = "mini-stack";
    stack.appendChild(backEl());
    const b = document.createElement("span");
    b.className = "count-badge";
    b.textContent = g.deck_count;
    stack.appendChild(b);
    deckSlot.appendChild(stack);
  } else {
    const empty = document.createElement("div");
    empty.className = "empty-slot";
    empty.textContent = "Empty";
    deckSlot.appendChild(empty);
  }
  el("deck-label").textContent = g.deck_count > 0 ? "Stock" : "Stock empty";

  // pile
  const playSlot = el("play-slot");
  playSlot.replaceChildren();
  if (g.pile.length > 0) {
    const stack = document.createElement("div");
    stack.className = "pile-stack";
    g.pile.slice(-3).forEach(c => stack.appendChild(cardEl(c)));
    playSlot.appendChild(stack);
  } else {
    const empty = document.createElement("div");
    empty.className = "empty-slot";
    empty.textContent = "Empty";
    playSlot.appendChild(empty);
  }
  el("pile-label").textContent = g.pile.length
    ? g.pile.length + " in pile" + (g.burned_count ? " · " + g.burned_count + " burned" : "")
    : "Pile";
  el("lock-badge").classList.toggle("hidden", !g.locked);

  // your three zones — only the live one accepts taps
  const zone = g.your_zone;
  renderZone(el("your-face-down"), null, mine && zone === "face_down" && !over, "face_down", me?.face_down_count);
  renderZone(el("your-face-up"), g.your_face_up, mine && zone === "face_up" && !over, "face_up");
  renderZone(el("your-hand"), g.hand, mine && zone === "hand" && !over, "hand");
  el("head-down").classList.toggle("live", zone === "face_down");
  el("head-up").classList.toggle("live", zone === "face_up");
  el("head-hand").classList.toggle("live", zone === "hand");
  el("head-down").textContent = "Face down" + (me?.face_down_count ? " (" + me.face_down_count + ")" : "");
  el("head-up").classList.toggle("hidden", !(g.your_face_up || []).length);
  el("your-face-up").classList.toggle("hidden", !(g.your_face_up || []).length);

  // hint
  el("action-hint").textContent = g.your_blind_power
    ? "Blind 3 or Joker revealed — tap a player to send the pile."
    : over ? "Match over."
    : mine ? (pending ? "Accept the pile, or counter with a 3 or Joker."
                      : "Tap a card to select, then Play. Pick up if you cannot go.")
    : "Waiting for the other player.";

  // actions — same enabling rules as the proven preview
  const playing = mine && !pending && !over;
  const visible = {
    "play-card": playing && zone !== "face_down" && !g.your_blind_power,
    "use-power": playing && (zone !== "face_down" || !!g.your_blind_power),
    "flip-card": playing && zone === "face_down" && !g.your_blind_power,
    "pickup":    playing && g.pile.length > 0 && !g.your_blind_power,
    "counter":   mine && pending && zone !== "face_down",
    "accept":    mine && pending
  };
  Object.entries(visible).forEach(([id, on]) => el(id).classList.toggle("hidden", !on));

  if (!mine) targetSeat = null;
}

/* --------------------------------------------------------------- actions */
el("play-card").onclick = () => sendGame("play", { indices: [...selection].sort((a, b) => a - b) });
el("use-power").onclick = () => sendGame("power", {
  index: [...selection][0] ?? null,
  indices: [...selection].sort((a, b) => a - b),
  target: targetSeat
});
el("flip-card").onclick = () => sendGame("flip", { index: [...selection][0] ?? 0 });
el("pickup").onclick = () => sendGame("pickup");
el("counter").onclick = () => sendGame("counter", {
  index: [...selection][0] ?? null,
  target: targetSeat
});
el("accept").onclick = () => sendGame("accept");

/* ------------------------------------------------------------- transport */
async function request(path, data) {
  const response = await fetch(path, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  const obj = await response.json();
  if (!response.ok) throw Error(typeof obj.detail === "string" ? obj.detail : "Request failed");
  return obj;
}

function connect(room, token, retry = 0) {
  if (ws) {
    ws.onclose = null;
    if (ws.readyState !== WebSocket.CLOSED) ws.close();
  }
  roomId = room; seatToken = token; snap = null;
  intentionalClose = false;
  const socket = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") +
    location.host + "/ws/" + encodeURIComponent(room));
  ws = socket;
  socket.onopen = () => {
    socket.send(JSON.stringify({ type: "auth", token }));
    status("Connected to room.");
    reconnects = 0;
  };
  socket.onmessage = message => {
    if (ws !== socket) return;
    let x;
    try { x = JSON.parse(message.data); }
    catch (_) { status("Invalid server response."); return; }
    if (x.type === "error") {
      if (x.stateSnapshot) render(x.stateSnapshot);
      const text = x.message || ("Action rejected: " + x.reasonCode);
      status(text); tableStatus(text);
    } else { render(x); tableStatus(""); }
  };
  socket.onclose = event => {
    if (ws !== socket) return;
    el("ready").disabled = true;
    if (event.code === 1008) {
      status("Room or seat credential no longer valid; start a new room if the server restarted.");
      return;
    }
    if (retry >= 5) {
      status("Connection lost. Refresh this tab to restore your existing seat.");
      tableStatus("Connection lost — refresh to rejoin.");
      return;
    }
    status("Disconnected; restoring the same seat…");
    tableStatus("Reconnecting…");
    const next = retry + 1;
    setTimeout(() => { if (ws === socket) connect(room, token, next); },
      Math.min(8000, 500 * Math.pow(2, next)));
  };
  socket.onerror = () => { status("Could not reach the server."); };
}

/* ------------------------------------------------------------ home flow */
el("go-create").onclick = () => {
  el("create-panel").classList.remove("hidden");
  el("join-panel").classList.add("hidden");
};
el("go-join").onclick = () => {
  el("join-panel").classList.remove("hidden");
  el("create-panel").classList.add("hidden");
};
el("go-rules").onclick = openRules;
el("table-rules").onclick = openRules;
el("rules-back").onclick = () => show(screenBeforeRules);

// One press: open the room and take the host's seat in the same request.
el("create").onclick = async () => {
  const name = el("name").value.trim();
  if (!name) { status("Enter your name first."); el("name").focus(); return; }
  try {
    const r = await request("/api/rooms", { capacity: Number(el("capacity").value), name });
    el("room").value = r.room_id;
    seatIndex = r.seat;
    saveSeat(r.room_id, r.token, r.seat, name);
    connect(r.room_id, r.token);
    status("Room " + r.room_id + " created — share the code.");
  } catch (e) { status(e.message); }
};

el("join").onclick = async () => {
  try {
    // Codes are issued uppercase, so a typed code is matched case-insensitively.
    const room = roomCode(el("room").value), name = el("name").value.trim();
    if (!room || !name) { status("Enter your name and the room code."); return; }
    const saved = loadSeat();
    if (saved?.room === room) { seatIndex = saved.seat; connect(room, saved.token); return; }
    const r = await request("/api/rooms/" + encodeURIComponent(room) + "/join", { name });
    seatIndex = r.seat;
    saveSeat(room, r.token, r.seat, name);
    connect(room, r.token);
  } catch (e) { status(e.message); }
};

el("ready").onclick = () => {
  if (!snap || !ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({
    type: "ready", ready: !snap.players[seatIndex]?.ready,
    expected_version: snap.version, request_id: crypto.randomUUID()
  }));
};

el("copy-code").onclick = async () => {
  try { await navigator.clipboard.writeText(roomId); el("lobby-status").textContent = "Code copied."; }
  catch (_) { el("lobby-status").textContent = "Code: " + roomId; }
};

/* Refresh and network reconnect use the original seat token, not a second join. */
const saved = loadSeat();
if (saved) {
  el("room").value = saved.room;
  el("name").value = saved.name || "Player";
  seatIndex = saved.seat;
  connect(saved.room, saved.token);
}
