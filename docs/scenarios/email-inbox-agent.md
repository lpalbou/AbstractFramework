# Scenario: Email inbox agent

Goal: let an agent read the mail you receive, act on it (summarise, sort, draft), and email you the
result, with your own mailbox and nothing configured outside the consoles.

## How it fits together

- You connect your own mailbox to the gateway. The account is yours alone and stored encrypted in
  your data folder.
- An automation with the **When an email arrives** trigger (`email.received@1`) runs your workflow
  on each batch of new mail that matches its filters.
- The gateway's mail watcher reads the mailbox read-only while at least one of your email
  automations is active; the runtime records each new message durably before the automation reads
  it.
- **Email me the result** sends the automation's results to your own address, through your own
  account.

See [Guide: Email integration](../guide/email-integration.md) for the rules (recipient policy, send
limits, agent email tools, sign-in by email).

## Step 1: Connect your mailbox

In the gateway web console, open **Users → My email** (terminal console: the Users screen, then
`@`). Enter the address, an app password and the IMAP and SMTP servers, or use **Sign in with
OAuth2** for Google or Microsoft. The gateway tests both servers before it saves the account.

Check the recipient policy in the same place: a new account allows mail only to your own address,
which is what this scenario needs.

## Step 2: Create the automation

From the Assistant, the Observer (**Launch → Automate**) or AbstractCode's browser client, create an
automation with:

- **When an email arrives**, with typed filters (from these addresses or domains, sent to these
  addresses, subject contains, has attachments);
- the task for the agent, for example "Summarise these emails and list what needs an answer";
- **Email me the result**, then turn on **Automation results** in **My email → Notifications**.

The same definition through the API:

```text
"trigger": {"source_id": "email.received", "source_version": 1,
            "config": {"every": "1h", "filter": {"subject_contains": "invoice"}}},
"notify":  {"channels": ["console", "email"]},
"policy":  {"tool_approval": "auto", "email_allowed_recipients": ["self"]}
```

An automation that runs a model runs at most once an hour by default, on all matching mail received
since its previous run.

## Step 3: Test

Send yourself an email that matches the filter after creating the automation. Expected:

- the automation runs on the next batch and shows the run as a question/answer turn in every client;
- its result reaches you by email when the workflow asks for attention;
- the result email does not trigger the automation again (mail the framework sends automatically
  through your account is never an event).

Mail that was already in the mailbox, or that arrived while no email automation was active, is not
processed.

## Letting the agent use email itself

To let the agent search your mailbox or send mail during a run, an administrator first makes
**Agent email tools** available to you; then turn them on in **My email**. A send to anyone but you
waits for your approval, and every send passes your recipient policy and send limits.
