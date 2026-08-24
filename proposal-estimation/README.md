# Project 1 — Bitrix24 SPA Proposal Estimation

Otomatisasi estimasi mandays proposal via integrasi **Bitrix24 → n8n → OpenAI → Bitrix24**.

Sales mengisi form di Bitrix24 SPA "Proposal Estimation" (entityTypeId=2098), lalu sistem otomatis panggil AI untuk generate breakdown mandays dan menulis hasilnya kembali ke field di Bitrix24.

## Status

✅ **Live in production** — deployed di shared n8n instance, tested & stable.

## Flow

```
Sales fill form in Bitrix24 SPA "Proposal Estimation"
        ↓ (stage moved to "Request AI Estimation")
Bitrix24 Automation Rule → outbound webhook
        ↓ POST { id: <item_id> }
n8n Workflow (15 nodes)
        ├─ GET full item data via crm.item.get
        ├─ Download & extract RFP PDF (if uploaded)
        ├─ Call OpenAI to extract only relevant sections (functional req, integrations, workflows, reporting, mobile/web)
        ├─ Map enum IDs → readable labels
        ├─ Build prompt from editable template
        ├─ Call OpenAI (gpt-5.5, reasoning model)
        ├─ Parse response
        └─ POST crm.item.update → write to AI Total Mandays Output + move stage to "Pending"
        ↓
Result visible in Bitrix24 detail view
```

## Folder Structure

```
proposal-estimation/
├── README.md                              # This file
├── docs/
│   ├── PRD.md                             # Product Requirements Document
│   ├── BITRIX_SCHEMA_REFERENCE.md         # Field codes, enum mappings, stage IDs
│   ├── BITRIX_BP_SETUP.md                 # How to setup Bitrix Automation Rule
│   └── SYSTEM_FLOW.md                     # Customer-facing flow explanation
└── workflow/
    ├── proposal-estimation.json           # n8n workflow (importable)
    └── IMPORT_GUIDE.md                    # How to import & test the workflow
```

## Bitrix Instance

**DEMO** — `askarasoftdemo.bitrix24.com` (SPA 2098 hanya ada di sini, tidak ada di production).

## Shared Infrastructure

n8n stack, VPS, dan AI API key di-share dengan Project 2 (tldv-meeting-summary).
Lihat `../deploy/` di root untuk shared deployment config.

- **VPS**: `<vps_ip>` (lihat memory.md / credentials.md)
- **n8n UI**: https://n8n.askarasoft.com (HTTPS via Caddy)
- **Webhook endpoint**: `https://n8n.askarasoft.com/webhook/bitrix-spa-estimate`
- **AI provider**: OpenAI (gpt-5.5)

## Quick Start

Kalau baru clone repo:

1. **Deploy shared infra** — lihat `../deploy/` folder
2. **Import workflow** — lihat `workflow/IMPORT_GUIDE.md`
3. **Setup Bitrix Automation Rule** — lihat `docs/BITRIX_BP_SETUP.md`

## Related

- Project 2 (TLDV Meeting Summary): `../tldv-meeting-summary/`
- Shared infra: `../deploy/`
- Root overview: `../README.md`
