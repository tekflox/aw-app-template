# `contributes.agents` — ship the agents your app needs

An app that is *about* an agent — a domain reviewer, a vertical's coder, a
persona behind a chat channel — used to ship its skill and then rely on
somebody opening Agents Platform and hand-creating four rows in the right
order. Nothing in the install said so, and nothing said when they got it
wrong.

`contributes.agents` lets the app declare them instead. On install (and on
every boot, since activation re-runs) the workspace hands the declaration to
whichever installed app can reach Agents Platform — today
`aw-app-agents-platform-runners` — and it creates what isn't there.

A working example lives in [`examples/contributes-agents/`](../examples/contributes-agents/).

## The declaration

```jsonc
{
  "permissions": ["agents:contribute"],
  "contributes": {
    "agents": {
      "models":        [ /* Model        */ ],
      "agent_configs": [ /* AgentConfig  */ ],
      "groups":        [ /* AgentGroup   */ ],
      "agents":        [ /* Agent        */ ]
    }
  }
}
```

**The key order is the creation order, and it is not cosmetic.** An Agent
references a model, an agent config and a group *by slug*, and Agents
Platform stores those as plain strings — declaring an agent whose group
doesn't exist yet doesn't error, it produces an agent pointing at nothing.
The provider always creates models → configs → groups → agents, so your
manifest never has to think about it. Declare only the kinds you need;
every key is optional.

Every entry needs a **`slug`** — that is the identity of a seeded object
(see "Seeded, not owned" below), so the workspace rejects a manifest with a
missing, blank, or non-slug-shaped one at install time rather than seeding
a duplicate later. Beyond the slug: a `models` entry needs `provider` and
`model_id`; the other three need a `name`.

### Fields

Anything Agents Platform's own create schema accepts is passed through;
anything else is dropped before the POST (the platform 422s on unknown
fields, which would otherwise turn a future manifest-only key into a hard
seeding failure). The useful ones:

| Kind | Fields |
|---|---|
| `models` | `slug`, `provider` (`anthropic`/`openai`/`bedrock`/`cli`/`echo`/`fake`), `model_id`, `display_name` (defaults to the slug), `params`, `enabled` |
| `agent_configs` | `slug`, `name`, `description`, `mcp_config`, `extra_volumes`, `permissions`, `auto_compact_threshold_tokens` |
| `groups` | `slug`, `name`, `description`, `instructions`, `capabilities`, `kanban_target_status` |
| `agents` | `slug`, `name`, `description`, `system_prompt`, `model_slug`, `agent_config_slug`, `group_slug`, `skill_slugs`, `use_cases`, `capabilities`, `tool_specs`, `params`, `mcp_config`, `extra_volumes`, `permissions`, `inherit_from`, `hidden_from_flow`, `kanban_target_status`, `icon`, `color` |

### Long prompts live in files

A system prompt does not belong inside JSON. Any `agents` entry may use
`system_prompt_file`, and any `groups` entry `instructions_file`, giving a
path **relative to your app's package dir**:

```jsonc
{ "slug": "sec-reviewer", "name": "Security Reviewer",
  "system_prompt_file": "prompts/sec-reviewer.md" }
```

The workspace inlines the file's contents before the declaration reaches the
provider. Paths are confined to your package; one that escapes it, or
doesn't exist, drops that single field with a warning rather than failing
the install — you get an agent with an empty prompt, not a dead app. An
inline `system_prompt` wins if you somehow declare both.

Pair this with `contributes.skills`: put the durable, versioned contract in
a SKILL.md and keep the `system_prompt` to the few lines that point at it.

## Seeded, not owned

Identical to [`contributes.tasks`](./contributing-tasks.md), keyed on the
slug:

* an object with that slug already exists → **left completely alone**
* no object with that slug exists → **created**

Two consequences, both deliberate:

* **Nothing is updated, ever.** A corrected system prompt in a new app
  version does *not* reach an existing installation. Ship it under a new
  slug, or the user edits theirs. This matters more here than for tasks —
  an agent's prompt is exactly the field a user tunes for weeks, and an app
  re-asserting its own copy on every boot would erase that with no trace.
* **Nothing is removed on uninstall.** An agent that has run has sessions,
  runs and retro scores hanging off it. It stays, to be deleted
  deliberately by someone who can see what else it is attached to.

Because the slug is Agents Platform's own natural key, an agent the user
already created by hand is recognised as already-there rather than
duplicated.

## What can go wrong, and what happens

Seeding never fails an install. An app whose features work but whose agent
didn't land beats an app that refuses to install, so every failure below is
a log line:

| Situation | Outcome |
|---|---|
| No provider app installed yet | Declaration is **held** and replayed when one appears — and the provider sweeps every already-loaded app when it activates, so boot order doesn't matter. |
| Provider installed but not configured (no `agents_platform_token`) | Quiet skip, logged. Paste the token in the app's settings; the next activation seeds. |
| Agents Platform unreachable / 500 | That object is skipped, the rest still go. Retried on the next boot. |
| Slug taken (409) | Treated as already-there — that's the same outcome a pre-existing slug gets. |

To check what landed: `aw-workspace-cli logs` for the seeding lines, then
the Agents Platform UI.
