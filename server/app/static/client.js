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
let chosenGame = "shithead";
let lastReactionSeq = 0;
let reactionTimer = null;
const REACTIONS = ["😂", "😏", "😭", "👀", "🔥", "💀"];

const roomCode = value => (value || "").trim().toUpperCase();
function status(message) { el("status").textContent = message; }
function namedGameEvent(message) {
  // UI-only: authoritative engine events and hidden state remain unchanged.
  return String(message || "").replace(/Player ([1-6])\b/g, (original, seat) =>
    snap?.players?.[Number(seat)-1]?.name || original);
}

function tableStatus(message) {
  el("table-status").textContent = message;
  el("ludo-status").textContent = message;
  el("awale-status").textContent = message;
  el("dara-status").textContent = message;
  el("yote-status").textContent = message;
  el("domino-status").textContent = message;
}

let screenBeforeRules = "screen-home";
function show(screen) {
  ["screen-home", "screen-lobby", "screen-table", "screen-ludo", "screen-awale", "screen-dara", "screen-yote", "screen-dominoes", "screen-dominoes-rules", "screen-rules", "screen-ludo-rules", "screen-awale-rules", "screen-dara-rules"].forEach(id =>
    el(id).classList.toggle("hidden", id !== screen));
}
function openRules() {
  screenBeforeRules = ["screen-home", "screen-lobby", "screen-table", "screen-ludo", "screen-awale", "screen-dara", "screen-yote", "screen-dominoes"]
    .find(id => !el(id).classList.contains("hidden")) || "screen-home";
  const game = screenBeforeRules === "screen-home" ? chosenGame : snap?.game_type;
  show(game === "dominoes" ? "screen-dominoes-rules" : game === "yote" ? "screen-yote-rules" : game === "dara" ? "screen-dara-rules" : game === "awale" ? "screen-awale-rules" : game === "ludo" ? "screen-ludo-rules" : "screen-rules");
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
  // A reaction, reconnect, or late join may refresh room metadata while the
  // authoritative game stays unchanged. Keep selected cards in that case.
  if (!snap || snap.room_id !== x.room_id ||
      JSON.stringify(snap.game) !== JSON.stringify(x.game)) {
    selection.clear();
  }
  snap = x;
  if (typeof x.you === "number") seatIndex = x.you;
  roomId = x.room_id;
  const isLudo = x.game_type === "ludo";
  const isAwale = x.game_type === "awale";
  const isDara = x.game_type === "dara";
  const isYote = x.game_type === "yote";
  const isDominoes = x.game_type === "dominoes";
  const hostPrompt = el("host-join-prompt");
  const lateNames = (x.pending_joiners || [])
    .map(i => x.players?.[i]?.name || "A player");
  hostPrompt.classList.toggle("hidden",
    x.you !== x.host_seat || lateNames.length === 0 || !x.game ||
    x.game.phase === "FINISHED");
  el("host-join-names").textContent = lateNames.join(", ") +
    (lateNames.length === 1 ? " has joined." : " have joined.");
  if (x.reaction && x.reaction.seq > lastReactionSeq) {
    lastReactionSeq = x.reaction.seq;
    const nm = x.players[x.reaction.seat]?.name || "Player";
    const toast = el("reaction-toast");
    toast.textContent = nm + "  " + x.reaction.emoji;
    toast.classList.remove("hidden");
    if (reactionTimer) clearTimeout(reactionTimer);
    reactionTimer = setTimeout(() => toast.classList.add("hidden"), 2400);
  }

  const reading = !el("screen-rules").classList.contains("hidden") || !el("screen-ludo-rules").classList.contains("hidden") || !el("screen-awale-rules").classList.contains("hidden") || !el("screen-dara-rules").classList.contains("hidden") || !el("screen-yote-rules").classList.contains("hidden") || !el("screen-dominoes-rules").classList.contains("hidden");
  if (x.game) {
    if (!reading) show(isDominoes ? "screen-dominoes" : isYote ? "screen-yote" : isDara ? "screen-dara" : isAwale ? "screen-awale" : isLudo ? "screen-ludo" : "screen-table");
    if (isDominoes) renderDominoes(x.game);
    else if (isYote) renderYote(x.game);
    else if (isDara) renderDara(x.game);
    else if (isAwale) renderAwale(x.game);
    else if (isLudo) {
      el("ludo-room").textContent = x.room_id;
      renderLudo(x.game);
    } else renderGame(x.game);
    return;
  }

  if (!reading) show("screen-lobby");
  el("room-label").textContent = x.room_id;
  el("lobby-game-label").textContent = "Selected game: " + (isDominoes ? "Jamaican Dominoes" : isYote ? "Yoté" : isDara ? "Dara" : isAwale ? "Awalé" : isLudo ? "Ludo" : "Shithead");
  el("lobby-switch").classList.toggle("hidden", seatIndex !== x.host_seat);
  el("lobby-game").value = x.game_type || "shithead";
  el("domino-lobby-options").classList.toggle("hidden", !isDominoes || seatIndex !== x.host_seat);
  el("lobby-domino-mode").value = x.domino_mode || "partner";
  const limit = isAwale || isDara || isYote ? 2 : isLudo || isDominoes ? 4 : 6;
  const picker = el("lobby-capacity");
  // Ludo and Dominoes both allow four players, but Ludo offers 2–4 while
  // Dominoes requires exactly four. Rebuild if the actual options differ.
  const capacityChoices = Array.from({length:isDominoes?1:limit-1},(_,i)=>String(i+(isDominoes?4:2)));
  if (picker.options.length !== capacityChoices.length ||
      capacityChoices.some((value,i)=>picker.options[i]?.value!==value)) {
    picker.replaceChildren(...capacityChoices.map(value=>{
      const o=document.createElement("option");o.value=value;o.textContent=value;return o;
    }));
  }
  picker.value=String(x.capacity);
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
  if (isDominoes && x.domino_mode !== "cutthroat") {
    const teamText = [0,1].map(t => "Team "+(t+1)+": "+[t,t+2].map(i=>x.players[i]?.name||"Waiting for partner").join(" & ")).join("  |  ");
    el("lobby-game-label").textContent = "Jamaican Dominoes · "+teamText;
  }
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

function renderZone(holder, cards, live, zoneName, faceDownCount, sourceIndices = null) {
  holder.replaceChildren();
  const list = zoneName === "face_down"
    ? Array(faceDownCount || 0).fill(null)
    : (cards || []);
  list.forEach((card, i) => {
    const serverIndex = sourceIndices ? sourceIndices[i] : i;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pick";
    btn.setAttribute("aria-pressed", selection.has(serverIndex) ? "true" : "false");
    btn.appendChild(card ? cardEl(card) : backEl());
    btn.setAttribute("aria-label", card ? rankText(card) + " " + (card.suit || "") : "Face-down card " + (i + 1));
    btn.disabled = !live;
    if (live) {
      btn.onclick = () => {
        if (selection.has(serverIndex)) selection.delete(serverIndex);
        else selection.add(serverIndex);
        btn.setAttribute("aria-pressed", selection.has(serverIndex) ? "true" : "false");
      };
    }
    holder.appendChild(btn);
  });
}

function renderGame(g) {
  const me = g.players[seatIndex];
  const spectator = !!g.is_spectator;
  const mine = !spectator && g.actor === seatIndex;
  const pending = g.phase === "PILE_PASS_DECISION";
  const choosingDraw = g.refill_choice && mine;
  const over = g.phase === "FINISHED";

  el("table-room").textContent = roomId;
  renderOpponents(g);

  // turn banner
  const banner = el("turn-banner");
  banner.classList.toggle("mine", mine && !over);
  banner.classList.toggle("over", over);
  if (spectator && !over) {
    banner.textContent = "Waiting for the next game";
  } else if (over) {
    const loserName = snap?.players?.[g.loser]?.name || ("Seat " + (g.loser + 1));
    banner.textContent = g.loser === seatIndex ? "You are the Shithead!" : loserName + " is the Shithead!";
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
  // A revealed blind 3/Joker is already the committed card, so the remaining
  // face-down cards must not be selectable: any selection makes the server
  // refuse the power ("a blind power is exactly one committed card").
  renderZone(el("your-face-down"), null,
             mine && zone === "face_down" && !over && !g.your_blind_power,
             "face_down", me?.face_down_count);
  renderZone(el("your-face-up"), g.your_face_up, mine && zone === "face_up" && !over, "face_up");
  // Sort for display without changing the server-owned hand indices.
  const sortedHand = (g.hand || []).map((card, index) => ({card, index}))
    .sort((a, b) => (a.card.rank === 0 ? 15 : a.card.rank) -
                     (b.card.rank === 0 ? 15 : b.card.rank) || a.index - b.index);
  renderZone(el("your-hand"), sortedHand.map(x => x.card),
             mine && zone === "hand" && !over, "hand", null,
             sortedHand.map(x => x.index));
  if (choosingDraw) {
    const allowed = new Set(g.your_refill_indices || []);
    el("your-hand").querySelectorAll(".pick").forEach((btn, i) => {
      const serverIndex = sortedHand[i].index;
      btn.disabled = !allowed.has(serverIndex);
      if (allowed.has(serverIndex)) btn.classList.add("drawn-option");
    });
  }
  el("head-down").classList.toggle("live", zone === "face_down");
  el("head-up").classList.toggle("live", zone === "face_up");
  el("head-hand").classList.toggle("live", zone === "hand");
  el("head-down").textContent = "Face down" + (me?.face_down_count ? " (" + me.face_down_count + ")" : "");
  el("head-up").classList.toggle("hidden", !(g.your_face_up || []).length);
  el("your-face-up").classList.toggle("hidden", !(g.your_face_up || []).length);

  // hint
  el("finished-actions").classList.toggle("hidden", !over);
  el("shithead-switch").classList.toggle("hidden", !(over && seatIndex === snap.host_seat));
  el("rematch").disabled = !over || (snap.rematch_votes || []).includes(seatIndex);
  el("rematch").textContent = (snap.rematch_votes || []).includes(seatIndex)
    ? "Waiting for others (" + snap.rematch_votes.length + "/" + snap.players.length + ")"
    : "Play again in this room";
  el("reaction-actions").classList.toggle("hidden", over);
  el("action-hint").textContent = g.your_blind_power
    ? "Blind 3 or Joker revealed — tap a player to send the pile."
    : over ? "Match over."
    : spectator ? "You're in the room! You will play in the next round unless the host restarts now."
    : mine ? (pending ? "Accept the pile, or counter with a 3 or Joker."
                      : choosingDraw ? "Matching card drawn! Play it now, or keep it for later."
                      : "Tap a card to Play, or choose Pick Up to collect the pile.")
    : "Waiting for the other player.";

  // actions — same enabling rules as the proven preview
  const playing = mine && !pending && !over && !choosingDraw;
  const visible = {
    "play-card": playing && zone !== "face_down" && !g.your_blind_power,
    "use-power": playing && (zone !== "face_down" || !!g.your_blind_power),
    "flip-card": playing && zone === "face_down" && !g.your_blind_power,
    "pickup":    playing && zone !== "face_down" && g.pile.length > 0 && !g.your_blind_power,
    "play-drawn": choosingDraw,
    "keep-drawn": choosingDraw,
    "counter":   mine && pending && zone !== "face_down",
    "accept":    mine && pending
  };
  Object.entries(visible).forEach(([id, on]) => el(id).classList.toggle("hidden", !on));

  if (!mine) targetSeat = null;
}

/* --------------------------------------------------------------- actions */
el("play-card").onclick = () => sendGame("play", { indices: [...selection].sort((a, b) => a - b) });
/* A 3/Joker is the only action that needs a chosen opponent, so the common way
   to "freeze" the game was to press these with nothing chosen and get a refusal
   back with no idea what was missing. Say what is missing instead of sending a
   request that cannot succeed. */
function powerPrerequisite(g, needCard) {
  if (!g) return "Waiting for the table.";
  if (needCard && !g.your_blind_power && selection.size === 0)
    return "Tap the 3 or Joker you want to use.";
  if (g.pile.length > 0 && targetSeat === null)
    return "Tap the player you are sending the pile to.";
  return null;
}

el("use-power").onclick = () => {
  const g = snap?.game;
  const missing = powerPrerequisite(g, true);
  if (missing) { tableStatus(missing); return; }
  sendGame("power", {
    index: [...selection][0] ?? null,
    indices: [...selection].sort((a, b) => a - b),
    target: targetSeat
  });
};
el("flip-card").onclick = () => sendGame("flip", { index: [...selection][0] ?? 0 });
el("pickup").onclick = () => sendGame("pickup");
el("play-drawn").onclick = () => {
  const allowed = new Set(snap?.game?.your_refill_indices || []);
  const chosen = [...selection].sort((a, b) => a - b);
  if (!chosen.length || chosen.some(i => !allowed.has(i))) {
    tableStatus("Select a newly drawn matching card."); return;
  }
  sendGame("play_drawn", { indices: chosen });
};
el("keep-drawn").onclick = () => sendGame("keep_drawn");
el("counter").onclick = () => {
  if (selection.size === 0) {
    tableStatus("Tap the 3 or Joker you want to counter with."); return;
  }
  if (targetSeat === null) {
    tableStatus("Tap the player you are sending the pile to."); return;
  }
  sendGame("counter", {
    index: [...selection][0] ?? null,
    target: targetSeat
  });
};
el("accept").onclick = () => sendGame("accept");

function sendRoomAction(type, fields = {}) {
  if (!snap || !ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({
    type, ...fields, expected_version: snap.version, request_id: crypto.randomUUID()
  }));
}
el("rematch").onclick = () => sendRoomAction("rematch");
el("shithead-switch").onclick = () => sendRoomAction("return_lobby");
el("host-restart").onclick = () => sendRoomAction("host_join_decision", {decision: "restart_now"});
el("host-finish").onclick = () => sendRoomAction("host_join_decision", {decision: "finish_current"});
el("main-menu").onclick = () => {
  // Leaving the table does not delete a room or change another player's game.
  intentionalClose = true;
  if (ws) { ws.onclose = null; ws.close(); ws = null; }
  sessionStorage.removeItem(KEY);
  seatToken = null; seatIndex = -1; roomId = ""; snap = null;
  selection.clear(); targetSeat = null;
  show("screen-home");
  status("You left the finished room. Create or join a new one.");
};
el("reaction-actions").replaceChildren(...REACTIONS.map(emoji => {
  const btn = document.createElement("button");
  btn.type = "button"; btn.textContent = emoji; btn.title = "Send " + emoji;
  btn.onclick = () => sendRoomAction("reaction", {emoji});
  return btn;
}));

/* ------------------------------------------------------------- transport */
async function request(path, data) {
  const response = await fetch(path, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  const obj = await response.json();
  if (!response.ok) {
    if (response.status === 503 && obj.detail?.code === "room_capacity_reached") {
      const detail=obj.detail;
      const error=new Error("All "+detail.room_limit+" room slots are allocated. New rooms are temporarily unavailable. Try again in around 5 minutes (availability not guaranteed). You can still join an existing room using its code.");
      error.code="room_capacity_reached";
      error.roomLimit=detail.room_limit;
      error.roomsAllocated=detail.rooms_allocated;
      throw error;
    }
    throw Error(typeof obj.detail === "string" ? obj.detail : "Request failed");
  }
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
      noteSnapshot(false, text);
    } else { render(x); tableStatus(""); noteSnapshot(true); }
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
function selectHomeGame(game) {
  chosenGame = game;
  document.querySelectorAll(".game-choice").forEach(button => {
    const active = button.dataset.game === game;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  el("domino-home-options").classList.toggle("hidden", game!=="dominoes");
  const capacity = el("capacity");
  const oldValue = Number(capacity.value);
  capacity.replaceChildren(...Array.from({length:((game==="awale"||game==="dara"||game==="yote"||game==="dominoes")?1:game==="ludo"?3:5)},(_,i)=>{
    const option=document.createElement("option"); option.value=String(i+(game==="dominoes"?4:2));
    option.textContent=option.value;return option;
  }));
  capacity.value=String(((game==="awale"||game==="dara"||game==="yote")?2:game==="dominoes"?4:Math.min(oldValue,game==="ludo"?4:6)));
}
document.querySelectorAll(".game-choice").forEach(btn=>{
  btn.onclick=()=>selectHomeGame(btn.dataset.game);
});
el("switch-game").onclick=()=>sendRoomAction("select_game",{game_type:el("lobby-game").value});
el("set-domino-mode").onclick=()=>sendRoomAction("set_domino_mode",{domino_mode:el("lobby-domino-mode").value});
el("set-capacity").onclick=()=>sendRoomAction("set_capacity",{capacity:Number(el("lobby-capacity").value)});
el("ludo-switch").onclick=()=>sendRoomAction("return_lobby");
el("ludo-refresh").onclick=refreshGame;
el("ludo-open-rules").onclick=openRules;
el("ludo-rules-back").onclick=()=>show(screenBeforeRules);
selectHomeGame("shithead");

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

/* ------------------------------------------------- refresh / resynchronise
   A safe state resynchronisation, never a page reload and never a new seat.
   Connected: ask the server for a fresh authoritative snapshot over the
   existing socket ("sync" changes no state and bumps no version).
   Disconnected: reconnect with the saved room id and private seat token, which
   returns the player to the same seat with the match untouched. */
let pendingSync = null;

function endSync(ok, text) {
  if (!pendingSync) return;
  clearTimeout(pendingSync.timer);
  const btn = el("refresh-game");
  btn.disabled = false;
  btn.classList.remove("spinning");
  if (text) tableStatus(text);
  pendingSync = null;
}

function noteSnapshot(ok, errorText) {
  if (!pendingSync) return;
  // A refused action is still proof the server is answering us.
  endSync(ok, ok ? pendingSync.success : (errorText || pendingSync.success));
}

function awaitSnapshot(success, failure) {
  if (pendingSync) clearTimeout(pendingSync.timer);
  pendingSync = {
    success,
    timer: setTimeout(() => {
      const t = failure;
      pendingSync = null;
      const btn = el("refresh-game");
      btn.disabled = false;
      btn.classList.remove("spinning");
      tableStatus(t);
    }, 6000),
  };
}

function refreshGame() {
  const btn = el("refresh-game");
  if (btn.disabled) return;
  const saved = loadSeat();
  const room = saved?.room || roomId;
  const token = saved?.token || seatToken;
  if (!room || !token) {
    // Be honest: nothing was lost on the server, this device just cannot prove
    // which seat is ours.
    tableStatus("This device no longer has your seat credentials. "
                + "Rejoin with the room code to take your seat back.");
    return;
  }
  btn.disabled = true;
  btn.classList.add("spinning");
  if (ws && ws.readyState === WebSocket.OPEN) {
    tableStatus("Refreshing game…");
    awaitSnapshot("Back in sync.",
                  "The server did not answer the refresh. Your match is still "
                  + "there — tap refresh again in a moment.");
    ws.send(JSON.stringify({ type: "sync" }));
  } else {
    tableStatus("Reconnecting to your game…");
    awaitSnapshot("Back in sync.",
                  "Could not reach the server. Your seat is still held — check "
                  + "your connection and tap refresh again.");
    connect(room, token);
  }
}

el("refresh-game").onclick = refreshGame;
el("rules-back").onclick = () => show(screenBeforeRules);

// One press: open the room and take the host's seat in the same request.
el("create").onclick = async () => {
  const name = el("name").value.trim();
  if (!name) { status("Enter your name first."); el("name").focus(); return; }
  try {
    const r = await request("/api/rooms", { capacity: Number(el("capacity").value), name, game_type: chosenGame,
      domino_mode: chosenGame==="dominoes" ? el("domino-home-mode").value : "partner" });
    el("room").value = r.room_id;
    seatIndex = r.seat;
    saveSeat(r.room_id, r.token, r.seat, name);
    connect(r.room_id, r.token);
    status("Room " + r.room_id + " created — share the code.");
  } catch (e) {
    if (e.code === "room_capacity_reached") {
      el("capacity-notice").classList.remove("hidden");
      el("capacity-message").textContent=e.message;
      status("Room creation is temporarily full; joining an existing room still works.");
    } else status(e.message);
  }
};

el("capacity-dismiss").onclick=()=>el("capacity-notice").classList.add("hidden");
el("capacity-join").onclick=()=>{
  el("capacity-notice").classList.add("hidden");
  el("join-panel").classList.remove("hidden");
  el("create-panel").classList.add("hidden");
  el("room").focus();
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
