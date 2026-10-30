"""Optional local browser QA. Requires Playwright + Chromium and a local server.
Run: python scripts/qa_ludo_browser.py [http://127.0.0.1:8765]
Uses only ordinary browser controls/protocol; never forces dice or game state.
"""
import sys
import os
import threading
import time
from pathlib import Path

# With no URL, start an isolated local server in this process.
if len(sys.argv) == 1:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import uvicorn
    from server.app.main import create_app
    config = uvicorn.Config(create_app(), host="127.0.0.1", port=8765, log_level="error")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(.05)
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765'
errors = []

def wait_version(p, version):
    p.wait_for_function('v => snap && snap.version > v', arg=version)

def click_action(p, selector):
    version = p.evaluate('snap.version')
    p.locator(selector).evaluate('(e)=>e.click()')
    wait_version(p, version)

with sync_playwright() as pw:
    browser = pw.chromium.launch(args=['--no-sandbox'])
    for n in (2, 3, 4):
        contexts = [browser.new_context(viewport={'width':390 if i % 2 == 0 else 1280,'height':844}, is_mobile=i%2==0, has_touch=i%2==0) for i in range(n)]
        pages = [c.new_page() for c in contexts]
        for i,p in enumerate(pages):
            p.on('pageerror', lambda e: errors.append(str(e)))
            p.goto(URL)
            p.wait_for_function('document.querySelector("#logo-slot").naturalWidth > 0')
            assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
            p.locator('#name').fill(f'Player {i+1}')
        host = pages[0]
        host.locator('[data-game=ludo]').click()
        host.locator('#go-rules').click()
        assert host.locator('#screen-ludo-rules').is_visible()
        host.locator('#ludo-rules-back').click()
        assert host.locator('#screen-home').is_visible()
        if n == 2:
            host.screenshot(path='/tmp/ludo-home-review.png', full_page=True)
        host.locator('#go-create').click()
        host.locator('#capacity').select_option(str(n))
        host.locator('#create').click()
        host.wait_for_function('snap && snap.phase === "LOBBY"')
        code = host.evaluate('roomId')
        for p in pages[1:]:
            p.locator('#go-join').click()
            p.locator('#room').fill(code)
            p.locator('#join').click()
            p.wait_for_function('snap && snap.phase === "LOBBY"')
        for i,p in enumerate(pages):
            p.wait_for_function('n => snap.players.length === n',arg=n)
            click_action(p,'#ready')
            for q in pages:
                q.wait_for_function('i => snap.players[i].ready',arg=i)
        for p in pages:
            p.wait_for_function('snap && snap.game && snap.game.game_type === "ludo"')
        assert host.locator('.ludo-token').count() == n*4
        assert host.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if n == 2:
            host.screenshot(path='/tmp/ludo-board-review.png',full_page=True)
        actions=0
        while True:
            state=host.evaluate('snap')
            if state['phase']=='FINISHED': break
            actor=state['game']['actor']; p=pages[actor]
            p.wait_for_function('v => snap.version >= v',arg=state['version'])
            if actions == 20:
                seat = p.evaluate('seatIndex')
                p.reload()
                p.wait_for_function('snap && snap.game')
                assert p.evaluate('seatIndex') == seat
            if actions == 30:
                p.evaluate('ws.onclose = null; ws.close()')
                p.wait_for_function('ws.readyState === WebSocket.CLOSED')
                p.locator('#ludo-refresh').click()
                p.wait_for_function('ws.readyState === WebSocket.OPEN && snap && !pendingSync')
                assert p.locator('#ludo-status').inner_text() == 'Back in sync.'
            if state['game']['turn_stage']=='ROLL':
                click_action(p,'#ludo-roll')
            else:
                click_action(p,'#ludo-move-options button:first-of-type')
            host.wait_for_function('v => snap.version > v',arg=state['version'])
            actions+=1
            assert actions<12000, 'Match did not finish'
        for p in pages:
            p.wait_for_function('snap.phase === "FINISHED"')
            assert 'wins Ludo!' in p.locator('#ludo-turn').inner_text()
        for p in pages:
            click_action(p,'#ludo-rematch')
            version=p.evaluate('snap.version')
            for q in pages: q.wait_for_function('v=>snap.version>=v',arg=version)
        assert host.evaluate('snap.phase')=='PLAYING'
        print(f'{n}-player full browser match: {actions} actions; reload, disconnected refresh, winner and unanimous rematch PASS',flush=True)
        for c in contexts: c.close()
    assert not errors, errors
    browser.close()
print('Browser JavaScript errors: 0',flush=True)
