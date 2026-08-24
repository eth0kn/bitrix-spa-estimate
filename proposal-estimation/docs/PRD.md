# PRD — Bitrix24 ↔ n8n ↔ AI Proposal Estimation

| Field | Value |
|---|---|
| Document Version | 0.1 (Draft) |
| Last Updated | 2026-05-13 |
| Status | Draft — pending customer clarification on 3 minor items |
| Project Codename | bitrix-ai-estimation |
| Customer | PT Len (via Askarasoft) — PIC: Michael Chandra |
| Vendor / Implementer | (Mas / Tim Internal) |

---

## 1. Background

Customer (PT Len) saat ini menggunakan AI (manual via ChatGPT / sejenisnya) untuk membuat estimasi mandays proposal proyek. Prosesnya manual: PIC sales menyusun prompt, mengetik data project, lalu menyalin hasil estimasi kembali ke sistem CRM mereka (Bitrix24).

Customer ingin **mengotomatisasi proses ini** dengan integrasi langsung antara Bitrix24 → n8n → AI → Bitrix24, sehingga Sales hanya perlu mengisi form di Bitrix24 dan hasil estimasi otomatis muncul di field yang sudah disiapkan.

## 2. Goals & Non-Goals

### 2.1 Goals
- Menghilangkan langkah copy-paste manual antara Bitrix24 dan AI.
- Memastikan format dan struktur prompt **konsisten** untuk semua proposal.
- Memberi customer fleksibilitas untuk **edit prompt sendiri** di n8n tanpa harus hubungi vendor.
- Mempercepat siklus pembuatan estimasi awal proposal.

### 2.2 Non-Goals (Out of Scope)
- Membangun form atau Business Process di sisi Bitrix24 (sudah disediakan customer).
- Menyediakan API key OpenAI / Gemini (default: customer yang sediakan & bayar — tunggu konfirmasi).
- Training Sales menggunakan fitur (handover dokumentasi singkat sudah cukup).
- Customisasi UI Bitrix24 (field render, dashboard, dsb.).
- Migrasi data historis proposal lama.
- Audit trail / reporting analytics atas penggunaan AI.

## 3. Stakeholders

| Role | Name / Party | Responsibility |
|---|---|---|
| Product Owner / Customer | Michael Chandra (PT Len) | Approve scope, sediakan akses Bitrix24 & sample data |
| Bitrix24 Admin (Customer side) | (TBD) | Setup BP, webhook outbound, create custom fields jika perlu |
| Implementer | Mas (Vendor) | Deploy n8n, bangun workflow, integrasi API |
| End User | Sales Team PT Len | Mengisi form SPA di Bitrix24 |
| Server Provider | Customer | Sediakan VPS / server untuk hosting n8n |

## 4. User Stories

- **US-01** — Sebagai Sales, saya ingin mengisi form proposal di Bitrix24, supaya AI otomatis menghitung estimasi mandays tanpa saya perlu copy-paste ke ChatGPT.
- **US-02** — Sebagai Sales, saya ingin melihat hasil estimasi langsung di field `AI Total Mandays Output` di item SPA, supaya saya bisa langsung gunakan untuk proposal.
- **US-03** — Sebagai Product Owner, saya ingin bisa mengubah isi prompt AI sendiri dari UI n8n, supaya saya bisa improve kualitas estimasi tanpa harus minta vendor.
- **US-04** — Sebagai Product Owner, saya ingin menambah field input baru ke prompt di kemudian hari, supaya prompt bisa berkembang seiring kebutuhan tanpa rebuild workflow.

## 5. System Architecture

### 5.1 High-Level Flow

```
[Sales]
   │
   ▼
[Bitrix24 SPA Form (Proposal Estimation, entityTypeId=2098)]
   │ submit / stage trigger
   ▼
[Bitrix24 Business Process]
   │ outbound webhook (HTTP POST)
   │ payload: { id: <item_id> }
   ▼
[n8n Webhook Endpoint]
   │
   ├─► [HTTP] crm.item.get (ambil full data item)
   ├─► [HTTP] download RFP file via urlMachine
   ├─► [Function] extract text dari PDF
   ├─► [Function] map enum IDs → label readable
   ├─► [Function] build prompt dari template + data
   ├─► [HTTP] call AI (OpenAI / Gemini)
   ├─► [Function] parse response
   └─► [HTTP] crm.item.update (tulis ke ufCrm497AiTotalMandays)
   ▼
[Bitrix24 SPA Item ter-update]
   │
   ▼
[Sales lihat hasil di Bitrix24]
```

### 5.2 Component Inventory

| Komponen | Lokasi | Tanggung Jawab |
|---|---|---|
| Bitrix24 (Cloud) | `askarasoftdemo.bitrix24.com` (dev) / TBD (prod) | Source of truth data SPA, form input, BP trigger |
| n8n | Customer VPS (TBD) | Orchestrator workflow |
| PostgreSQL | Container di VPS yang sama | Database internal n8n |
| Reverse Proxy (Caddy / Nginx) | Container di VPS yang sama | TLS termination, public endpoint |
| AI Provider | OpenAI / Gemini (TBD) | LLM inference |

### 5.3 Deployment

- Single VPS, Docker Compose stack:
  - `n8n` (latest stable)
  - `postgres` (16-alpine)
  - `caddy` atau `nginx` (TLS via Let's Encrypt)
- Domain dedicated untuk n8n: `n8n.<customer-domain>` (TBD).
- Backup: volume Postgres + n8n workflow JSON, scheduled daily.

## 6. Data Model — SPA Proposal Estimation

**Entity Type ID:** `2098`
**Base URL (dev):** `https://askarasoftdemo.bitrix24.com/rest/1177/<YOUR_WEBHOOK_TOKEN>/`

### 6.1 Input Fields (Diisi Sales, masuk ke prompt)

| Field Code | Type | Label | Catatan |
|---|---|---|---|
| `title` | string | Nama Project | Standard field |
| `ufCrm497Summary` | string | Requirement Summary | Deskripsi narrative proyek |
| `ufCrm497FeatureList` | string | Feature List | **Perlu re-verify via `crm.item.fields`** — tidak ada di doc API v1 |
| `ufCrm497UploadRfp` | file | Upload RFP | Returns `{id, url, urlMachine}` — perlu di-download & extract |
| `ufCrm497Platform` | enumeration (multi) | Platform | Web (9011), Mobile (9013), Portal (9015), API (9017) — **multi-select** |
| `ufCrm497IsIntegrate` | enumeration | Integration Required | Yes (9019), No (9021) |
| `ufCrm497IntegrationDetail` | string | Integration Details | Free text |
| `ufCrm497Complexity` | enumeration | Complexity Level | Low (9023), Medium (9025), High (9027) |
| `ufCrm497UserScale` | double | User Scale | Jumlah user |
| `ufCrm497Timeline` | enumeration | Timeline Expectation | Normal (9029), Dipercepat (9031) |

### 6.2 Output Field (Diisi n8n setelah AI selesai)

| Field Code | Type | Label | Format |
|---|---|---|---|
| `ufCrm497AiTotalMandays` | string | AI Total Mandays Output | Multi-line text berisi breakdown item + mandays per item + total. Format final TBD (lihat Open Question OQ-3). |

### 6.3 Contoh Format Output (dari customer sample)

```
1. Data Integration Framework
   • API integration engine
   • Bi-directional sync
   • Event-driven
   → 60 MD

2. Data Cleansing, Enrichment, Update Logic
   → 25 MD

3. Data Grouping & Distribution (Rule Engine)
   → 30 MD

4. Dashboard & Reporting (custom enterprise dashboard)
   → 40 MD

5. Backend & Role Management (enterprise grade RBAC + audit trail enhancement)
   → 25 MD

6. Workflow Automation (approval flow engine enhancement)
   → 35 MD

7. Single Customer 360 View (custom module)
   → 35 MD

8. Profiling & Segmentation Engine
   → ...

TOTAL: <X> MD
```

## 7. API Integration Spec

### 7.1 Inbound: Bitrix24 → n8n

- **Method:** HTTP POST
- **Endpoint:** `https://<n8n-domain>/webhook/bitrix-spa-estimate`
- **Payload (minimal):**
  ```json
  { "id": "<spa_item_id>" }
  ```
- **Auth:** URL secret token (path segment) + opsional shared secret header (TBD).

### 7.2 Outbound: n8n → Bitrix24

Menggunakan inbound webhook Bitrix24 yang sudah ada (`/rest/<user>/<token>/`).

| Endpoint | Tujuan | Required Params |
|---|---|---|
| `crm.item.get` | Ambil full data SPA item | `entityTypeId=2098`, `id` |
| `crm.item.update` | Update field hasil AI | `entityTypeId=2098`, `id`, `fields={ufCrm497AiTotalMandays: "..."}` |
| `crm.item.fields` | (One-time) verify schema | `entityTypeId=2098` |

### 7.3 Outbound: n8n → AI Provider

- **Default plan:** OpenAI Chat Completions API (`gpt-4o` atau `gpt-4o-mini`) atau Gemini `gemini-2.0-flash`.
- Final pilihan menunggu OQ-2.
- Request body: prompt yang sudah di-render + opsional file RFP attachment.
- Response format: structured JSON (preferred) atau plain markdown text.

## 8. n8n Workflow Design

### 8.1 Node Sequence (Main Workflow)

| # | Node | Type | Purpose |
|---|---|---|---|
| 1 | Webhook Trigger | Webhook | Terima POST dari Bitrix24 |
| 2 | Get SPA Item | HTTP Request | POST `crm.item.get` → ambil semua field |
| 3 | Has RFP? | IF | Branch: kalau ada file RFP, lanjut download |
| 4a | Download RFP | HTTP Request | GET `urlMachine` → binary |
| 4b | Extract PDF Text | Code (pdf-parse) | Konversi binary PDF → text |
| 5 | Map Enums | Set / Code | Map ID enum (9011, 9023, dll) → label readable |
| 6 | Build Prompt | Set | Substitute variable ke prompt template (editable) |
| 7 | Call AI | HTTP Request | POST ke OpenAI / Gemini |
| 8 | Parse Response | Code | Ambil text breakdown dari response |
| 9 | Update SPA | HTTP Request | POST `crm.item.update` dengan hasil |
| 10 | Success Notify | (opsional) | Log / Telegram / Email |

### 8.2 Error Handling Workflow (Sub)

- Trigger: workflow utama gagal di node manapun.
- Aksi:
  - Log payload + error detail ke n8n execution log.
  - Kirim notifikasi (channel TBD: email / Telegram bot).
  - Tidak melakukan update partial ke Bitrix24 (rollback by default — tidak update jika AI gagal).
- Retry: 2x untuk error transient (timeout, 5xx). Tidak retry untuk error 4xx (bad input).

### 8.3 Prompt Template Storage

- Prompt disimpan di node "Set" bernama `Prompt Template` di awal workflow.
- Mengandung placeholder dengan format `{{$json.fieldName}}` yang di-substitute otomatis oleh n8n.
- Customer bisa edit langsung dari UI n8n tanpa modifikasi node lain.
- Versioning: gunakan fitur n8n workflow version history.

### 8.4 Adding New Input Field (Customer self-service)

Langkah untuk customer kalau ingin tambah field baru ke prompt:
1. Admin Bitrix24 buat custom field baru di SPA 2098 (misal `ufCrm497NewField`).
2. Di n8n: edit node `Map Enums` (kalau enum) untuk tambah mapping ID → label.
3. Di n8n: edit node `Prompt Template`, tambah baris baru menggunakan `{{$json.result.item.ufCrm497NewField}}`.
4. Test workflow → save.

## 9. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Sistem menerima webhook dari Bitrix24 yang membawa minimal `id` SPA item | MUST |
| FR-02 | Sistem mengambil seluruh field SPA item via `crm.item.get` | MUST |
| FR-03 | Sistem men-download file RFP (jika ada) dan extract teks dari PDF | MUST |
| FR-04 | Sistem mapping enum ID ke label readable sebelum masuk prompt | MUST |
| FR-05 | Sistem mengirim prompt + data ke AI provider | MUST |
| FR-06 | Sistem menulis hasil AI ke field `ufCrm497AiTotalMandays` via `crm.item.update` | MUST |
| FR-07 | Prompt template dapat diedit langsung di UI n8n tanpa coding | MUST |
| FR-08 | Sistem log setiap eksekusi (success/error) di n8n execution history | MUST |
| FR-09 | Sistem kirim notifikasi (channel TBD) kalau workflow gagal | SHOULD |
| FR-10 | Sistem retry 2x untuk error transient sebelum gagal final | SHOULD |
| FR-11 | Sistem support format file RFP selain PDF (DOCX) | NICE-TO-HAVE |
| FR-12 | Sistem support OCR untuk RFP scan (image-based PDF) | NICE-TO-HAVE |

## 10. Non-Functional Requirements

| Kategori | Requirement |
|---|---|
| Performance | End-to-end latency target: <60 detik dari webhook trigger sampai field ter-update (kondisi normal, RFP <10 halaman) |
| Availability | n8n uptime target: 99% (single VPS, no HA) |
| Security | TLS wajib di endpoint publik n8n. Bitrix24 webhook token + AI API key disimpan di environment variable n8n, bukan hardcode |
| Scalability | Initial capacity: 50 estimasi/hari. Single n8n instance cukup. Queue mode jika >200/hari |
| Maintainability | Workflow JSON di-export & disimpan di repo Git (vendor side) untuk version control |
| Compliance | Tidak ada data PII sensitif di RFP (asumsi). Kalau ada, perlu re-evaluate AI provider (Azure OpenAI / on-prem) |

## 11. Security Considerations

- **Bitrix24 webhook token** (`<YOUR_WEBHOOK_TOKEN>`): treat as secret. Tidak boleh masuk Git, hanya di n8n environment.
- **AI API key**: disimpan di n8n credentials store (encrypted at rest oleh n8n).
- **n8n public endpoint**: lindungi dengan path secret yang panjang + opsional verifikasi header signature dari Bitrix24.
- **Rate limit**: implementasikan di reverse proxy untuk mencegah abuse.
- **Audit log**: aktifkan execution log retention minimal 30 hari.
- **Server hardening**: SSH key-only, firewall (UFW), fail2ban, auto-update security patch.

## 12. Assumptions

- A-01: Customer Bitrix24 adalah **cloud** (askarasoftdemo.bitrix24.com), bukan self-hosted Bitrix.
- A-02: Customer akan sediakan **VPS dengan minimum spec**: 2 vCPU, 4GB RAM, 40GB SSD, Ubuntu 22.04+.
- A-03: Customer punya **domain** yang bisa di-pointing untuk n8n endpoint.
- A-04: File RFP dalam **PDF native** (text-based), bukan scan. Kalau scan, butuh tambahan OCR (out of MVP scope).
- A-05: Volume estimasi awal **<50/hari**. Single-instance n8n cukup.
- A-06: Customer setuju data RFP & company info dikirim ke **AI provider eksternal** (OpenAI / Gemini). Tidak ada NDA blocker.

## 13. Open Questions (To Confirm with Customer)

| ID | Question | Impact | Status |
|---|---|---|---|
| OQ-1 | Kapan trigger webhook di Bitrix24 di-fire? Saat item created? Saat stage berubah? Saat klik tombol manual? | UX flow, frekuensi AI call (cost) | OPEN |
| OQ-2 | AI provider: OpenAI atau Gemini? Siapa sediakan & bayar API key? | Cost model, integrasi spesifik | OPEN |
| OQ-3 | Output di field `ufCrm497AiTotalMandays` formatnya: plain text, markdown, atau JSON-stringified? | Render di Bitrix UI, post-processing | OPEN |
| OQ-4 | Production Bitrix24 URL? (sekarang masih `askarasoftdemo`) | Final deploy config | OPEN |
| OQ-5 | Channel notifikasi error: email, Telegram, atau Bitrix internal message? | Implementasi error handler | OPEN |
| OQ-6 | Spec VPS yang tersedia + akses (SSH user, sudo)? | Deployment planning | OPEN |
| OQ-7 | Apakah ada SLA / response time target dari customer? | NFR refinement | OPEN |

## 14. Acceptance Criteria

Project dianggap **selesai (MVP)** apabila:

- [ ] **AC-01** — Sales bisa submit item SPA di Bitrix24 dan dalam <60 detik field `ufCrm497AiTotalMandays` ter-update otomatis dengan output AI.
- [ ] **AC-02** — Output AI mengikuti format breakdown item + mandays per item + total (sesuai sample customer).
- [ ] **AC-03** — Customer (Michael) dapat masuk ke UI n8n, edit prompt template, save, dan perubahan langsung berlaku untuk submission berikutnya tanpa restart workflow.
- [ ] **AC-04** — Workflow handle file RFP PDF (text-based) hingga 20 halaman tanpa error.
- [ ] **AC-05** — Kalau AI provider error / timeout, workflow tidak menulis garbage ke Bitrix24 — field tetap di kondisi sebelumnya, dan ada notifikasi error ke channel yang disepakati.
- [ ] **AC-06** — Workflow JSON di-export dan diserahkan ke customer sebagai backup.
- [ ] **AC-07** — Dokumentasi singkat (1–2 halaman) cara edit prompt + cara tambah field baru di-handover ke customer.
- [ ] **AC-08** — End-to-end test menggunakan minimal 3 sample RFP berbeda berhasil semua.

## 15. Milestones & Estimated Timeline

| Fase | Deliverable | Estimasi |
|---|---|---|
| M1 — Discovery & Sign-off | PRD final disetujui, OQ-1 s/d OQ-7 terjawab, akses Bitrix24 + VPS diberikan | 2–3 hari |
| M2 — Infrastructure Setup | VPS provisioned, Docker stack jalan, n8n accessible via HTTPS | 1–2 hari |
| M3 — Workflow Build | n8n workflow utama + error handler selesai, prompt template draft v1 | 3–4 hari |
| M4 — Prompt Tuning | Iterasi prompt dengan sample RFP customer, output match harapan | 2–3 hari |
| M5 — UAT & Handover | End-to-end test, dokumentasi, training singkat ke customer | 2 hari |
| **TOTAL** | | **~10–14 hari kerja** |

## 16. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| File RFP berbentuk scan (image PDF) tidak bisa di-extract | Medium | High | Tambah OCR di Phase 2; untuk MVP, return error eksplisit ke Sales agar upload PDF native |
| Output AI tidak konsisten formatnya | High | Medium | Pakai structured output (JSON mode); validasi schema sebelum update Bitrix |
| Customer ubah custom field tanpa info → workflow break | Medium | Medium | Workflow design defensive: skip field kalau tidak ada, log warning |
| Bitrix24 webhook token bocor | Low | High | Rotate token, simpan hanya di env n8n, tidak commit ke Git |
| AI API cost membengkak | Medium | Medium | Set max input token, monitor pemakaian, alert kalau lewat threshold |
| VPS down / n8n crash | Low | High | Auto-restart container, backup workflow JSON, dokumentasi recovery |

## 17. Out of Scope (Eksplisit)

Hal-hal berikut **tidak termasuk** dalam project ini:

- Pembangunan form, custom fields, atau Business Process di sisi Bitrix24.
- Customisasi UI Bitrix24 (placement field, rendering markdown, dll).
- Migrasi data historis proposal lama.
- Dashboard / reporting analytics terhadap output AI.
- OCR untuk RFP scan (Phase 2 candidate).
- High Availability / multi-region deployment.
- Penyediaan & pembayaran API key AI provider (default: customer side).
- Training panjang untuk Sales (hanya handover dokumentasi singkat).
- Maintenance bulanan (perlu kontrak terpisah).

## 18. Glossary

| Term | Definisi |
|---|---|
| SPA | Smart Process Automation — modul custom entity di Bitrix24 |
| Entity Type ID 2098 | ID SPA "Proposal Estimation" di Bitrix24 customer |
| BP | Business Process — automation engine di Bitrix24 |
| RFP | Request For Proposal — dokumen requirement dari client |
| MD | Mandays — unit estimasi effort (1 MD = 1 person-day) |
| Prompt | Instruksi tekstual yang dikirim ke LLM AI |
| Webhook | HTTP callback untuk komunikasi sistem-ke-sistem |

---

## Appendix A — Sample Prompt Template (Draft v0)

```
Anda adalah konsultan teknis senior. Hitung estimasi breakdown mandays
untuk project software berikut. Berikan output dalam bentuk list bernomor
berisi nama modul + jumlah mandays per modul, lalu total di bagian akhir.

== DATA PROJECT ==
Nama Project: {{title}}
Platform: {{platform_labels}}
Kompleksitas: {{complexity_label}}
Skala User: {{ufCrm497UserScale}}
Timeline Expectation: {{timeline_label}}
Butuh Integrasi: {{integrate_label}}
Detail Integrasi: {{ufCrm497IntegrationDetail}}

Requirement Summary:
{{ufCrm497Summary}}

Feature List:
{{ufCrm497FeatureList}}

Isi dokumen RFP:
{{rfp_extracted_text}}

== OUTPUT FORMAT ==
Ikuti format berikut persis:
1. <Nama Modul>
   • <Sub-item 1>
   • <Sub-item 2>
   → <X> MD

2. <Nama Modul Berikutnya>
   → <X> MD

...

TOTAL: <Y> MD
```

## Appendix B — Referensi API

- Bitrix24 REST docs: `crm.item.*` family
- API documentation file: `docs/apidocs_spa_proposal_estimation_update.pdf` (17 halaman)
- n8n self-host docs: https://docs.n8n.io/hosting/

---

**Sign-off**

| Role | Name | Date | Signature |
|---|---|---|---|
| Customer (Product Owner) | Michael Chandra | __________ | __________ |
| Implementer | (Mas) | __________ | __________ |
