# Scenario: Phone thin client

Goal: follow and steer your agents from a phone or a tablet while the gateway's computer runs the
models, the tools and the durable runs.

This is useful for:
- checking on long coding or research sessions away from your desk;
- answering tool approvals and questions from an automation;
- reading automation results as conversations.

## Mental model (thin client)

- The phone does not run the runtime.
- It renders by replaying and streaming the ledger.
- It acts by sending durable commands (resume, pause, cancel, answers to waits).

## Quickstart (local network)

1. On the gateway's computer, let other devices reach it (user accounts stay on):

   ```bash
   abstractgateway network set lan
   abstractgateway network restart --token <admin token>
   abstractgateway network addresses     # the addresses to open on the phone
   ```

2. Install the apps you want from the console's **Apps** page, on the gateway's own computer.
3. On the phone, open `http://<address>:8080/console` and sign in with your gateway user name and
   token (or **Forgot your token? Email me a sign-in code**).
4. Open Code, Observer or another app from the Apps page: it opens at `/apps/<app>/` on the same
   address, already signed in. The console and every app adapt to the phone's screen.

## Away from home

With Tailscale on the gateway's computer and the phone, run
`tailscale serve --bg http://127.0.0.1:<port>` on the gateway's computer and open
`https://<host>.<tailnet>.ts.net/console` on the phone (`tailscale serve reset` undoes it). The
gateway can keep its `localhost` Network setting, and voice and camera work because the page is
https. Or put the gateway behind a reverse proxy with HTTPS: one proxy block covers the console,
the API and every app at `/apps/<app>/`. See
[Phones and tablets: Reached through Tailscale](../guide/deployment-iphone.md#reached-through-tailscale-https). A home-screen app (Safari: **Share → Add to Home Screen**) then opens
the same address.

## Deeper guides

- [Guide: Phones and tablets](../guide/deployment-iphone.md)
- [Guide: Web deployment](../guide/deployment-web.md)
- [Guide: Gateway exposure security](../guide/gateway-security.md)
