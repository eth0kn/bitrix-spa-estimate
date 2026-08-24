# PRD — TLDV Meeting Summary ↔ n8n ↔ Bitrix24 Timeline Comment

| Field | Value |
|---|---|
| Document Version | 1.2 (Implemented + Extended) |
| Last Updated | 2026-08-24 |
| Status | ✅ Live in production (v2 workflow deployed) |
| Project Codename | tldv-meeting-summary |
| Customer | PT Len (via Askarasoft) — PIC: Michael Chandra |
| Related Project | Project 1: Bitrix SPA Proposal Estimation (`../proposal-estimation/`) |

## Change Log

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-08 | Initial draft — TLDV → n8n → OpenAI → Bitrix Lead comment |
| 1.0 | 2026-07-09 | Implemented v1 baseline (13 nodes). Comment posting works. HTTPS via Caddy live. |
| 1.1 | 2026-07-15 | **Critical fix**: TLDV real webhook payload uses `body.data.data` as array of segments (not `{transcript, segments}` object per initial research). Reconstruct transcript from segments. Also switched Bitrix from `askarasoftdemo` (demo) to `askarasoft` (production) via new env var `BITRIX_PROD_URL`. Verified: Comment #408245 posted with real transcript content to Lead 69503. |
| 1.2 | 2026-07-17 | **Extension**: v2 workflow adds auto-create SPA "Proposal & Quotation" (entityTypeId=1070) when AI classifier detects action item requesting proposal. 6 new nodes appended after "Bitrix: Post Timeline Comment" (existing behavior preserved). Comprehensive Log Proposal Result for skipped/success/error paths. Verified end-to-end: SPA #621 auto-created for Test A, correctly skipped for Test B. |

## Bitrix Instance Used

**PRODUCTION** — `askarasoft.bitrix24.com` (Michael provided webhook token via `BITRIX_PROD_URL` env var). Lead real customer di sini.

Different from Project 1 which uses `askarasoftdemo.bitrix24.com` (demo, karena SPA 2098 hanya ada di demo).

---

## 1. Background

Sales team melakukan meeting via Zoom yang otomatis di-record dan di-transkrip oleh **TLDV** (Askarasoft sudah punya subscription — verified 657 meetings historical di 2026-07). Saat ini, hasil transcript disimpan di TLDV app; Sales harus manual buka, baca, dan ketik ringkasan ke CRM Bitrix24 sebagai catatan follow-up. Manual → time-consuming, tidak konsisten, sering kelewat.

Customer ingin **mengotomatisasi**: begitu TLDV selesai bikin transcript, sistem otomatis summarize (via AI) dan post hasilnya sebagai timeline comment di CRM Lead yang relevan. Sales tinggal review.

## 2. Goals & Non-Goals

### 2.1 Goals
- Hilangkan manual step "buka TLDV → salin → summarize → paste ke Bitrix"
- Summary konsisten (structured, sales-oriented)
- Latency < 2 menit dari meeting selesai (transcript ready) sampai comment muncul di Lead
- Reusable AI provider & infra existing (share n8n stack dengan Project 1)

### 2.2 Non-Goals (Out of Scope)
- Auto-detect lead dari attendee email (Phase 2 candidate — see §17)
- Auto-generate follow-up email atau task (Phase 2)
- Sentiment analysis / talk-time analytics
- Support platform meeting lain (Google Meet, Teams) — TLDV integrasi Zoom-only untuk sekarang
- Bikin meeting link di Bitrix (Sales tetap create meeting manual di Zoom/TLDV)

## 3. Stakeholders

| Role | Party | Responsibility |
|---|---|---|
| Product Owner | Michael Chandra | Approve scope, provide TLDV/AI/Bitrix creds |
| Sales Team | PT Len sales | Naming meeting sesuai konvensi (lihat §12) |
| Implementer | Vendor (kita) | n8n workflow build + deploy |
| Bitrix Admin | (customer) | Nothing baru (comment API sudah tersedia native) |
| TLDV Admin | (customer) | Setup webhook TLDV → n8n endpoint |

## 4. User Stories

- **US-01** — Sebagai Sales, saya ingin selesai meeting Zoom, ~2 menit kemudian summary otomatis muncul di Lead terkait, supaya saya tidak perlu manual copy-paste transcript.
- **US-02** — Sebagai Sales Manager, saya ingin summary punya struktur konsisten (attendees, discussion, decisions, pain points, action items, next steps), supaya cepat scan untuk semua meeting.
- **US-03** — Sebagai Product Owner, saya ingin bisa ubah prompt AI dari n8n UI, supaya bisa iterate style summary tanpa hubungi vendor.
- **US-04** — Sebagai Sales, kalau lupa naming meeting sesuai konvensi, saya ingin tahu (via error log / notif) supaya bisa fix retroactively.

## 5. System Architecture

### 5.1 High-Level Flow

```
[Sales] create Zoom meeting with title: "meeting askarasoft with pt <company>_ <lead_id>"
   │
   ▼
[TLDV] records meeting → generates transcript (delay: ~1-5 min post-meeting)
   │
   ▼ event: TranscriptReady (POST webhook)
   │ payload: { data: { meetingId, data: { transcript, segments } } }
   ▼
[n8n Workflow: tldv-meeting-summary]
   │
   ├─► [HTTP GET] TLDV /v1alpha1/meetings/{meetingId} → get meeting metadata (name/title/etc)
   ├─► [Regex] extract lead_id from meeting name (pattern: _\s*(\d+)\s*$)
   ├─► [IF] lead_id valid? (numeric, non-empty)
   │     └─ NO → error branch: log + notify
   ├─► [HTTP POST] Bitrix crm.lead.get → validate lead exists
   │     └─ 404/not found → error branch
   ├─► [Function] Build summarize prompt from transcript + template
   ├─► [HTTP POST] OpenAI /v1/chat/completions (gpt-5.5) → summarize
   ├─► [Function] Extract BBCode-formatted summary
   └─► [HTTP POST] Bitrix crm.timeline.comment.add → post to lead timeline
   ▼
[Bitrix Lead Timeline] shows AI-generated meeting summary as comment
```

### 5.2 Component Inventory

| Komponen | Lokasi | Tanggung Jawab |
|---|---|---|
| TLDV cloud | tldv.io / pasta.tldv.io | Meeting recording + transcript generation |
| n8n workflow (this) | shared VPS n8n instance (port 5678) | Orchestration |
| OpenAI API | api.openai.com | Summarization (gpt-5.5) |
| Bitrix24 | askarasoft.bitrix24.com (PRODUCTION) | Lead source of truth + timeline UI |

Shared with Project 1: n8n instance, Postgres, VPS, OpenAI key, Bitrix webhook token.

## 6. Data Contracts

### 6.1 TLDV TranscriptReady Webhook (Inbound)

```json
{
  "id": "webhook-<uuid>",
  "event": "TranscriptReady",
  "data": {
    "id": "<meetingId>",
    "meetingId": "<meetingId>",
    "data": {
      "transcript": "Hello everyone, welcome ...",
      "segments": [
        { "startTime": 0, "endTime": 5, "text": "..." }
      ]
    }
  },
  "executedAt": "2026-07-08T10:35:00Z"
}
```

### 6.2 TLDV Meeting Metadata (via GET /meetings/{id})

Fields returned (verified via live test):
```json
{
  "id": "6a4dbd36912a5400133f688a",
  "name": "Bitrix24 E-Procurement Intro - Askarasoft Hybrid Meeting with pt abc_ 4759",
  "happenedAt": "2026-07-08T03:00:00.000Z",
  "duration": 7049.038,
  "invitees": [{"name": "", "email": "michael@askarasoft.com"}],
  "organizer": {"name": "Askarasoft", "email": "marketing@askarasoft.net"},
  "url": "https://tldv.io/app/meetings/6a4dbd36912a5400133f688a",
  "template": {"id": "ai-topics", "label": "Smart topics"},
  "extraProperties": {"conferenceId": "kdz-ppdt-ncg"}
}
```

The `name` field contains the meeting title where we parse `lead_id`.

### 6.3 Bitrix Lead (crm.lead.get response)

Fields we care about:
- `ID`
- `TITLE`
- `NAME`, `LAST_NAME`
- `EMAIL`, `PHONE`
- `STATUS_ID`
- `ASSIGNED_BY_ID`

### 6.4 Bitrix Timeline Comment Add (Outbound)

```json
{
  "fields": {
    "ENTITY_ID": <lead_id>,
    "ENTITY_TYPE": "lead",
    "COMMENT": "<BBCode-formatted summary>"
  }
}
```

Response: `{ "result": <comment_id> }`.

## 7. Meeting Title Parsing

### 7.1 Convention (enforced by Sales)

Format:
```
<any prefix>_ <numeric lead_id>
```

Contoh valid:
- `meeting askarasoft with pt abc_ 4759`
- `Follow-up call PT XYZ_ 5001`
- `Sales meeting_ 4759`

### 7.2 Regex

```javascript
const match = meetingName.match(/_\s*(\d+)\s*$/);
const leadId = match ? parseInt(match[1], 10) : null;
```

### 7.3 Fallback (kalau tidak match)

- Workflow log error dengan meeting name asli
- Notify (email/Telegram) ke Michael/Sales lead
- Meeting summary tetap dibuat & disimpan (opsional Phase 2: post ke "orphan meetings" folder atau Deal generic)
- v1 default: **skip Bitrix comment, log error, exit gracefully**

## 8. AI Summarization Prompt

### 8.1 Style Target (structured + sales-oriented)

Output berformat BBCode dengan section:

```
[b]Meeting Summary[/b]

[b]Attendees:[/b]
- Nama 1 (email)
- Nama 2 (email)

[b]Duration:[/b] X menit

[b]Discussion Highlights:[/b]
- Point 1
- Point 2

[b]Client Pain Points / Needs:[/b]
- ...

[b]Decisions Made:[/b]
- ...

[b]Action Items:[/b]
- [ ] Owner: Task (Due: date)

[b]Next Steps:[/b]
- ...

[b]Sales Signals:[/b]
- Budget: ...
- Timeline: ...
- Decision-maker: ...
- Objections: ...
```

### 8.2 Prompt Template (v0 draft)

```
Anda adalah AI assistant untuk sales team. Berikut transcript meeting Zoom.
Buat ringkasan terstruktur dalam format BBCode Bitrix24 (bukan HTML, bukan markdown).

Gunakan format PERSIS ini (skip section yang tidak relevan):

[b]Meeting Summary[/b]

[b]Attendees:[/b]
- Nama (email)

[b]Duration:[/b] X menit

[b]Discussion Highlights:[/b]
- ...

[b]Client Pain Points / Needs:[/b]
- ...

[b]Decisions Made:[/b]
- ...

[b]Action Items:[/b]
- Owner: Task (Due: date jika disebutkan)

[b]Next Steps:[/b]
- ...

[b]Sales Signals:[/b]
- Budget: ... (kalau ada indikasi)
- Timeline: ... (kalau ada indikasi kapan launch/deadline)
- Decision-maker: ... (kalau ada indikasi siapa yang punya kata final)
- Objections: ... (kalau ada concern spesifik dari client)

== METADATA MEETING ==
Nama: {{ meeting_name }}
Tanggal: {{ happened_at }}
Durasi: {{ duration_minutes }} menit
Organizer: {{ organizer }}
Attendees: {{ attendees_joined }}

== TRANSCRIPT ==
{{ transcript }}

== ATURAN ==
- Bahasa Indonesia
- BBCode SAJA (no HTML, no markdown)
- Gunakan \n untuk newline (Bitrix parse ini sebagai break)
- Section boleh di-skip kalau tidak ada info dari transcript
- Ringkas & to-the-point, jangan verbose
- Bahasa formal profesional
- Kalau ada speaker tidak dikenal, tulis "Peserta"
```

Prompt disimpan di node Set editable — bisa iterate tanpa touch node lain.

## 9. n8n Workflow Design (Draft)

Node sequence (~10 nodes):

| # | Node | Type | Purpose |
|---|---|---|---|
| 1 | Webhook (TLDV Trigger) | Webhook | POST /webhook/tldv-transcript-ready |
| 2 | Filter Event | IF | body.event == "TranscriptReady" |
| 3 | Extract Meeting ID | Set | body.data.meetingId → $json.meeting_id |
| 4 | Get Meeting Metadata | HTTP | GET pasta.tldv.io/v1alpha1/meetings/{id} |
| 5 | Parse Lead ID from Title | Code | regex extract, validate numeric |
| 6 | IF Lead ID Valid? | IF | branch to error handler if not |
| 7 | Get Bitrix Lead | HTTP | POST crm.lead.get → validate exists |
| 8 | Build Summarize Prompt | Set | template + metadata + transcript |
| 9 | Call OpenAI (gpt-5.5) | HTTP | POST /v1/chat/completions |
| 10 | Extract AI Summary | Set | choices[0].message.content |
| 11 | Post Comment to Bitrix | HTTP | POST crm.timeline.comment.add |
| (err) | Log & Notify Error | Set + HTTP | log to n8n execution + optional Telegram |

## 10. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Terima TranscriptReady webhook dari TLDV | MUST |
| FR-02 | Fetch meeting metadata via TLDV GET endpoint | MUST |
| FR-03 | Parse lead_id dari meeting name via regex | MUST |
| FR-04 | Validasi lead_id existence di Bitrix sebelum comment | MUST |
| FR-05 | Summarize transcript via OpenAI gpt-5.5 | MUST |
| FR-06 | Format output sebagai BBCode Bitrix-compatible | MUST |
| FR-07 | Post comment ke Bitrix Lead timeline via `crm.timeline.comment.add` | MUST |
| FR-08 | Prompt editable dari n8n UI | MUST |
| FR-09 | Error handling: lead_id gagal parse → log + skip | MUST |
| FR-10 | Error handling: lead tidak ada di Bitrix → log + skip | MUST |
| FR-11 | Idempotency: skip duplicate webhook (same meetingId) | SHOULD |
| FR-12 | Filter webhook by event type (ignore MeetingReady dll) | SHOULD |
| FR-13 | Notif error via Telegram/email | NICE |
| FR-14 | Support Deal in addition to Lead | NICE |
| FR-15 | Chunk long transcript (>50k tokens) | NICE |

## 11. Non-Functional Requirements

| Kategori | Requirement |
|---|---|
| Performance | End-to-end latency <2 menit dari TranscriptReady → comment visible di Bitrix |
| Availability | Uptime target 99% (shared n8n, single VPS) |
| Security | TLDV API key + OpenAI key + Bitrix token semua via env var, tidak hardcode |
| Scalability | Handle ~10 meetings/hari initially. Bitrix ~2 req/sec limit → aman untuk volume ini |
| Maintainability | Workflow JSON di Git, prompt editable in-UI, dokumentasi lengkap |
| Compliance | Transcript berisi discussion internal — sudah ke OpenAI dengan disclaimer (sama seperti Project 1) |

## 12. Security Considerations

- **TLDV API key** (`caf5ab70-...`): treat as secret. Simpan di n8n env var (`TLDV_API_KEY`), tidak commit.
- **TLDV webhook endpoint**: no HMAC/signature by default. Recommendation:
  - Tambahkan **secret token di URL path**: `/webhook/tldv-transcript-ready/<random-secret>` — bandingkan di n8n
  - Atau minta Michael setup **shared secret header** di TLDV admin (kalau supported)
- **Bitrix webhook token**: sama dengan Project 1, sudah aman di env var
- **OpenAI key**: sama, di env var
- **Data privacy**: transcript may contain client-confidential info — Michael sudah accept ini di Project 1 dengan disclaimer OpenAI API-not-training

## 13. Assumptions

- A-01: TLDV subscription Askarasoft aktif dan bisa setup outbound webhook (verified: 657 meetings recorded).
- A-02: Sales team akan comply naming convention `<prefix>_ <lead_id>` setelah dilatih.
- A-03: Volume meeting ≤20/hari initial. n8n shared instance cukup.
- A-04: Bitrix Lead ID selalu numeric integer.
- A-05: TLDV TranscriptReady payload include transcript inline (verified via doc research).
- A-06: OpenAI gpt-5.5 support prompt panjang (transcript bisa 20-50 min meeting ≈ 3000-10000 kata).

## 14. Open Questions (perlu dikonfirmasi customer)

| ID | Question | Impact |
|---|---|---|
| OQ-1 | Volume meeting perkiraan per hari? | Sizing + potential rate-limit strategy |
| OQ-2 | Michael mau notifikasi kalau workflow error? (channel: email/Telegram/Bitrix chat) | Error handling design |
| OQ-3 | Sales team siap dilatih naming convention? Atau perlu fuzzy fallback? | Determine strictness of regex |
| OQ-4 | Support Deal juga (tidak cuma Lead)? Kalau ya, gimana bedain di judul meeting? | Scope |
| OQ-5 | Backfill: mau proses meeting historical (657 existing) juga, atau cuma yang new? | Migration one-time |

## 15. Acceptance Criteria

MVP dianggap selesai jika:

- [ ] AC-01: Meeting selesai → 2 menit kemudian comment muncul di Bitrix Lead yang di-reference judulnya.
- [ ] AC-02: Comment berisi structured summary sesuai format BBCode (§8.1).
- [ ] AC-03: BBCode di-render Bitrix jadi bold section + newline (bukan raw text `[b]...[/b]`).
- [ ] AC-04: Kalau judul meeting tidak match regex → tidak crash workflow; error ter-log di n8n executions.
- [ ] AC-05: Kalau lead_id tidak ada di Bitrix → tidak crash; error ter-log.
- [ ] AC-06: Prompt bisa di-edit dari n8n UI, perubahan berlaku untuk meeting berikutnya tanpa restart.
- [ ] AC-07: Test dengan minimal 3 real meeting dari TLDV Askarasoft (naming disesuaikan).

## 16. Milestones & Estimated Timeline

| Fase | Deliverable | Estimasi |
|---|---|---|
| M1 — PRD sign-off & OQ resolved | Michael approve PRD | 1-2 hari |
| M2 — Env setup | TLDV_API_KEY added to VPS, webhook URL ready | 30 menit |
| M3 — Workflow build | 11-node workflow, importable JSON | 2-3 hari |
| M4 — Prompt iterasi | Test dengan 3-5 sample meeting, tune output | 1-2 hari |
| M5 — Bitrix side setup | Michael setup TLDV → webhook (from tldv admin) | 30 menit (customer side) |
| M6 — UAT & handover | End-to-end test + docs handover | 1 hari |
| **TOTAL** | | **~5-7 hari kerja** |

## 17. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Sales tidak comply naming convention | High | Medium | v2: fuzzy match by attendee email / meeting title semantic search |
| TLDV `/v1alpha1/` breaking change | Low | Medium | Monitor doc, wrap in error handler, log unknown response format |
| Bitrix comment BBCode tidak render properly | Low | Low | Test v0, adjust prompt kalau ada issue |
| Long transcript (2+ jam meeting) exceed AI context | Medium | Medium | Chunk transcript, OR summarize per section then combine |
| Lead ID collision (Deal ID 4759 & Lead ID 4759) | Low | Medium | Explicit ENTITY_TYPE=lead di comment API |
| TLDV webhook fire multiple times (retry) | Medium | Low | Idempotency: dedupe by meetingId in n8n (Postgres check) |

## 18. Out of Scope (Eksplisit)

- Membuat meeting link (Sales tetap create manual di Zoom/TLDV app)
- Setup TLDV account/subscription
- Bitrix Lead custom fields creation (comment tidak perlu new field)
- Real-time transcript (streaming) — kita cuma proses post-meeting
- Summary translation (Bahasa Indonesia only untuk v1)
- Face detection / video analysis / sentiment
- Auto-schedule follow-up

## 19. Glossary

| Term | Definisi |
|---|---|
| TLDV | Meeting recording + transcription SaaS untuk Zoom (tldv.io) |
| Transcript | Text output dari speech recognition |
| BBCode | Format markup ala forum (`[b]bold[/b]`) — Bitrix native |
| Lead | Entity di Bitrix CRM untuk prospect yang belum jadi Deal |
| Timeline comment | Text/HTML note attached ke entity Bitrix, shown chronologically di UI |

---

## Appendix A — Sample Comment (target output visual di Bitrix)

Untuk meeting "Follow-up call PT ABC_ 4759", output di Bitrix Lead 4759 → Timeline:

> **Meeting Summary**
>
> **Attendees:**
> - Michael (michael@askarasoft.com)
> - Budi (budi@ptabc.com)
> - Sari (sari@ptabc.com)
>
> **Duration:** 45 menit
>
> **Discussion Highlights:**
> - Review demo Bitrix24 procurement module
> - Concern integrasi dengan SAP existing
> - Budget internal sudah approved untuk Q3
>
> **Client Pain Points / Needs:**
> - Manual approval flow saat ini lambat (rata-rata 5 hari)
> - Compliance audit trail requirement (BPK)
>
> **Decisions Made:**
> - Approval untuk phase 1: SAP-Bitrix integration
> - Timeline pilot: Q3 2026 (Sep launch)
>
> **Action Items:**
> - Michael: Kirim technical proposal + timeline (Due: 2026-07-15)
> - Budi (PT ABC): Info technical SAP contact person (Due: 2026-07-10)
>
> **Next Steps:**
> - Technical workshop dengan tim IT PT ABC minggu depan
>
> **Sales Signals:**
> - Budget: approved Q3 (~ Rp 500jt indication)
> - Timeline: launch Sep 2026
> - Decision-maker: Bu Budi (Head of Procurement) + IT Director
> - Objections: SAP integration complexity, need reassurance

## Appendix B — References

- TLDV API docs: https://doc.tldv.io/index.html
- TLDV Webhook triggers: https://doc.tldv.io/index.html#section/Webhook-Feature/Available-Triggers
- TLDV Get Transcript: https://doc.tldv.io/index.html#tag/Transcripts/operation/GetTranscriptByMeetingId
- Bitrix crm.lead.list: https://apidocs.bitrix24.com/api-reference/crm/leads/crm-lead-list.html
- Bitrix crm.lead.get: https://apidocs.bitrix24.com/api-reference/crm/leads/crm-lead-get.html
- Bitrix crm.timeline.comment.add: https://apidocs.bitrix24.com/api-reference/crm/timeline/comments/crm-timeline-comment-add.html

---

**Sign-off**

| Role | Name | Date | Signature |
|---|---|---|---|
| Customer (Product Owner) | Michael Chandra | __________ | __________ |
| Implementer | (Mas) | __________ | __________ |
