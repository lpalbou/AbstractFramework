# Email integration

Every signed-in person on an AbstractGateway can connect **their own** mailbox. That account is used
for three things:

- **automations on new mail**: the **When an email arrives** trigger (`email.received@1`);
- **email notifications**: automation results and failures, approvals waiting for you, finished or
  failed runs, sent through your own account to your own address;
- **sign-in by email**: **Forgot your token?** and **Email me a sign-in code** on the gateway's
  sign-in page.

Email is configured as settings in the consoles, never through environment variables. Nothing is
active until you choose it: no mail is read until you create an email automation, notifications stay
in the console until you turn them on, and agents get no email tools until an administrator makes
them available and you turn them on.

The package guides hold the full references:

| Topic | Reference |
|---|---|
| Your mailbox, notifications, sign-in by email, what administrators decide, where things are stored | [AbstractGateway: Email](https://github.com/lpalbou/AbstractGateway/blob/main/docs/email.md) |
| The `email.received@1` trigger, the event inbox, sending without asking, mail sent by automations | [AbstractRuntime: Email](https://github.com/lpalbou/AbstractRuntime/blob/main/docs/email.md) |
| The account of an AbstractCore install, the `abstractcore email` commands, the recipient policy | [AbstractCore: Email](https://github.com/lpalbou/abstractcore/blob/main/docs/email.md) |
| Creating and managing email automations in the apps | [Automations: Email automations](../automations.md#email-automations) |

## Connect your mailbox

Open **My email** in any of these places; they share the same fields:

- the gateway web console: **Users → My email** (every signed-in user);
- the gateway terminal console (`abstractgateway-console`): the Users screen, then `@`;
- the HTTP API: `PUT /api/gateway/me/email`.

Give the address, the password (or an app password) and the IMAP and SMTP servers, or choose
**Sign in with OAuth2** for Google or Microsoft. The gateway signs in to both servers before it saves
anything and names the cause and the fix when a server refuses. The account is stored in your own
data folder with its credentials encrypted, and every connection verifies TLS. The mailbox is only
read: nothing is marked read, moved or deleted.

Many providers (Gmail, iCloud, Fastmail) accept an **app password** when two-step verification is
on; Microsoft 365 and Outlook need OAuth2.

## Who can receive mail: recipient policy and send limits

Every send (an agent's email tool, an automation's send action, a notification, a sign-in code)
passes the same checks:

1. email is turned on, by you and by the administrator;
2. your **recipient policy**: an **allowlist** (only the listed addresses and domains) or a
   **denylist** (everyone except them), applied to To, Cc and Bcc. A new account starts with an
   allowlist that holds your own registered address;
3. your **send limits**: 20 messages per rolling hour and 100 per day by default, which you can
   change.

On top of the policy, an agent's send to anyone but you (or the recipients an automation lists)
waits for your approval.

## Agent email tools (off by default)

Your agents and workflows get the email tools (list, search and read mail, list folders, send,
reply, download an attachment) only when all three hold:

1. an administrator made **Agent email tools** available to you (they are not, by default);
2. your account is connected and email is allowed for you;
3. you turned on **Agent email tools** in **My email** (web console), **Policy, limits & tools**
   (terminal console) or with `PUT /api/gateway/me/email/agent-tools`.

The rule applies to every client (AbstractCode, the Assistant, the Observer, the consoles). An
automation that only sends you its results, notifications and sign-in codes do not need the
switch; they need a connected, allowed account.

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
  fixed frame. An email-triggered automation never follows links from an email: tools such as
  `fetch_url`, `browser_probe`, `web_search` and `execute_command` ask for your approval even when
  the automation runs its tools without asking, unless you name them in
  `policy.untrusted_input_tools`. Sending tools are never granted that way.
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

Email notifications are off until you turn each event on in **My email → Notifications**:
automation results and failures (for automations set to **Email me the result**), a run waiting for
your approval, and runs started with an email notice. Each notice is queued once and sent once,
through your own account, to your registered address.

## Sign-in by email

When at least one account on the gateway has email set up, the sign-in page offers **Forgot your
token?** (a new token, shown once; the old one stops working) and **Email me a sign-in code**. Enter
your gateway user name; an 8-digit code is sent to your registered address. A code works once,
expires after 10 minutes and allows 5 tries. Users without email ask an administrator to rotate
their token.

## What administrators decide

Administrators make email available; users turn it on for themselves. In the web console's
**Users** tab (**Email for users** and the row buttons) or the terminal console's Users screen, an
administrator sets, gateway-wide and per user:

| Capability | Default | Meaning |
|---|---|---|
| Email | available | users may connect their own mailbox |
| Agent email tools | not available | users may turn on the email tools for their own agents |
| Sign-in by email | available (gateway-wide) | **Forgot your token?** and **Email me a sign-in code** |

Administrators see each user's mailbox state, address and last error, never messages, recipient
lists or credentials. Sign-in by email means whoever controls a user's mailbox can sign in as that
user; turn it off where mailboxes are less protected than gateway tokens.

## AbstractCore on its own

An AbstractCore install without a gateway has one account of its own, set with
`abstractcore email connect`, the core web console's **Email** page or the core terminal console's
Email screen. From a script, pass the password on stdin so it never appears on a command line:

```bash
abstractcore email connect --address me@example.com \
  --imap-host imap.example.com --smtp-host smtp.example.com --password-stdin
```

`--client-secret-stdin` does the same for an OAuth client secret. See
[AbstractCore: Email](https://github.com/lpalbou/abstractcore/blob/main/docs/email.md).

## Coming from the environment variables

The `ABSTRACT_EMAIL_*` environment variables and the gateway email bridge are not used. A gateway or
AbstractCore install that still has those variables imports that account once into the
administrator's email settings, then names each variable still set and the setting that replaced
it. Email automations (`email.received@1`) replace the bridge.
