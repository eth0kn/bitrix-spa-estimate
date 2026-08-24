# Project 2 — TLDV Meeting Summary → Bitrix24 Timeline Comment + Auto Proposal Creation

Otomatisasi meeting summary: TLDV rekam meeting → transcript siap → n8n summarize via AI → post ke Bitrix24 Lead sebagai timeline comment. Kalau AI classifier deteksi ada action item minta buat proposal, otomatis create SPA item di "Proposal & Quotation".

## Status

✅ **Live in production** — deployed dan tested end-to-end (Test A + B pass).

## Flow (v2 — Current)

```
Sales bikin Zoom meeting via TLDV, judul format:
    "<any prefix>_ <lead_id>"
    contoh: "Requirement E-Proc PT ABC_ 69503"

        ↓ (meeting selesai, TLDV proses transcript)

TLDV: TranscriptReady webhook fires
        ↓ POST body.data.data = array of segments {startTime, endTime, speaker, text}

n8n Workflow (19 nodes)
    ├─ Filter: TranscriptReady only
    ├─ GET /meetings/{meetingId} → ambil meeting metadata (title, invitees, organizer)
    ├─ Regex parse title → extract lead_id
    ├─ Bitrix crm.lead.get → validasi lead exists (di PRODUCTION Bitrix)
    ├─ Reconstruct transcript from segments array
    ├─ Build summarize prompt → Call OpenAI (gpt-5.5) → parse BBCode summary
    ├─ Bitrix crm.timeline.comment.add → post ke Lead timeline
    ├─ Build classifier prompt → Call OpenAI Classifier → decide should_create + suggested_title
    ├─ IF should_create=true → Bitrix crm.item.add (SPA 1070) → link lead via ufCrm11CustomerProposal
    └─ Log Proposal Result (skipped / success / error)
        ↓
Summary tampil di CRM Lead timeline + (kondisional) SPA item baru di "Proposal & Quotation"
```

## Folder Structure

```
tldv-meeting-summary/
├── README.md                              # This file
├── docs/
│   ├── PRD.md                             # Full product requirements + change log
│   ├── TLDV_API_REFERENCE.md              # TLDV API endpoints (verified live)
│   └── BITRIX_LEADS_REFERENCE.md          # Bitrix Leads + timeline comment API
└── workflow/
    ├── tldv-meeting-summary.json                     # v1 baseline (13 nodes, comment only) — rollback safe
    ├── tldv-meeting-summary-with-proposal.json       # v2 extended (19 nodes, with auto SPA) — CURRENT in production
    └── IMPORT_GUIDE.md                    # How to import both versions + side-by-side compare
```

## Bitrix Instance

**PRODUCTION** — `askarasoft.bitrix24.com` (bukan `askarasoftdemo`).

⚠️ Different dari Project 1 (yang di demo). Lead real customer ada di sini.

## Shared Infrastructure

n8n stack, VPS, dan AI API key di-share dengan Project 1 (proposal-estimation).
Lihat `../deploy/` di root untuk shared deployment config.

- **VPS**: `<vps_ip>` (lihat memory.md / credentials.md)
- **n8n UI**: https://n8n.askarasoft.com (HTTPS via Caddy)
- **Webhook endpoint**: `https://n8n.askarasoft.com/webhook/tldv-transcript-ready`
- **AI provider**: OpenAI gpt-5.5 (reasoning model)
- **Bitrix env vars**:
  - `BITRIX_WEBHOOK_BASE_URL` → askarasoftdemo (dipakai Project 1)
  - `BITRIX_PROD_URL` → askarasoft (dipakai Project 2 ini)
- **TLDV**: `TLDV_API_KEY` env var untuk fetch metadata

## Quick Start

1. **Import workflow** — see [`workflow/IMPORT_GUIDE.md`](workflow/IMPORT_GUIDE.md)
2. **Setup TLDV webhook** — di TLDV admin panel, subscribe `TranscriptReady` → point ke n8n webhook URL

## Related

- Project 1 (Proposal Estimation): `../proposal-estimation/`
- Shared infra: `../deploy/`
- Root overview: `../README.md`
