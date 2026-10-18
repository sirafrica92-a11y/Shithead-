# Staging: play.shithead.games

The site is for invited testers only, NOT a public production launch.

Railway service: deploy branch deploy/railway-shithead-games-staging.
Railway needs one persistent volume mounted at /data, and service secret
SHITHEAD_TEST_PASSWORD of at least 16 characters. Never commit the password.
One Python worker, with Railway's PORT env var, FastAPI, and WebSockets.

Attach play.shithead.games as a custom domain. The domain registrar is
separate from the DNS host. Enter the DNS records Railway returns into
the authoritative DNS service. Railway provisions HTTPS automatically
once ownership and routing records are correct.

Verify:
1. The home page asks for the private test password.
2. API and static JS without the password return 401.
3. Two browser tabs join one room, Ready up, and play cards.
4. Refresh a tab and reconnect to the existing seat.
5. Restart the service and confirm match state survives via the /data volume.

This shared-password gate is suitable for limited trusted testers, not for
an unrestricted public audience. Real accounts, rate limiting, moderation,
multi-instance storage, and AFK policies remain production requirements.
