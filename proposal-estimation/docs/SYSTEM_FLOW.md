# Flow Sistem — Bitrix24 ↔ n8n ↔ AI

> Dokumen ini untuk dishare ke customer (Michael) supaya bisa menjelaskan
> end-to-end flow dari sisi user (Sales) sampai hasil tampil di Bitrix24.

---

## TL;DR (Eksekutif Summary)

Sales mengisi form di Bitrix24 sebagaimana biasa. Saat mereka pindahkan kartu ke stage **"Request AI Estimation"**, sistem otomatis memanggil AI di belakang layar. Dalam 10–15 detik, hasil estimasi mandays muncul di field **"AI Total Mandays Output"** dan kartu pindah otomatis ke stage **"Pending"** untuk review. Tidak ada copy-paste manual, tidak perlu pindah aplikasi.

---

## Visual Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                          SALES USER                                │
│                          ─────────                                 │
│                                                                    │
│   [1] Buka Bitrix24                                                │
│   [2] Create item baru di SPA "Proposal Estimation"                │
│   [3] Isi field:                                                   │
│       • Nama project                                               │
│       • Requirement Summary                                        │
│       • Feature List                                               │
│       • Upload RFP (PDF, optional)                                 │
│       • Platform (Web/Mobile/Portal/API)                           │
│       • Integration Required + Detail                              │
│       • Complexity (Low/Medium/High)                               │
│       • User Scale                                                 │
│       • Timeline (Normal/Dipercepat)                               │
│   [4] Drag kartu dari "New" → "Request AI Estimation"              │
│                                                                    │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         │  (Business Process auto-fire webhook)
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                       SISTEM (n8n + AI)                            │
│                       ─────────────────                            │
│   ⚙️  Otomatis, ~10–15 detik:                                       │
│                                                                    │
│   [a] n8n terima webhook → ambil semua data item dari Bitrix       │
│   [b] Download file RFP (kalau ada) → extract text dari PDF        │
│   [c] Bangun prompt dari template + data project                   │
│   [d] Kirim ke AI (OpenAI GPT-4o-mini)                             │
│   [e] AI return breakdown estimasi mandays                         │
│   [f] n8n tulis hasil ke field "AI Total Mandays Output"           │
│   [g] n8n pindah stage: "Request AI Estimation" → "Pending"        │
│                                                                    │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                          SALES USER                                │
│                          ─────────                                 │
│                                                                    │
│   [5] Refresh / buka kartu di Bitrix24                             │
│   [6] Lihat hasil di field "AI Total Mandays Output":              │
│                                                                    │
│       1) Dashboard (12 MD) — UI/UX, Backend, Charts;               │
│       2) Auth (5 MD) — Login, JWT, Reset password;                 │
│       3) Workflow (8 MD) — ...                                     │
│       TOTAL: 50 MD                                                 │
│                                                                    │
│   [7] Stage sudah di "Pending" — siap review                       │
│   [8] Sales/PM review hasil → adjust kalau perlu →                 │
│       move ke "Done" → "Success" (Finish)                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Detail (Perspektif Sales)

### 1️⃣ Sales Buka Form

Sales login Bitrix24 → buka SPA **"Proposal Estimation"** (di menu CRM atau via Smart Process Automation).

### 2️⃣ Sales Isi Data Project

Form input berisi 9 field (sesuai schema SPA 2098):

| Field | Tipe | Contoh Isi |
|---|---|---|
| Name | Text | "Proposal PT XYZ Bank" |
| Requirement Summary | Text panjang | Deskripsi narrative project |
| Feature List | Text | "Dashboard, Auth, Workflow, ..." |
| Upload Rfp | File (PDF) | RFP dari client (optional) |
| Platform | Multi-select | Web + Mobile |
| Integration Required | Yes/No | Yes |
| Detil Integration | Text | "Integrasi SAP + LDAP" |
| Complexity Level | Low/Medium/High | High |
| User Scale | Number | 500 |
| Timeline Expectation | Normal/Dipercepat | Normal |

### 3️⃣ Sales Trigger Estimasi

Saat semua field sudah diisi, Sales **drag kartu** dari stage **"New"** ke **"Request AI Estimation"** (atau klik tombol Move Stage).

→ **Inilah trigger point.** Tidak ada tombol tambahan, tidak perlu manual copy-paste, tidak buka aplikasi lain.

### 4️⃣ Sistem Bekerja (10–15 detik)

Apa yang terjadi di belakang layar (Sales tidak perlu tahu detail ini):

| Step | Apa yang Terjadi |
|---|---|
| a | Bitrix24 Business Process fire webhook ke n8n |
| b | n8n ambil seluruh data item via Bitrix API |
| c | Kalau ada file RFP → n8n download & extract teks dari PDF |
| d | n8n bangun prompt: gabungkan template + data project + isi RFP |
| e | n8n kirim ke OpenAI (model GPT-4o-mini) |
| f | OpenAI return breakdown mandays per modul |
| g | n8n write hasil ke field "AI Total Mandays Output" di Bitrix |
| h | n8n pindah stage dari "Request AI Estimation" → "Pending" |

### 5️⃣ Sales Lihat Hasil

Sales **refresh** halaman atau buka ulang item. Hasil tampil di field **"AI Total Mandays Output"** dalam format:

```
1) Dashboard Project (12 MD) — UI/UX, Backend API, Charts;
2) Manajemen Role (8 MD) — Definisi role, Kontrol akses;
3) Workflow Persetujuan (14 MD) — Approval engine, UI;
...
TOTAL: 50 MD
```

Stage sudah pindah ke **"Pending"** = sinyal bahwa AI sudah selesai dan siap di-review manusia.

### 6️⃣ Review & Finalisasi (Manual oleh Sales/PM)

- Sales/PM cek hasil estimasi, validasi reasonableness
- Kalau perlu adjust (mis: AI underestimate untuk fitur tertentu), edit field manual
- Move stage ke **"Done"** kalau sudah OK
- Move ke **"Success"** (Finish) saat proposal sudah dikirim ke client

---

## Pembagian Peran (Siapa Setup Apa)

| Komponen | Owner | Status |
|---|---|---|
| Bitrix24 SPA (Proposal Estimation) + custom fields | **Customer (Michael)** | ✅ Sudah ada |
| Form layout & validation di Bitrix | **Customer (Michael)** | ✅ Sudah ada |
| **Business Process trigger** (webhook saat stage change) | **Customer (Michael)** | ⏳ **PENDING — perlu setup** |
| VPS server + n8n stack | Vendor (kita) | ✅ Done |
| n8n workflow (webhook → AI → update) | Vendor (kita) | ✅ Done |
| Prompt engineering (instruksi ke AI) | Vendor + Customer review | ✅ v1 ready |
| OpenAI API key & billing | **Customer (Michael)** | ✅ Sudah disediakan |
| Akses & permission Bitrix user | Customer | ✅ Sudah ada |

---

## Yang Perlu Michael Setup di Bitrix24

Ini bagian yang masih outstanding dari sisi customer:

### Business Process / Automation Rule

Di SPA "Proposal Estimation" (entityTypeId=2098), buat automation rule:

**Trigger:**
- Saat **stage berubah** dari "New" → "Request AI Estimation"
- (Stage ID: `DT2098_891:PREPARATION`)

**Action:**
- Fire **outbound webhook** ke URL:
  ```
  http://<YOUR_VPS_IP>:5678/webhook/bitrix-spa-estimate
  ```
- **Method:** POST
- **Content-Type:** application/json
- **Payload:** `{"id": <ID item ini>}`

Bitrix24 memang punya fitur outbound webhook di Automation Rules / Business Processes. Michael atau Bitrix admin tahu cara setup-nya.

### Setelah BP Setup

Sales tidak perlu apa-apa lagi — cukup drag kartu, hasil otomatis muncul.

---

## Yang Sudah Bisa Di-test Sekarang (Tanpa BP)

Untuk testing manual sebelum BP setup, bisa langsung trigger webhook dari command line:

```bash
curl -X POST "http://<YOUR_VPS_IP>:5678/webhook/bitrix-spa-estimate" \
  -H "Content-Type: application/json" \
  -d '{"id": <ID item Bitrix>}'
```

Workflow akan jalan persis seperti kalau di-trigger oleh BP.

---

## Cost & Performance (Untuk Disampaikan ke Michael)

### Cost AI

Model: **OpenAI GPT-4o-mini**
- Input: ~3000 tokens (form + RFP excerpt) ≈ $0.00045
- Output: ~500 tokens (breakdown) ≈ $0.00030
- **Total per estimasi: ~$0.0008 (~Rp 13)**
- **Asumsi 50 proposal/hari → ~Rp 650/hari → ~Rp 20.000/bulan**

Praktis gratis. Bisa upgrade ke GPT-4o (full) untuk reasoning lebih kuat dengan cost 10x (~Rp 200.000/bulan untuk 50 estimasi/hari).

### Cost Hosting

Sudah berjalan di VPS existing customer. Tidak ada incremental cost untuk hosting n8n.

### Performance

- **End-to-end latency:** 10–15 detik (dari trigger sampai field ter-update)
- **Throughput:** Bisa handle ~100+ estimasi/jam tanpa optimasi
- **Concurrency:** Multiple proposal bisa di-process paralel

### Reliability

- **Self-hosted** di VPS customer → tidak ada vendor lock-in selain OpenAI API
- **Error handling:** Kalau OpenAI down atau RFP corrupt, workflow tidak menulis garbage — field tetap state sebelumnya, log tersedia di n8n executions
- **Backup:** Workflow JSON ada di Git repo, restoration < 5 menit

---

## Customization Path

Hal-hal yang **gampang diubah** setelah MVP live, tidak perlu hubungi vendor:

| Yang Mau Diubah | Cara |
|---|---|
| Isi prompt AI | Login n8n → buka workflow → klik node "Build Prompt" → edit text → save |
| Tambah field input baru ke prompt | Login n8n → edit node "Build Prompt" → tambah `{{ $json.fieldname }}` |
| Ganti AI model | Login n8n → klik node "Call OpenAI" → ganti string model name |
| Naikkan kualitas (pakai GPT-4o full) | Same as above, ganti `gpt-4o-mini` → `gpt-4o` |
| Tambah custom field di SPA Bitrix | Michael / Bitrix admin via Bitrix UI |

Yang **harus hubungi vendor** untuk diubah:
- Logic workflow (mis: tambah branch baru, integrasi tools lain)
- Struktur output format yang fundamental berbeda
- Tambah AI provider selain OpenAI/OpenRouter

---

## FAQ Antisipatif (Pertanyaan dari Michael)

**Q: Berapa lama waktunya dari Sales submit sampai hasil muncul?**
A: 10–15 detik di kondisi normal. Maksimum 60 detik kalau RFP besar (>20 halaman PDF) atau OpenAI lagi sibuk.

**Q: Kalau AI estimasinya kurang akurat?**
A: Bisa langsung tune prompt di n8n (tanpa coding). Kalau masih kurang, upgrade ke model lebih kuat (gpt-4o atau Claude Sonnet). Sales/PM tetap bisa edit manual hasil di Bitrix kalau perlu adjustment kecil.

**Q: Apakah data project dikirim ke OpenAI? Aman?**
A: Ya, prompt + data project + isi RFP dikirim ke OpenAI API. OpenAI policy: tidak dipakai untuk training kalau pakai API (beda dengan ChatGPT public). Kalau ada concern data sensitif, bisa pakai Azure OpenAI (deployment private) atau on-premise LLM.

**Q: Kalau Sales lupa isi salah satu field?**
A: AI tetap proses dengan data yang ada. Field kosong di-mark "(empty)". Bisa di-enforce validation di Bitrix form supaya wajib isi tertentu.

**Q: Bisakah customize untuk SPA lain (selain Proposal Estimation)?**
A: Ya, workflow ini reusable. Tinggal duplicate + adjust entityTypeId + field mapping. Estimasi adjustment: 2-3 hari kerja per SPA baru.

**Q: Apakah data RFP yang diupload tersimpan di n8n?**
A: Tidak permanent. n8n download untuk extract teks lalu di-discard setelah workflow selesai. File aslinya tetap tersimpan di Bitrix24.

**Q: Bagaimana kalau ingin upgrade ke OCR untuk RFP scan (image PDF)?**
A: Phase 2 candidate. Bisa pakai Tesseract (open source, gratis) atau Google Vision API (~Rp 25/halaman). Estimasi development: 1-2 hari.

**Q: Apa yang terjadi kalau workflow error?**
A: Field di Bitrix tetap di state sebelumnya (tidak ditulis garbage). Error log tersedia di n8n Executions tab. Bisa setup notifikasi otomatis (email/Telegram) kalau diperlukan.

---

## Next Steps yang Disarankan ke Michael

1. **Setup Business Process** di Bitrix24 untuk auto-trigger webhook (estimasi 30 menit kerja Bitrix admin)
2. **Test dengan 3-5 proposal real** untuk benchmark kualitas AI
3. **Review & tune prompt** kalau ada gap di hasil
4. **Sign-off MVP** → masuk pilot dengan tim Sales kecil dulu
5. **(Optional)** Upgrade model ke gpt-4o untuk kualitas lebih tinggi kalau pilot results justify
