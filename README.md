# Bitrix24 SPA Proposal Estimation — n8n + AI Integration

Otomatisasi estimasi mandays proposal proyek via integrasi **Bitrix24 → n8n → AI (OpenAI/OpenRouter) → Bitrix24**.

Sales mengisi form di Bitrix24 SPA, lalu sistem otomatis memanggil AI untuk generate breakdown estimasi mandays dan menulis hasilnya kembali ke field di Bitrix24.

## Flow

```
Sales fill form in Bitrix24 SPA "Proposal Estimation"
        ↓ (stage moved to "Request AI Estimation")
Bitrix24 Business Process → outbound webhook
        ↓ POST { id: <item_id> }
n8n Workflow
        ├─ GET full item data via crm.item.get
        ├─ Download & extract RFP PDF (if uploaded)
        ├─ Map enum IDs → readable labels
        ├─ Build prompt from editable template
        ├─ Call OpenAI/OpenRouter
        ├─ Parse response
        └─ POST crm.item.update → write to AI Total Mandays Output + move stage to "Pending"
        ↓
Result visible in Bitrix24 detail view
```

## Repo Structure

```
.
├── docs/
│   ├── PRD.md                     # Product Requirements Document
│   └── BITRIX_SCHEMA_REFERENCE.md # Field codes, enum mappings, stage IDs
├── deploy/
│   ├── docker-compose.yml         # n8n + Postgres stack
│   ├── .env.example               # Template for env vars (copy to .env)
│   ├── .gitignore
│   └── DEPLOYMENT_NOTES.md        # How to deploy, backup, rollback
└── workflow/
    ├── proposal-estimation.json   # n8n workflow (importable)
    └── IMPORT_GUIDE.md            # How to import & test the workflow
```

## Quick Start

### 1. Prerequisites

- VPS dengan Docker + Docker Compose
- Bitrix24 instance dengan SPA "Proposal Estimation" (entityTypeId=2098)
- API key dari OpenAI atau OpenRouter
- Bitrix24 Inbound Webhook token

### 2. Deploy n8n Stack

```bash
git clone https://github.com/eth0kn/bitrix-spa-estimate.git
cd bitrix-spa-estimate/deploy
cp .env.example .env
# Edit .env, isi semua placeholder
docker compose up -d
```

n8n akan accessible di `http://<N8N_PUBLIC_HOST>:5678`.

### 3. Import Workflow

Lihat detail di [`workflow/IMPORT_GUIDE.md`](workflow/IMPORT_GUIDE.md).

Singkatnya:
1. Login ke n8n → buat owner account (first visit)
2. Workflows → Create → paste `workflow/proposal-estimation.json` ke canvas (Ctrl+V)
3. Publish workflow
4. Webhook URL siap dipakai: `http://<N8N_PUBLIC_HOST>:5678/webhook/bitrix-spa-estimate`

### 4. Setup Bitrix24

Lihat [`docs/BITRIX_SCHEMA_REFERENCE.md`](docs/BITRIX_SCHEMA_REFERENCE.md) untuk field codes & enum mappings.

Di sisi Bitrix24:
1. Buat custom fields di SPA 2098 sesuai schema reference
2. Setup Business Process trigger: saat item move ke stage **"Request AI Estimation"** (`DT2098_891:PREPARATION`), fire webhook ke n8n
3. Webhook payload minimal: `{"id": <item_id>}`

### 5. Test

```bash
curl -X POST "http://<N8N_PUBLIC_HOST>:5678/webhook/bitrix-spa-estimate" \
  -H "Content-Type: application/json" \
  -d '{"id": <sample_item_id>}'
```

Cek hasil di Bitrix24 → field "AI Total Mandays Output" + stage akan ter-update.

## Customization

### Edit Prompt
Buka workflow di n8n UI → klik node **"Build Prompt (EDIT ME)"** → edit text → save. Berlaku langsung untuk eksekusi berikutnya.

### Tambah Field Input Baru
1. Di Bitrix24: tambah custom field di SPA 2098
2. Di n8n: edit node **"Map Enums → Labels"** (kalau enum) + node **"Build Prompt (EDIT ME)"** untuk include field baru

### Ganti AI Model
Klik node **"Call OpenAI (gpt-5.5)"** → edit field `jsonBody` → ganti string model:
- `gpt-5.5` (default sekarang — reasoning model, kualitas tinggi, lebih lambat ~30-60s)
- `gpt-5.5-mini` (lebih cepat, kualitas sedikit lebih rendah)
- `gpt-5.4`, `gpt-5.4-nano` (faster, non-reasoning, support `temperature` & lebih hemat token)
- `gpt-4o`, `gpt-4o-mini` (legacy generation, gunakan param `max_tokens`)
- atau pakai OpenRouter dengan ganti URL ke `https://openrouter.ai/api/v1/chat/completions` + ganti auth header

⚠️ **Note penting per model family:**
- `gpt-5.5` reasoning model → **TIDAK support custom `temperature`** (forced default 1.0), butuh `max_completion_tokens` ≥4000 (reasoning tokens dimakan dulu)
- `gpt-5.4` / `gpt-5.4-nano` → support `temperature`, pakai `max_completion_tokens`
- `gpt-4.x` → support `temperature`, pakai `max_tokens` (deprecated param di model baru)

## License

MIT (opsional, ditambah kalau perlu)
