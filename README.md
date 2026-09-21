# PesaGuard Status (status.pesaguard.victorkipruto.com)

Static status page for PesaGuard services (API, Dashboard, Transactions,
Reconciliation, Fraud Detection, Webhooks). No build step: hand-written HTML
plus vanilla CSS/JS. State is read at runtime from JSON under `data/`, with
`api/status.json` preferred as the runtime endpoint.

The palette, typography, dark mode and motion mirror
[docs.pesaguard.victorkipruto.com](https://docs.pesaguard.victorkipruto.com);
the favicon and colour tokens come from that site.

## Current status of this page: NOT CONNECTED

**No monitoring source, incident system or maintenance scheduler is wired up
yet.** The page therefore reports `unknown` / `Not available` everywhere rather
than showing a green board. This is deliberate.

Do not publish a green status page for a payments platform without real
measurements behind it. `tests/accessibility.test.js` and
`tests/status.test.js` fail the build if a hardcoded "healthy" state or a
fabricated timestamp appears in a page or component.

### The verification contract

Every payload declares its provenance:

```json
{
  "dataSource": "unconfigured",
  "verified": false,
  "note": "explains the current state to anyone reading the file"
}
```

* `verified: false` — the page renders `unknown` / `Not available` and shows an
  on-page notice. Payloads must stay empty (`[]`, `{}`, `null`). Tests enforce this.
* `verified: true` — the payload must carry real measurements **and** a real
  `lastUpdated`/`generatedAt`. Tests then require valid percentages.

To go live: connect a health-check aggregator, write its real output into the
JSON files (or serve it from the runtime endpoint), then flip `verified` to
`true` and set `dataSource` to the system that produced the numbers.

## Preview

The page loads its header/footer via `fetch()`, so it needs a static server:

```powershell
npm run serve
# http://localhost:4174/
```

Browsing the files directly over `file://` shows page content but not the
shared header/footer.

## Validate

```powershell
npm run check
```

## Data files

| File | Purpose | Shape |
| --- | --- | --- |
| `data/status.json` | Overall + per-service state | `{ version, generatedAt, dataSource, verified, note, lastUpdated, overall, services[], activeIncidents[], activeMaintenance[] }` |
| `api/status.json` | Runtime status endpoint mirror | same as above |
| `data/incidents.json` | Incident record | `{ version, dataSource, verified, note, incidents[] }` |
| `data/maintenance.json` | Maintenance windows | `{ version, dataSource, verified, note, maintenance[] }` |
| `data/uptime.json` | Uptime measurements | `{ version, dataSource, verified, note, overall, periods{}, services[], history[], recentDowntime[] }` |

Status values: `operational`, `degraded`, `outage`, `maintenance`, `unknown`.
Unknown is a first-class state and is what the page shows when nothing has been
measured.

## Structure

```
index.html  incidents.html  maintenance.html  uptime.html  404.html
css/    reset, variables, global, layout, components, status,
        incidents, maintenance, uptime, animations, responsive
js/     ui.js (helpers + component loader), app.js (chrome/behaviour),
        status.js, incidents.js, maintenance.js, uptime.js
data/   status.json, incidents.json, maintenance.json, uptime.json
api/    status.json (runtime endpoint)
components/  header, footer + reference markup templates for
             status-overview, service-list, incident-card,
             maintenance-card, uptime-card
assets/ logo/*.svg, icons/{operational,degraded,outage,maintenance}.svg
tests/  status, incidents, uptime, accessibility + run.js
```

`components/*.html` provides the shared chrome. The four card templates are
reference markup documenting the intended DOM; the page scripts build the same
structure from data.

## Accessibility and UX

`lang` on every page, skip link, landmark regions, keyboard-visible focus,
`prefers-reduced-motion`, `prefers-color-scheme` dark theme, ARIA labels on
controls, `aria-label` on chart bars, and status conveyed by icon plus text plus
colour (never colour alone).

## Known gaps

* Email subscriptions are **not implemented**. The form is rendered disabled
  with an explanation; it sends nothing.
* Uptime charts render only measured days. There is no synthetic backfill.
* No CSP, no SRI on the Google Fonts stylesheet, and no rate limiting on the
  runtime status endpoint (which is currently a static file).
* `npm run check` validates data shape, page/component structure, SEO and the
  no-false-claims contract by reading files. It does **not** execute the page
  JavaScript — a browser smoke test is still required after front-end changes.
