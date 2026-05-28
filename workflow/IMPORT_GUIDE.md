# n8n Workflow Import Guide

> File workflow: `workflow/proposal-estimation.json`
> Tujuan: import workflow ke n8n yang sudah deployed di VPS.

## Prerequisites (sudah selesai)

- ✅ n8n deployed di http://<YOUR_VPS_IP>:5678
- ✅ Owner account dibuat (mknizar10@gmail.com)
- ✅ Env vars `OPENROUTER_API_KEY`, `BITRIX_WEBHOOK_BASE_URL`, `BITRIX_ENTITY_TYPE_ID` sudah di-set di container

## Step-by-Step Import

### 1. Buka n8n UI

URL: **http://<YOUR_VPS_IP>:5678**

Login dengan email yang dipakai saat setup owner.

### 2. Import Workflow JSON

1. Di sidebar kiri, klik **"Workflows"**
2. Di kanan atas, klik tombol **`+`** atau **"Create Workflow"**
3. Di workflow editor kosong, klik **menu titik 3 (⋯)** di kanan atas
4. Pilih **"Import from File"** atau **"Import from URL"**
5. Pilih **"Import from File"** → upload file `proposal-estimation.json` dari folder lokal Mas:
   ```
   C:\Users\KN\Documents\Projects\bitrix\workflow\proposal-estimation.json
   ```
6. Workflow akan muncul dengan **15 node** terhubung jadi flow (termasuk 2 node baru untuk AI extraction RFP)

### 3. Cek Setiap Node Tidak Ada Error

Setelah import, scan tiap node:
- **Tidak ada icon merah** ⛔ — kalau ada, klik node-nya, lihat error message
- Common error: "Credential not found" — tapi workflow ini **TIDAK pakai credentials**, semua via env var
- Kalau ada warning tipe versi node, klik "Update" — biasanya auto-resolve

### 4. Save Workflow

- Klik **"Save"** di kanan atas (atau `Ctrl+S`)
- Beri nama (default sudah: "Bitrix SPA Proposal Estimation (AI)")

### 5. Ambil Webhook URL untuk Bitrix

1. Klik node **"Webhook (Bitrix Trigger)"** (paling kiri)
2. Di panel kanan, tab **"Production URL"** copy URL-nya
3. URL akan kira-kira begini:
   ```
   http://<YOUR_VPS_IP>:5678/webhook/bitrix-spa-estimate
   ```
4. **Simpan URL ini** — nanti dipakai Michael untuk setup outbound webhook di Bitrix24

### 6. Activate Workflow

- Di kanan atas, klik toggle **"Inactive"** → jadi **"Active"** (hijau)
- Sekarang webhook URL ready menerima POST dari Bitrix24

---

## Cara Test Workflow (Tanpa Bitrix BP)

Sebelum minta Michael setup BP, kita test dulu manual:

### Test Method 1 — Manual Execution di n8n

1. Buka workflow di n8n
2. Klik tombol **"Execute Workflow"** di bawah
3. n8n akan kasih sample webhook URL di node Webhook
4. Tapi ini butuh ada payload — skip method ini

### Test Method 2 — Curl dari Mesin Mas (recommended)

Buka PowerShell, jalankan:

```powershell
curl -X POST "http://<YOUR_VPS_IP>:5678/webhook/bitrix-spa-estimate" `
  -H "Content-Type: application/json" `
  -d '{\"id\": 1}'
```

Ini akan trigger workflow dengan item id=1 (sample "Proposal PT Sukses Jaya Abadi").

### Lihat Hasil Eksekusi di n8n

1. Buka workflow → menu **"Executions"** di kiri
2. Akan muncul list eksekusi (latest di atas)
3. Klik eksekusi terakhir → lihat per-node:
   - ✅ Hijau = sukses
   - ❌ Merah = error (klik untuk lihat detail)

### Lihat Hasil di Bitrix24

Setelah test sukses:
1. Refresh URL: https://askarasoftdemo.bitrix24.com/crm/type/2098/details/1/
2. Item "Proposal PT Sukses Jaya Abadi" harus:
   - Field **"AI Total Mandays Output"** ter-update dengan breakdown baru dari AI
   - Stage pindah dari **"New"** ke **"Pending"**

---

## Cara Edit Prompt AI

Ada **2 prompt** yang bisa di-tune:

### A. Main Estimation Prompt (paling sering diedit)
1. Buka workflow → klik node **"Build Prompt (EDIT ME)"**
2. Edit text di field **"prompt"** → save
3. Berlaku untuk eksekusi berikutnya

### B. RFP Extraction Prompt
Bertugas filter PDF RFP: extract hanya functional req, integrations, workflows, reporting, mobile/web. Buang legal, SLA, company profile, commercial terms.

1. Buka workflow → klik node **"Build RFP Extraction Prompt"**
2. Edit text di field **"extraction_prompt"** → save
3. Misal mau extract kategori baru (mis: "Compliance Requirements"), tambah di list EKSTRAK

## Cara Tambah Field Input Baru

Buka node **"Map Enums → Labels"** — di awal code ada **block komentar verbose step-by-step** untuk:
1. Buat custom field di Bitrix
2. Tambah ENUM mapping (kalau perlu)
3. Tambah field di return object
4. Reference di "Build Prompt (EDIT ME)" sebagai `{{ $json.<field_name> }}`

Placeholder yang tersedia di prompt:
- `{{ $json.title }}` — Nama project
- `{{ $json.platform_labels }}` — Platform (joined string)
- `{{ $json.complexity }}` — Low/Medium/High
- `{{ $json.user_scale }}` — Number of users
- `{{ $json.timeline }}` — Normal/Dipercepat
- `{{ $json.is_integrate }}` — Yes/No
- `{{ $json.integration_detail }}` — Free text
- `{{ $json.summary }}` — Requirement Summary
- `{{ $json.feature_list }}` — Feature List
- `{{ $json.rfp_text }}` — Isi file RFP (text yang ter-extract dari PDF)

---

## Ganti Model AI (kalau Free Tier Kurang)

Default sekarang: `google/gemini-2.0-flash-exp:free`

Untuk ganti:
1. Klik node **"Call OpenRouter (Gemini Flash Free)"**
2. Edit field **"jsonBody"** — ganti string `"google/gemini-2.0-flash-exp:free"` jadi model lain:
   - `meta-llama/llama-3.3-70b-instruct:free` — alternatif free
   - `anthropic/claude-sonnet-4.7` — paid, kualitas tertinggi
   - `openai/gpt-4o-mini` — paid, balanced
   - `deepseek/deepseek-r1` — reasoning model

Lihat semua model tersedia di: https://openrouter.ai/models

---

## Untuk Setup di Sisi Bitrix24 (Customer / Michael)

Setelah workflow active, kasih Michael info ini:

> **Outbound Webhook URL untuk Bitrix BP:**
> `http://<YOUR_VPS_IP>:5678/webhook/bitrix-spa-estimate`
>
> **Method:** POST
> **Content-Type:** application/json
> **Payload:** `{"id": <ID dari SPA item>}` atau `{"document_id": [...]}` (n8n parse keduanya)
>
> **Trigger setup:**
> Setup Business Process / Automation Rule di SPA "Proposal Estimation" (entityTypeId=2098), trigger saat item move ke stage **"Request AI Estimation"** (`DT2098_891:PREPARATION`).

---

## Troubleshooting

### Webhook tidak fire / 404

- Pastikan workflow **"Active"** (toggle hijau di kanan atas)
- Coba akses URL webhook di browser → harus muncul page "n8n - Workflow Automation" atau JSON error (bukan 404)

### Node "Bitrix: Get SPA Item" gagal

- Cek env var `BITRIX_WEBHOOK_BASE_URL` di container:
  ```bash
  ssh root@<YOUR_VPS_IP> 'docker exec n8n env | grep BITRIX'
  ```
- Test API langsung:
  ```bash
  curl -X POST "https://askarasoftdemo.bitrix24.com/rest/1177/<YOUR_WEBHOOK_TOKEN>/crm.item.get" \
    -H "Content-Type: application/json" \
    -d '{"entityTypeId": 2098, "id": 1}'
  ```

### Node "Call OpenRouter" return 401

- API key invalid atau expired — generate baru di https://openrouter.ai/keys
- Update env var di `/opt/n8n-stack/.env` lalu `docker compose up -d`

### Node "Extract PDF Text" gagal

- Kemungkinan file bukan PDF native (scan/image)
- Sementara: skip RFP, isi langsung di Requirement Summary
- Long-term: tambahkan OCR (Phase 2)

### AI output format tidak sesuai

- Edit prompt di node **"Build Prompt (EDIT ME)"** — tambah contoh output yang diinginkan
- Coba ganti model ke yang lebih kuat (paid model)

---

## Backup Workflow Setelah Edit

Setelah Mas/Michael edit prompt di n8n UI:

1. Export workflow: menu titik 3 → "Download" → save sebagai JSON
2. Replace file `workflow/proposal-estimation.json` di repo lokal
3. (Opsional) commit ke Git untuk version control
