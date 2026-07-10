# n8n Workflow Import Guide — TLDV Meeting Summary

> File workflow: `tldv-meeting-summary/workflow/tldv-meeting-summary.json`
> Tujuan: import ke n8n instance yang sudah ada, jadi workflow kedua (Project 1 tetap jalan).

## Prerequisites (sudah selesai)

- ✅ n8n deployed di http://46.250.226.221:5678
- ✅ Owner account (n8n@bitrix.com — see memory.md)
- ✅ Env vars sudah di-passthrough: `TLDV_API_KEY`, `OPENAI_API_KEY`, `BITRIX_WEBHOOK_BASE_URL`

## Step 1 — Copy JSON ke Clipboard

Buka PowerShell:

```powershell
Get-Content "C:\Users\KN\Documents\Projects\bitrix\tldv-meeting-summary\workflow\tldv-meeting-summary.json" -Raw | Set-Clipboard
Write-Host "TLDV workflow di clipboard"
```

## Step 2 — Import di n8n

1. Buka http://46.250.226.221:5678 → login
2. Sidebar: **Workflows** → klik **`+ Create workflow`**
3. Di canvas kosong "Add first step..." → **`Ctrl+V`**
4. 13 node ter-render otomatis, tersambung dalam flow
5. **Ctrl+S** save → nama default "TLDV Meeting Summary → Bitrix Lead Comment"

## Step 3 — Publish

1. Pojok kanan atas: klik **Publish** → toggle jadi hijau
2. Webhook URL akan tersedia. Klik node "Webhook (TLDV Trigger)" → copy Production URL:
   ```
   http://46.250.226.221:5678/webhook/tldv-transcript-ready
   ```

## Step 4 — Manual Test (Sebelum Setup TLDV Webhook)

Test dengan payload dummy — pakai meeting ID real dari TLDV Askarasoft:

```powershell
$body = @'
{
  "id": "test-webhook-1",
  "event": "TranscriptReady",
  "data": {
    "id": "6a4dbd36912a5400133f688a",
    "meetingId": "6a4dbd36912a5400133f688a",
    "data": {
      "transcript": "Michael: Hi tim, terima kasih sudah joint hari ini. Kita mau bahas requirement e-procurement. Budi: Betul mas, kita butuh sistem yang bisa integrate dengan SAP existing. Michael: Oke, kita ada 3 opsi implementasi. Fase 1 akan fokus di procurement request module dulu, budget kami sekitar 500 juta untuk Q3. Timeline launch September 2026. Budi: Setuju, tapi tolong include audit trail juga karena BPK requirement. Michael: Noted. Action item saya kirim proposal Jumat depan, mas Budi info tim IT SAP contact.",
      "segments": []
    }
  },
  "executedAt": "2026-07-08T10:35:00Z"
}
'@

Invoke-RestMethod -Uri "http://46.250.226.221:5678/webhook/tldv-transcript-ready" -Method POST -ContentType "application/json" -Body $body
```

⚠️ **Note**: Meeting real "6a4dbd36912a5400133f688a" ada di TLDV, tapi title-nya "Bitrix24 E-Procurement Intro - Askarasoft Hybrid Meeting with Margocity Mall" (tidak match regex `_<digits>`). Jadi test ini akan flow ke branch **"Log Skip Reason"** — expected behavior. Untuk test happy path, buat meeting di TLDV dengan title format sesuai konvensi (`..._ <lead_id>`) atau test dengan meeting ID yang tidak ada di TLDV (akan gagal di step 4).

**Happy path test** (test dengan lead ID valid di Bitrix):
- Cari salah satu Lead ID valid di Bitrix (mis 4759, 4757, 4755)
- Bikin meeting real di TLDV dengan judul: `Test meeting_ 4759`
- Setelah transcript ready, TLDV webhook akan fire otomatis

## Step 5 — Cek Hasil

**Di n8n**: sidebar workflow → **Executions** tab → lihat execution terbaru:
- ✅ Semua node hijau → happy path
- 🟡 Branch ke "Log Skip Reason" → title parse gagal atau lead tidak ada (bukan crash, expected)
- ❌ Merah di node manapun → real error, klik untuk detail

**Di Bitrix**: buka Lead detail → tab **Timeline** → harusnya ada comment baru dengan BBCode formatted summary.

## Step 6 — Setup TLDV Webhook (Michael side, saat siap production)

Michael perlu login TLDV admin panel → Settings → Webhooks → Add:
- **URL**: `http://46.250.226.221:5678/webhook/tldv-transcript-ready`
- **Event**: `TranscriptReady`
- **Method**: POST (auto)

Setelah setup, setiap meeting yang transcript-nya ready akan otomatis fire.

## Struktur Workflow

```
[1] Webhook (TLDV Trigger)                       ← POST /webhook/tldv-transcript-ready
         ↓
[2] Filter: TranscriptReady?                     ← IF body.event == "TranscriptReady"
    ├─ true                                       ← lanjut
    └─ false                                      ← ignore (short-circuit)
         ↓
[3] Extract Meeting ID                           ← body.data.meetingId
         ↓
[4] TLDV: Get Meeting Metadata                   ← GET pasta.tldv.io/v1alpha1/meetings/{id}
         ↓
[5] Parse Lead ID from Title                     ← regex /_\s*(\d+)\s*$/
         ↓
[6] IF Lead ID Valid?
    ├─ true                                       ↓
    └─ false → [Log Skip Reason]
         ↓
[7] Bitrix: Get Lead (validate)                  ← POST crm.lead.get
         ↓
[8] IF Lead Exists?
    ├─ true                                       ↓
    └─ false → [Log Skip Reason]
         ↓
[9] Build Summarize Prompt (EDIT ME)             ← template + metadata + transcript
         ↓
[10] Call OpenAI (gpt-5.5)                       ← chat/completions
         ↓
[11] Extract AI Summary                          ← choices[0].message.content
         ↓
[12] Bitrix: Post Timeline Comment               ← POST crm.timeline.comment.add
```

## Editable Untuk Michael

### A. Prompt Summary
Klik node **"Build Summarize Prompt (EDIT ME)"** → edit field `prompt` → Ctrl+S.

Placeholder yang tersedia:
- `{{ $('Parse Lead ID from Title').item.json.meeting_name }}` — nama meeting
- `{{ $('Parse Lead ID from Title').item.json.happened_at }}` — tanggal meeting
- `{{ $('Parse Lead ID from Title').item.json.duration_minutes }}` — durasi (menit)
- `{{ $('Parse Lead ID from Title').item.json.organizer }}` — organizer
- `{{ $('Parse Lead ID from Title').item.json.attendees }}` — attendees list
- `{{ $('Parse Lead ID from Title').item.json.transcript }}` — full transcript
- `{{ $('Parse Lead ID from Title').item.json.lead_id }}` — Bitrix lead ID
- `{{ $json.result?.TITLE }}` — Bitrix Lead title (dari `crm.lead.get`)

### B. Regex Parsing Rule
Klik node **"Parse Lead ID from Title"** → di code, ada block comment dengan alternatif regex untuk format berbeda (`#`, `[]`, `lead:`, dll).

### C. Ganti Model AI
Sama seperti Project 1 — klik node "Call OpenAI (gpt-5.5)" → edit `jsonBody` → ganti model string. Ingat: gpt-5.x pakai `max_completion_tokens`, gpt-4.x pakai `max_tokens`.

## Troubleshooting

| Gejala | Cek |
|---|---|
| Webhook return 404 | Workflow belum di-Publish. Toggle Publish di kanan atas. |
| Node "TLDV: Get Meeting Metadata" gagal (401) | `TLDV_API_KEY` env var tidak set / salah. Verify: `ssh root@... docker exec n8n env \| grep TLDV` |
| Node "Bitrix: Get Lead" success tapi flow lanjut ke Log Skip | Lead ID tidak ada di Bitrix. Cek Lead di Bitrix UI. |
| Bitrix comment tampil raw `[b]...[/b]` | Bitrix tidak render BBCode — coba edit prompt supaya output plain text tanpa BBCode. |
| Response OpenAI kosong (finish_reason=length) | `max_completion_tokens` terlalu kecil. Bump ke 8000-10000 (reasoning model butuh besar). |
