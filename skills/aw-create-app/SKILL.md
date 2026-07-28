---
name: aw-create-app
description: >-
  Author a decoupled aw-workspace app from this template — manifest, tiers
  (Tier-1 in-process vs Tier-2 container), the capability/permission catalog,
  what an app can contribute (windows, nav, routes, system CLIs, DB tables,
  frontend bundles), the declarative window widget vocabulary, install +
  marketplace release, and how it shows up in the Apps grid. Use whenever you
  are asked to build a new aw-workspace app, add an app to the marketplace, or
  extend/port a monolith feature into a decoupled app.
---

# Creating a decoupled aw-workspace app

This skill ships **inside `aw-app-template`** and teaches how to turn this
repo into a real app. The template is itself a marketplace app (a minimal,
fully-wired "hello" example). Copy it, rename everything marked `TEMPLATE`/
`hello`, and follow the contract below.

> **Migration mindset:** most new apps are *ports* of an existing
> `agentic-workspace` monolith feature — base the app on the working monolith
> code (cite `file:line`) and port faithfully. Greenfield only when there is
> no monolith equivalent.

## 1. What an app is

A decoupled app is a self-contained repo (`aw-app-<name>`) with a manifest
(`aw-app.json`) at its root. The aw-workspace runtime loads installed apps
from `~/agentic-workspace/apps/<id>/` and serves them under `/api/apps/<id>`.
Two tiers:

- **Tier-1 (`"tier": "inprocess"`)** — a Python plugin loaded into the
  workspace process. Cheapest; use for routes, DB tables, CLIs, windows,
  background tasks. Entrypoint: `runtime.entrypoint = "pkg.plugin:ClassName"`.
- **Tier-2 (`"tier": "container"`)** — a sidecar container from a prebuilt
  image, spawned over the host podman socket and reverse-proxied. Use when the
  app needs its own runtime/binaries (e.g. a browser). Needs
  `permissions: ["containers:manage"]` and `runtime.image/port/run_flags_needed`.

## 2. The manifest (`aw-app.json`)

```jsonc
{
  "manifest_version": 1,
  "id": "myapp",                       // unique slug; becomes /api/apps/myapp
  "name": "My App",
  "version": "0.1.0",
  "description": "...",
  "tier": "inprocess",                 // or "container"
  "publisher": "TekFlox",
  "requires_ui_refresh": true,          // SPA re-fetches contributions after install/config-save
  "resource_estimate": { "cpu": "low", "memory": "low", "disk": "low" },

  "runtime": {                          // Tier-1:
    "python": ">=3.11",
    "entrypoint": "myapp_app.plugin:MyAppPlugin",
    "pip_requires": []
  },
  // Tier-2 instead: "runtime": { "image": "ghcr.io/tekflox/aw-myapp:latest",
  //                              "port": 7900, "resources": {"cpus":0.5,"mem_mb":1024},
  //                              "run_flags_needed": ["--shm-size=1g"] }

  "permissions": [ "routes:register" ],  // capability grants — see §3
  "contributes": { /* see §4 */ },
  "config_schema": { "type": "object", "properties": {}, "required": [] },
  "dependencies": {},
  "migrations": {}
}
```

Validate it: `python tests/validate_manifest.py` (schema in `schemas/aw-app.schema.json`).

## 3. Capability catalog (`permissions`)

Only request what you use — each is enforced by the runtime's `AppContext`.

| Capability | Risk | Grants |
|---|---|---|
| `routes:register` | low | mount `/api/apps/<id>/*` routes |
| `db:own-tables` | low | create/use app-owned workspace tables |
| `commands:install` | low | install CLIs/commands that survive restart |
| `service:manage` | low | register a start/stop background service |
| `watchdog:tasks` | low | register in-process periodic tasks |
| `net:outbound` | low | outbound HTTP from Tier-1 code |
| `fs:workspace-data` | low | read/write the app's own data dir |
| `secrets:own` | low | request the app's own secrets |
| `notifications:send` | low | fire a workspace notification |
| `containers:manage` | **high** | run/manage sidecar containers (Tier-2) |
| `ui:code` | **high** | load the app's JS bundle into the SPA |
| `ui:slots:<slot>` | low | render into a named SPA slot (e.g. `core.nav.workspace`) |
| `config:extend:<app>` | high | write config into another app's extension point |

## 4. What an app contributes (`contributes`)

- **`windows`** — declarative windows opened from the app's card. Each:
  `{ "id": "myapp.main", "title": "...", "body": { "type": "declarative", "spec": "windows/main.json" } }`.
- **`nav`** — OPTIONAL top-bar buttons. `section: "workspace"` → Workspace menu.
  **Omit nav for normal apps** — every installed app already appears as a card
  in the **Apps grid** (the launcher reads `GET /api/apps`); nav is only for
  apps that also want a persistent menu entry.
- **`routes`** — `[{ "prefix": "/api/apps/myapp" }]` (needs `routes:register`).
- **`system_clis`** — `[{ "name": "hello", "installer": "scripts/install_hello.sh" }]`
  (needs `commands:install`).
- **`db`** — app-owned tables (needs `db:own-tables`).
- **`frontend`** — a JS bundle mounted into granted slots (needs `ui:code`;
  unsigned apps are downgraded to iframe mode).

### Window widget vocabulary (`windows/*.json`)

`layout: "stack"`, `regions: [{ id, widgets: [...] }]`. Widget `type`:
`markdown`, `list`, `button`, `collapsible`, `form`, `auth_status`,
`iframe` (`{ src }`, an `/api/*` path — rewritten to the workspace API host),
`app_iframe` (`{ app_id, path }` — resolves to the app's **external
subdomain** `https://<app_id>.app.<slug>.workspace.<apex>`, honoring the LAN
fast-path; use this to surface a Tier-2 container's own web UI).

## 5. How it shows up + install

- Installed apps live in `~/agentic-workspace/apps/<id>/`; the runtime loads
  their manifests and serves `GET /api/apps` (list) + `GET /api/apps/-/contributions`
  (live-refetched nav/windows) + `GET /api/apps/-/catalog` (marketplace).
- The SPA "Apps" launcher lists them as cards; clicking opens the default window.
- Install paths: `POST /api/apps/install` (fetch repo + reconcile), the
  reconciler's "Install My Apps", or a hand-sync of the app dir + workspace reload.
- **Marketplace:** the app must be listed in the marketplace catalog source
  (public, tokenless raw-GET). Ship `.github/workflows/release.yml` (see this
  repo) to cut versioned releases; the catalog references the repo.

## 6. Reference apps (read these before building)

- `aw-app-template` (this repo) — Tier-1 + `commands:install` (the `hello` CLI).
- `aw-app-whiteboard` — Tier-1 + `routes:register` + `db:own-tables` + a window.
- `aw-app-devctl` — Tier-1 + `routes:register` (talks CDP to another app's container).
- `aw-app-browser` — Tier-2 container + `app_iframe` window → external subdomain (noVNC).

## 7. Checklist

1. Copy this repo → `aw-app-<name>`; rename `template_app/`, `id`, `name`, entrypoint.
2. Pick the tier; declare only the capabilities you use.
3. Add your `contributes` (window for UI, routes for a backend, etc.).
4. `python tests/validate_manifest.py` green; `tests/standalone_test.sh` green.
5. Push to `github.com/tekflox/aw-app-<name>`; wire `release.yml`; add to the
   marketplace catalog.
6. Install and confirm the card shows in the Apps grid and opens.
