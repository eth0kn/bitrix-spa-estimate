# TLDV Meeting Summary → Bitrix24 Timeline Comment

Otomatisasi meeting summary: TLDV rekam meeting → transcript siap → n8n summarize via AI → post ke Bitrix24 Lead sebagai timeline comment.

## Flow

```
Sales bikin meeting di Zoom dengan judul format:
    "meeting askarasoft with pt <company>_ <lead_id>"
    contoh: "meeting askarasoft with pt abc_ 4759"

        ↓ (meeting selesai, TLDV proses transcript)

TLDV: TranscriptReady webhook fires
        ↓ POST { data: { meetingId, data: { transcript, segments } } }

n8n Workflow (tldv-meeting-summary)
    ├─ GET /meetings/{meetingId} → ambil meeting metadata (name/title)
    ├─ Regex parse title → extract lead_id (angka setelah "_ ")
    ├─ Bitrix crm.lead.get?ID={lead_id} → validasi lead exists
    ├─ Build summarize prompt + transcript
    ├─ Call OpenAI (gpt-5.5)
    ├─ Parse BBCode-formatted summary
    └─ Bitrix crm.timeline.comment.add → post ke lead timeline

        ↓

Summary tampil di CRM Lead → tab Timeline → sebagai comment
```

## Repo Structure (This Subfolder)

```
tldv-meeting-summary/
├── README.md
├── docs/
│   ├── PRD.md                      # Full product requirements
│   ├── TLDV_API_REFERENCE.md       # TLDV API endpoints we use
│   └── BITRIX_LEADS_REFERENCE.md   # Bitrix Leads + timeline comment API
└── workflow/
    └── (workflow JSON — TBD)
```

## Shared Infrastructure

n8n stack + VPS dipakai bareng dengan Project 1 (proposal-estimation). Lihat `../deploy/` di root.

- **VPS**: sama (46.250.226.221)
- **n8n instance**: sama (http://46.250.226.221:5678)
- **AI provider**: OpenAI gpt-5.5 (reuse API key project 1)
- **Bitrix domain**: sama (askarasoftdemo.bitrix24.com)

## Status

📝 **Planning phase** — PRD dalam draft. Belum ada workflow code.

## Related

- Project 1 (Proposal Estimation): root folder — SPA integration
- Root README: overview kedua project
