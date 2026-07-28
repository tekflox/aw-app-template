# aw-app-template

Starting point for a new [Decoupled Apps Framework](https://github.com/fredericowu/agentic-workspace/blob/main/docs/knowledge_base/docs/architecture/decoupled-apps-framework.md)
app (`aw-app.json` manifest schema v1). Every `aw-app-*` app should be born
from **the latest version of this template**, not copy-pasted from an
existing app — this repo already carries the full, currently-correct
skeleton: manifest, plugin, tests, and a CI/CD pipeline wired to the
`tekflox/aw-marketplace` release + catalog-sync automation, including every
fix that's landed on that pipeline so far (test-gating before release,
correct permissions ceiling, auto-merge).

It's a real, working app — not just files. `hello` installs one trivial CLI
that prints a configurable greeting, so cloning this template and pushing to
`master` gives you a green CI run, a tagged release, and a marketplace
catalog entry before you've changed a single line.

## Use this template

GitHub's **"Use this template"** button (top of the repo page) creates a
new repo seeded from this one's current `master` — no git history, no fork
relationship, just a fresh copy. From the CLI:

```bash
gh repo create tekflox/aw-app-<yourapp> --template tekflox/aw-app-template --public
git clone https://github.com/tekflox/aw-app-<yourapp>
```

Then rename everything marked **TEMPLATE** in comments and every `hello`/
`template_app` occurrence:

1. **`aw-app.json`** — `id`, `name`, `description`, `runtime.entrypoint`,
   `contributes.system_clis`, `config_schema` (or remove it if your app has
   no config knobs — see `aw-app-brew`'s manifest for a config-free example).
2. **`template_app/`** — rename the directory + the class in `plugin.py`
   (and update `runtime.entrypoint` in `aw-app.json` to match). If your app
   needs more than "install some CLIs" (a settings/config route, a
   background service, a frontend nav entry), don't force it into this
   shape — look at a sibling app that already does what you need instead:
   - `aw-app-git` — a settings panel + OAuth device-flow login route.
   - `aw-app-presentations` / `aw-app-whiteboard` — `contributes.nav` +
     `contributes.frontend` (a top-nav entry + window).
   - `aw-app-browser` — `tier: container` (Tier-2, a sidecar container
     instead of in-process Python).
3. **`scripts/`** — replace `install_hello.sh` with your app's real
   installer(s) (one script per CLI is the convention, but a single script
   installing several related tools — like `aw-app-essentials`'s Node.js
   toolkit — is fine too). Keep `uninstall.sh` in sync — it's the one
   script the framework's journal reverse-replay calls on uninstall, so it
   must reverse *everything* every `install_*.sh` here does.
4. **`tests/`** — `validate_manifest.py` needs no changes (fully generic).
   Update `test_installer.py`'s assertions to match your real
   `installer.py` functions, and `standalone_test.sh` to install/check your
   real CLI(s).
5. **`.github/workflows/release.yml`** — no changes needed. It calls
   `tekflox/aw-marketplace`'s shared `app-release.yml`, which runs
   `tests/validate_manifest.py` + `tests/test_*.py` on every push to
   `master` — a failing test stops the release before any version bump,
   tag, or marketplace catalog write happens.
6. **`README.md`** — replace this file with your app's own (what it
   installs, how it's configured, what's been tested where).

Finally, get your new app **listed** in the marketplace: your first push
past a passing test suite auto-tags a release and opens a
`chore(sync): <id> -> vX.Y.Z` PR against `tekflox/aw-marketplace`'s
`apps.json` (auto-merged for first-party TekFlox sources) — nothing to do
by hand.

## Layout

- `aw-app.json` — the manifest (`id: hello`, `tier: inprocess`).
- `schemas/aw-app.schema.json` — local structural validator; same schema
  every `aw-app-*` repo validates against — keep it in sync with
  `aw-workspace`'s `src/apps/capabilities.py` (the authoritative permission
  catalog) if that ever adds a new capability string.
- `scripts/install_hello.sh` — installs a trivial `hello` command into the
  workspace's persistent bin dir (`~/.aw-workspace/bin`, on PATH, survives
  restarts). Idempotent.
- `scripts/uninstall.sh` — reverses it.
- `template_app/plugin.py` — `HelloAppPlugin` entrypoint; `activate(ctx)`
  installs the CLI via the gated `ctx.commands` facade (capability
  `commands:install`) so it's journaled and the framework reverts it on
  uninstall.
- `template_app/installer.py` — the same install logic as a plain
  subprocess-calling module (no framework `ctx` needed) — used by the tests
  below.
- `tests/validate_manifest.py` — validates `aw-app.json` against the schema
  + checks every `system_clis` installer path exists on disk.
- `tests/test_installer.py` — unit tests (subprocess mocked, no real
  installs) — runs in CI on every push, gating the release.
- `tests/standalone_test.sh` — installs `hello` for real and checks
  resolution + output; run inside the aw-workspace container (not part of
  CI — needs the real target environment).

## CI/CD

`tests/validate_manifest.py` and `tests/test_*.py` run in
`tekflox/aw-marketplace`'s shared `app-release.yml` reusable workflow on
every push to `master` — a failure stops the release **before** any version
bump, tag, or marketplace catalog sync happens. See that repo's
`scripts/bump_version.py` for the semver-bump-from-commit-messages logic and
`scripts/sync_catalog_entry.py` for what fields get written into
`apps.json` automatically (name/description/publisher/resource_estimate —
`has_config`/`bootstrap`/`icon`/`tags`/`category` are set once by hand on
first listing and not auto-synced afterward).
