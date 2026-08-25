# Bitrix24 Integrations — n8n + AI

Monorepo untuk **integrasi Bitrix24** yang share n8n instance + AI provider di 1 VPS.
Customer: **PT Len / Askarasoft** — PIC Michael Chandra.

## Projects

| # | Project | Folder | Status | Trigger | Bitrix Instance | Bitrix Action |
|---|---|---|---|---|---|---|
| **1** | Proposal Estimation | [`proposal-estimation/`](proposal-estimation/) | ✅ Live | Bitrix Automation Rule (SPA 2098 stage change) | `askarasoftdemo.bitrix24.com` (DEMO) | Write to SPA field |
| **2** | TLDV Meeting Summary | [`tldv-meeting-summary/`](tldv-meeting-summary/) | ✅ Live | TLDV `TranscriptReady` webhook | `askarasoft.bitrix24.com` (PRODUCTION) | Post Lead timeline comment + auto-create SPA "Proposal & Quotation" |
| **3** | Product Image Extraction | [`product-image-extraction/`](product-image-extraction/) | ✅ v1+v2+v3 Live | Bitrix Automation Rule (SPA 1038 stage change "Prepare") | `tfssbdemo.bitrix24.com` (DEMO) | Extract quotation (image/PDF/DOCX) → SPA custom fields + Products tab dengan TRUE SKU (parent+variant) + attribute properties + multi-quotation |

Both projects share:
- **VPS**: same server, shared n8n stack
- **n8n instance**: https://n8n.askarasoft.com (HTTPS via Caddy)
- **AI provider**: OpenAI (gpt-5.5 reasoning model)
- **Deploy config**: [`deploy/`](deploy/) folder

## Repo Structure

```
bitrix-integrations/
├── README.md                              # This file — overview & routing
├── .gitignore
│
├── deploy/                                # ← SHARED n8n stack (both projects)
│   ├── docker-compose.yml                 # n8n + Postgres + Caddy stack
│   ├── Caddyfile                          # HTTPS reverse proxy
│   ├── .env.example                       # Env var template
│   ├── .gitignore
│   └── DEPLOYMENT_NOTES.md                # How to deploy, backup, rollback
│
├── proposal-estimation/                   # ← Project 1
│   ├── README.md
│   ├── docs/
│   │   ├── PRD.md
│   │   ├── BITRIX_SCHEMA_REFERENCE.md
│   │   ├── BITRIX_BP_SETUP.md
│   │   └── SYSTEM_FLOW.md
│   └── workflow/
│       ├── proposal-estimation.json
│       └── IMPORT_GUIDE.md
│
├── tldv-meeting-summary/                  # ← Project 2
│   ├── README.md
│   ├── docs/
│   │   ├── PRD.md
│   │   ├── TLDV_API_REFERENCE.md
│   │   └── BITRIX_LEADS_REFERENCE.md
│   └── workflow/
│       ├── tldv-meeting-summary.json                     # v1 baseline (comment only)
│       ├── tldv-meeting-summary-with-proposal.json       # v2 extended (with auto-create SPA)
│       └── IMPORT_GUIDE.md
│
└── product-image-extraction/              # ← Project 3 (POC in planning)
    ├── README.md
    ├── docs/                              # PRD, Excel attributes, sample images TBD
    └── workflow/                          # n8n workflow TBD
```

## Quick Start (kalau baru clone)

1. **Deploy shared infra** — [`deploy/DEPLOYMENT_NOTES.md`](deploy/DEPLOYMENT_NOTES.md)
2. **Pilih project** yang mau diintegrasi:
   - Project 1: [`proposal-estimation/README.md`](proposal-estimation/README.md)
   - Project 2: [`tldv-meeting-summary/README.md`](tldv-meeting-summary/README.md)
   - Project 3: [`product-image-extraction/README.md`](product-image-extraction/README.md)
3. Follow project-specific import guide di masing-masing folder

## Live Endpoints

| Endpoint | Purpose |
|---|---|
| https://n8n.askarasoft.com | n8n UI (owner login) |
| https://n8n.askarasoft.com/webhook/bitrix-spa-estimate | Project 1 webhook (from Bitrix Automation Rule) |
| https://n8n.askarasoft.com/webhook/tldv-transcript-ready | Project 2 webhook (from TLDV) |

## License

MIT (opsional, ditambah kalau perlu)
