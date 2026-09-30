# Email integration

Two things carry the word "email" on an AbstractGateway, and every console names them the same way:

- your **email address**: where sign-in codes, "Forgot your token?" and notifications go, and the
  first address your agents may write to. It has no password. An administrator sets it in
  **Create user**, or you set it on your account page;
- your **mailbox**: a connection you make (Google or Microsoft sign-in, or address and password for
  other providers) so that your agents and automations can read and send mail as you. Only you
  connect it; administrators never see or touch it.

Every signed-in person can connect **their own** mailbox. It is used for three things:

- **automations on new mail**: the **When an email arrives** trigger (`email.received@1`);
- **email notifications**: **Job failed** and **Approval needed**, plus the results of automations
  set to **Email me the result**, sent through your own mailbox to your own email address;
- **sign-in by email**: **Forgot your token? Email me a sign-in code** on the gateway's sign-in
  page.

Email is configured as settings in the consoles, never through environment variables. Nothing reads
your mail until you create an email automation, nothing is sent until your mailbox is connected,
and agents get no email tools until you switch **Agent email tools** on.

The package guides hold the full references:

| Topic | Reference |
|---|---|
| Your email address and mailbox, notifications, sign-in by email, what administrators decide, where things are stored | [AbstractGateway: Email](https://github.com/lpalbou/AbstractGateway/blob/main/docs/email.md) |
| The `email.received@1` trigger, the event inbox, sending without asking, mail sent by automations | [AbstractRuntime: Email](https://github.com/lpalbou/AbstractRuntime/blob/main/docs/email.md) |
| The account of an AbstractCore install, the `abstractcore email` commands, the recipient policy | [AbstractCore: Email](https://github.com/lpalbou/abstractcore/blob/main/docs/email.md) |
| Creating and managing email automations in the apps | [Automations: Email automations](../automations.md#email-automations) |

## Your account page

Every signed-in user has the same account page:

- the gateway web console: **Users & Entities → My email address and mailbox**;
- the gateway terminal console (`abstractgateway-console`): the Users screen, then `@`
  (**My account — email**);
- the HTTP API: `GET /api/gateway/me/email` and the routes below.

It shows, in order: **Email address** (the only field with its own **Save**), **Mailbox**,
**Notifications**, **Agent email tools** and a folded **Advanced** section. Switches apply at once;
there is no other Save button.

## Connect your mailbox

The **Mailbox** card has three tabs:

- **Google** and **Microsoft**: **Sign in with Google** / **Sign in with Microsoft**. Microsoft
  shows a code to enter in any browser; Google opens a browser on the gateway's own computer. Your
  own sign-in client goes under the tab's **Advanced**.
- **Other**: your **Email address** and **Password** (an app password when your provider needs
  one). The gateway finds the mail servers from the address and shows them on one line with
  **Edit**; **Server settings** stay folded and open by themselves only when the servers cannot be
  found.

**Connect** saves and tests in one step: the gateway signs in to both servers first, stores nothing
when a step fails, and the error names the step ("Sign-in refused by imap.example.com — check the
password."). Once connected, the card shows the status line ("Connected as me@example.com ·
Google · checked 2 min ago"), **Test** and **Disconnect** (with an inline confirmation; your
policy and limits are kept). Over HTTP, `PUT /api/gateway/me/email` with `address` and `password`
does the same.

The mailbox is stored in your own data folder with its credentials encrypted, and every connection
verifies TLS. It is only read: nothing is marked read, moved or deleted. Many providers (Gmail,
iCloud, Fastmail) accept an **app password** when two-step verification is on; Microsoft 365 and
Outlook need the Microsoft sign-in.

## Who can receive mail: recipient rules and send limits

Every send (an agent's email tool, an automation's send action, a notification, a sign-in code)
passes the same checks:

1. your mailbox is connected and in use (**Use this mailbox** under **Advanced**), and your
   administrator allows mailboxes;
2. your **Recipient rules**: **Only these recipients** (an allowlist of addresses and domains) or
   **Everyone except these** (a denylist), applied to To, Cc and Bcc. A new account starts with an
   allowlist that holds your own email address;
3. your **Send limits**: 20 messages per rolling hour and 100 per day by default.

Both sit under **Advanced** on your account page, with the **Folder** automations watch (INBOX by
default) and **Send a test notification**. On top of the rules, an agent's send to anyone but you
(or the recipients an automation lists) waits for your approval.

## Agent email tools (off by default)

Your agents and workflows get the email tools (list, search and read mail, list folders, send,
reply, download an attachment) only when all three hold:

1. your administrator leaves **Agent email tools for users** on (it is on by default);
2. your mailbox is connected and in use, and mailboxes are allowed for you;
3. you switched **Agent email tools** on, on your account page (web or terminal console) or with
   `PUT /api/gateway/me/email/agent-tools`.

Until it can be switched on, the switch shows why ("Connect a mailbox first."). The rule applies
to every client (AbstractCode, the Assistant, the Observer, the consoles). An automation's own
send-email action (fixed templates you wrote), notifications and sign-in codes do not need the
switch; they need a connected, allowed mailbox.

## Automations on new mail

With your mailbox connected, the Assistant, the Observer and AbstractCode's browser client offer
**When an email arrives**, **Email me the result** and the recipients an automation may email without
asking. The rules that matter:

- **Only new mail.** Mail already in your mailbox when the watcher starts, or that arrived while none
  of your email automations was active, is never processed. Mail that arrives while the gateway is
  stopped is read when it is back.
- **Batches.** An automation that runs a model runs at most once an hour by default, one that needs
  no model every 60 seconds, on the matching mail received since its previous run. Each automation
  reads a message at most once.
- **Mail is data, never instructions.** An occurrence receives the emails as untrusted content in a
  fixed frame. An email-triggered automation does not open links or run commands on its own:
  tools such as `fetch_url`, `browser_probe`, `web_search`, `execute_command`, the memory-writing
  tools, MCP tools and camera tools ask for your approval even when the automation runs its tools
  without asking, unless you name them in `policy.untrusted_input_tools`. Sending tools are never
  granted that way.
- **Your own automatic mail never triggers an automation.** Every message the framework sends automatically
  through your account carries `Auto-Submitted: auto-generated` and an
  `X-AbstractFramework-Automation` header, and its Message-ID is recorded, so an automation never
  runs on its own result email. The trigger also ignores automatic mail from others (auto-replies,
  vacation notices) unless its configuration sets `"auto_submitted": "admit"`.

### In a workflow

An email-triggered occurrence receives the batch in `input_data.trigger`
(`source: "email.received@1"`, `content_trust: "untrusted"`, `count`, `emails`, each with its
headers, whole bodies and attachment list). A target with a string `prompt` also gets the emails
appended inside the untrusted frame. Automations whose steps need no model ("forward invoices to
me") can use the runtime's send-email action with fixed templates instead of an agent. See
[AbstractRuntime: Email](https://github.com/lpalbou/AbstractRuntime/blob/main/docs/email.md).

## Notifications

The **Notifications** card has two switches, both on by default; nothing is sent until your mailbox
is connected (until then they show "Connect a mailbox first."):

| Switch | Emails you when |
|---|---|
| **Job failed** | an automation of yours, or a run you asked to be emailed about, failed after its retries |
| **Approval needed** | a run is waiting for your answer |

An automation set to **Email me the result** also emails you the results that ask for your
attention, and a run started with an email notice emails you when it finishes or fails, as
asked. Each notice is queued once and sent once, through your own mailbox, to your email address.

## Sign-in by email

When at least one account on the gateway has a connected mailbox, the sign-in page shows one link:
**Forgot your token? Email me a sign-in code**. Enter your **Gateway user** and select the link:
it shows "Sending…". When a code was sent, the code step says where ("A sign-in code is on its
way to l•••@•••. It expires in 10 minutes.") and shows the field **Code from the email**, **Use
code**, **Send a new code** (after 30 seconds) and **Back to token**; when none was sent, the reason
appears under the link. The 8-digit code is sent to your email address
through your own mailbox; it works once, expires after 10 minutes and allows 5 tries. Once signed
in, you can rotate your token from your account. A user without an email address (or without a
connected mailbox to send with) is told so: "This account has no email address, so a code can't be
sent. Ask your gateway admin for a token."

## What administrators decide

Administrators decide what is available; users switch features on for themselves. Above the users
table in the web console's **Users & Entities** tab (and on the terminal console's Users screen)
there is one switch, **Mailboxes for users**, and two more under its **Advanced** disclosure:

| Switch | Default | Meaning |
|---|---|---|
| **Mailboxes for users** | on | users may connect their own mailbox for their agents, automations and notifications |
| **Agent email tools for users** (Advanced) | on | users may let their agents use their mailbox; each user still switches **Agent email tools** on |
| **Sign-in by email** (Advanced) | on | shows **Forgot your token? Email me a sign-in code** on the sign-in page |

The users table shows each user's **Email address** and **Mailbox** state ("connected as …",
"not connected"), never messages, recipient lists or credentials. **Create user** asks for the
user's **Email address** at the top level. Sign-in by email means whoever controls a user's mailbox
can sign in as that user; switch it off where mailboxes are less protected than gateway tokens.

## AbstractCore on its own

An AbstractCore install without a gateway has one account of its own, set with
`abstractcore email connect`, the core web console's **Email** tab or the core terminal console's
Email screen (`@`); both show the same **Email address**, **Mailbox** and **Agent email tools**
sections. From a script, pass the password on stdin so it never appears on a command line:

```bash
abstractcore email connect --address me@example.com \
  --imap-host imap.example.com --smtp-host smtp.example.com --password-stdin
```

`--client-secret-stdin` does the same for an OAuth client secret. See
[AbstractCore: Email](https://github.com/lpalbou/abstractcore/blob/main/docs/email.md).

## Coming from the environment variables

The `ABSTRACT_EMAIL_*` environment variables are not used. A gateway or AbstractCore install that
still has them imports that account once (a gateway into the administrator's own mailbox settings,
AbstractCore into its own), then names each variable still set and the setting that replaced it.
Email automations (`email.received@1`) replace `ABSTRACT_EMAIL_BRIDGE`.
