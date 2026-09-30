# Phones and tablets (Safari, Chrome, home-screen apps)

The gateway's web console and the five browser apps (Code, Flow Editor, Observer, Continuum,
Entity) work on phones, tablets and windows of any size. A phone is a thin client: the gateway's
computer runs the models, the tools and the durable runs; the phone shows them and sends commands.

## One address for everything

The gateway serves the console at `/console` and every installed app at `/apps/<app>/` on its own
address, so a phone needs only that one address. There is no separate app server to run and no
browser origin to allow.

1. **Let the phone reach the gateway.** The gateway listens on its own computer only until you
   change its Network setting: `abstractgateway network set lan`, the console's **Network** tab or
   the menu-bar icon, then restart the gateway when asked (`abstractgateway network restart`). User
   accounts stay on. `abstractgateway network addresses` lists the addresses to use.
2. **Install the apps** you want from the console's **Apps** page, signed in as an administrator
   on the gateway's own computer (installs from another device need an administrator to allow them
   first, with the `allow_engine_install` setting).
3. **Open the console on the phone**, for example `http://192.168.1.20:8080/console`, and sign in
   with your gateway user name and token, or with **Email me a sign-in code** when your account has
   email set up ([Email integration](email-integration.md#sign-in-by-email)). The one-time claim
   link only works on the gateway's own computer.
4. **Open an app** from the Apps page. It opens at `/apps/<app>/`, already signed in.
5. Optional: add the page to the home screen (Safari: **Share → Add to Home Screen**).

For access from outside your network, put the gateway behind a reverse proxy with HTTPS (one proxy
block covers the console, the API and every app), or choose the `internet` Network setting (no
HTTPS; you handle port forwarding). See
[Gateway exposure security](gateway-security.md) and
[AbstractGateway: Deployment](https://github.com/lpalbou/AbstractGateway/blob/main/docs/deployment.md).

## What adapts on a small screen

- Sidebars and side panels become drawers below 1024 px wide; Escape, a tap outside or the close
  button closes them.
- Dialogs open as bottom sheets on phones (below 768 px wide, or in landscape under 500 px tall),
  with their buttons always visible.
- Touch screens get 44 px targets and 16 px form fields, so iOS does not zoom when you focus a
  field.
- Pages respect the notch and home-indicator areas.

Each app's changelog describes its own layout (for example, AbstractCode's composer and the
Observer's one-pane run view on phones).

## Limits

- The phone does not run tools or models; files are the gateway computer's files.
- Mobile browsers suspend background tabs. Runs keep going on the gateway, and the page catches up by
  replaying the ledger when you return.
