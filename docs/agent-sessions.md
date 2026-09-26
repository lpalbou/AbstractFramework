# Agent sessions on a gateway

This page explains what happens when you chat with an agent through a gateway, from any client:
which workflow answers, where the agent's files live and how they are protected, which skills it
can use, how replies stream while the model writes them, and how the desktop Assistant signs in.
It is the cross-package overview; each package owns the full reference, linked in every section.

The same rules apply to every client: AbstractCode (terminal and browser), AbstractAssistant, the
gateway's own consoles, and your own app through the gateway API. For how the packages connect,
see [Architecture](architecture.md#agent-sessions-how-a-turn-flows); for first steps, see
[Getting Started](getting-started.md).

---

## The default agent workflow

A client that runs an agent names an **interface** (the input/output contract the workflow
implements) rather than a fixed workflow. The gateway decides which workflow answers each
interface with its setting `agents.default_workflow.<interface>`:

| Interface | Used by | When nothing is saved |
|---|---|---|
| `abstractcode.agent.v1` | AbstractCode (terminal and browser) | the default entrypoint of the shipped `basic-agent` workflow |
| `abstractassistant.agent.v1` | AbstractAssistant | none: the Assistant runs its built-in orchestrator |
| any other interface a workflow declares | your own clients | none until an admin saves one |

The gateway's Telegram bridge and its backlog advisor resolve their agent the same way.

Change it in any of the three places the gateway offers (admin only, audit-logged):

| Web console | Terminal console | Command line |
|---|---|---|
| **Workflows** → *Default agent workflow*, or *Make agent default* on an entrypoint | Runtimes → *Runtime knobs* → *Edit default agent workflows* | `abstractgateway config set agents.default_workflow.abstractcode.agent.v1 coding-agent:coder` |

The value is `[catalog:]bundle[@version]:flow`. Without a version, the latest published version
runs; `catalog:` picks a workflow from the shared workflow catalog.

How clients follow it:

- AbstractCode and the Assistant list **Gateway default → name @version** first in their workflow
  pickers (`/workflow` and `--workflow default` in the terminal, the **Workflow** list in the
  browser, Settings → Models → **Workflow** in the Assistant).
- Choosing it saves "the gateway default", not a copy of today's workflow: the gateway resolves it
  at every new turn, so a change on the gateway applies to the next turn of every conversation
  that follows the default. A turn never changes workflow while it runs.
- Picking a named workflow pins that workflow for the client.
- A saved default that no longer resolves (a removed or deprecated workflow) is shown as
  unavailable with the reason, and runs that ask for it are refused until an admin changes it.
  The gateway never substitutes another workflow on its own.

Your own client asks for the default with `flow_id: "@default"` plus `interface` on
`POST /api/gateway/runs/start`; the response names the workflow that ran (`resolved_workflow`).
Reference: [AbstractGateway configuration: default agent workflow](https://github.com/lpalbou/AbstractGateway/blob/main/docs/configuration.md#default-agent-workflow).

---

## The conversation workspace

An agent reads and writes files **on the gateway's computer**, in its run's workspace folder:

- the conversation's own folder, which the gateway creates under
  `<data dir>/workspaces/session-…`; or
- the folder you started the AbstractCode terminal client from, when the gateway runs on the same
  machine.

You can see that folder from AbstractCode: the **Files** tab in the browser and `/files` in the
terminal show its absolute path on the gateway host, the host name, the folder tree, and a
preview of each file. **Open folder** (the terminal's `o`) is offered only to an admin sitting at
the gateway's computer; everyone else sees the path, with a copy button, labelled as being on the
gateway host. Another user's run is never visible: its workspace routes answer 404.

### Built-in protection for every run

Whatever starts a run (a client, a schedule, the Telegram, email or agora bridges, an entity
summons), the gateway gives it a workspace folder and a built-in deny list. These folders of the
gateway's user account are never listed or served by the workspace browser, and the agent's file
tools cannot read or write them:

- credential folders: `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.config/gcloud`, `~/.kube`,
  `~/Library/Keychains`;
- the framework's own settings: `~/.abstractgateway`, `~/.abstractcode`, `~/.abstractassistant`,
  `~/.abstractcontinuum`, `~/.abstractcore`;
- the gateway's data folder, except the run's own conversation folder inside it.

A run also cannot choose a folder inside the gateway's data folder as its workspace (other than
the conversation folder the gateway made for the same user). The deny list is applied on every
file access without being written into the model's prompt, so the prompt stays identical from
turn to turn.

Limits to know:

- An admin can turn the deny list off for runs (`abstractgateway config set workspace_builtin_deny
  off`); the workspace browser keeps hiding those folders.
- Shell commands that a run is allowed to execute are not confined by the deny list; keep shell
  tools behind approval on machines that hold secrets.

Reference: [AbstractGateway configuration: workspace policy](https://github.com/lpalbou/AbstractGateway/blob/main/docs/configuration.md#workspace-policy-filesystem-scope)
and [API: a run's workspace folder](https://github.com/lpalbou/AbstractGateway/blob/main/docs/api.md#a-runs-workspace-folder-browse-and-preview).

---

## Skills

[Agent Skills](guide/agent-skills.md) (`SKILL.md` folders) are portable instructions an agent can
read when a task calls for them. A curated shelf of reviewed skills ships inside the
`abstractskill` package, which the gateway installs with itself.

- At each start, the gateway copies the curated shelf into `<data dir>/skills/registry`: it adds
  new skills and refreshes the files it wrote before, and never overwrites a file you edited
  there. **Refresh the curated shelf** in the console runs the copy again on demand.
- To use another folder, set `skills.shelf` (console **Apps** → *Skills shelf*, the terminal
  console's runtime knobs, or `abstractgateway config set skills.shelf /path/to/registry`). A
  folder that does not exist or holds no skills is reported as unavailable with the reason; the
  gateway does not fall back to another shelf silently.
- A trust gate decides what an agent may use: validated skills activate, unverified skills are
  held, and skills under a do-not-use advisory never do. An edited skill counts as unverified
  until it is validated again.
- Attach skills to a run from AbstractCode (browser Settings, `/skills` in the terminal) or with
  `input_data.skills` on `POST /runs/start`. When the gateway offers no skills, the clients show
  the gateway's explanation and where its shelf is.

Reference: [AbstractSkill](https://github.com/lpalbou/AbstractSkill) and
[AbstractGateway configuration: skills shelf](https://github.com/lpalbou/AbstractGateway/blob/main/docs/configuration.md#skills-shelf).

---

## Live replies (streaming)

With live replies on, you watch the answer while the model writes it; the finished answer then
replaces the live text, and it is the same answer you get without streaming.

Two settings decide it:

| Setting | Where | Values |
|---|---|---|
| The gateway's default, `agents.streaming_default` | console **Workflows** → *Stream replies by default*, the terminal console's runtime knobs, `abstractgateway config set agents.streaming_default on` | on or off (off until saved) |
| Each client's **Stream replies** | AbstractCode browser Settings, `/stream` in the terminal client, Assistant Settings → Models; `assistant run --stream on\|off` for one turn | **Gateway default**, **On**, **Off** |

A client left on **Gateway default** follows the gateway's setting. **Off** is always honoured.
**On** takes effect only when the gateway advertises live replies; otherwise the client says so
once and shows the finished answer.

What streams: the text and the reasoning (shown apart) of every model call in the run, including
the calls of sub-agents it starts. What does not stream, with a one-line note in the client:

- calls that return structured output;
- a gateway whose runtime calls a remote AbstractCore server instead of running models in process;
- providers that cannot stream, or cannot report token usage while streaming;
- a workflow step that turns streaming off for its model call;
- entity chat and an entity's own-time loop.

Scheduled runs and the Telegram and email bridges do not stream by default.

Live text travels as `llm.delta` / `llm.delta_end` events on the run's existing SSE stream
(`GET /api/gateway/runs/{run_id}/ledger/stream`). They are not ledger records: the ledger holds
the same records with streaming on or off. A client that connects in the middle of an answer
first receives the text written so far. Reference:
[AbstractGateway API: live replies](https://github.com/lpalbou/AbstractGateway/blob/main/docs/api.md#4b-live-replies-token-deltas-on-the-same-stream).

---

## Opening the Assistant from the gateway

AbstractAssistant is a desktop app that runs on the gateway's computer. Click **Open** on its card
in the gateway console (or use the gateway's menu-bar icon): the gateway starts the Assistant
already connected and signed in as you, with no token to type.

How it works: the gateway writes a one-time code (valid for two minutes, usable once) into a file
only your account can read, and starts the Assistant with `--gateway-url <address>
--gateway-handover-file <file>`. The Assistant reads and deletes the file, trades the code for a
sign-in on this computer, and remembers that sign-in in
`~/.abstractassistant/gateway_connection.json` for later launches. No code or token is ever on its
command line or in its environment.

An Assistant that is already running cannot receive a code: if it is not signed in, quit it and
click **Open** again. From another computer the console explains that the Assistant opens on the
gateway's computer. Reference:
[AbstractGateway apps](https://github.com/lpalbou/AbstractGateway/blob/main/docs/apps.md) and
[AbstractAssistant](https://github.com/lpalbou/AbstractAssistant).

---

## Related pages

- [Architecture](architecture.md): how the gateway, the apps, the runtime and AbstractCore connect,
  with the live-reply lane and the app proxies.
- [Configuration](configuration.md): where each setting lives.
- [FAQ](faq.md) and [Troubleshooting](troubleshooting.md): recurring questions and fixes,
  including model memory after an eject.
- [Gateway exposure security](guide/gateway-security.md): what "this computer" means for a request
  and who may open folders or apps.
