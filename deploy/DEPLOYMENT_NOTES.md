# Deployment Notes — n8n Stack on VPS

| | |
|---|---|
| **First Deployed** | 2026-05-21 |
| **HTTPS Enabled** | 2026-07-09 (via Caddy) |
| **VPS IP** | `<YOUR_VPS_IP>` (see credentials.md) |
| **Public Domain** | n8n.askarasoft.com (HTTPS via Let's Encrypt) |
| **OS** | Ubuntu 24.04.4 LTS |
| **n8n Version** | 2.21.5+ |
| **Stack Location** | `/opt/n8n-stack/` on VPS |
| **Stack Mode** | HTTPS via Caddy reverse proxy |
| **Serves Both** | Project 1 (`proposal-estimation/`) + Project 2 (`tldv-meeting-summary/`) |

---

## Access

| Service | URL | Catatan |
|---|---|---|
| n8n UI | **https://n8n.askarasoft.com** | HTTPS via Caddy — primary access |
| Legacy HTTP | http://`<YOUR_VPS_IP>`:5678 | Masih listen (backward compat for Project 1 BP) |
| Healthcheck | https://n8n.askarasoft.com/healthz | Returns `{"status":"ok"}` |
| Webhook base | https://n8n.askarasoft.com/webhook/... | Pattern URL untuk webhook trigger |
| Postgres | (internal only) | Tidak exposed ke publik |

### Active Webhook Endpoints

| Project | Path | Trigger |
|---|---|---|
| Project 1 (Proposal Estimation) | `/webhook/bitrix-spa-estimate` | Bitrix Automation Rule (SPA 2098 stage change) |
| Project 2 (TLDV Meeting Summary) | `/webhook/tldv-transcript-ready` | TLDV `TranscriptReady` event |

---

## Credentials

Lihat `deploy/.env.backup` (git-ignored) + `credentials.md` (git-ignored) untuk complete reference.

Env vars di container n8n (dari `deploy/.env`):

| Variable | Purpose | Used By |
|---|---|---|
| `POSTGRES_PASSWORD` | DB internal password | Both (infra) |
| `N8N_ENCRYPTION_KEY` | Encrypt stored credentials in n8n | Both (infra) — JANGAN ganti setelah ada credentials tersimpan |
| `N8N_PUBLIC_HOST` | Public hostname for TLS (`n8n.askarasoft.com`) | Both (Caddy + n8n cookie config) |
| `OPENAI_API_KEY` | AI provider | Both projects |
| `BITRIX_WEBHOOK_BASE_URL` | Bitrix DEMO webhook base URL | Project 1 (SPA 2098) |
| `BITRIX_ENTITY_TYPE_ID` | Default 2098 | Project 1 |
| `BITRIX_PROD_URL` | Bitrix PRODUCTION webhook base URL | Project 2 (Lead + SPA 1070) |
| `TLDV_API_KEY` | TLDV API for meeting metadata fetch | Project 2 |

---

## What's Running

- 3 container Docker:
  - `n8n` (port 5678 exposed publik untuk backward compat, primary access via Caddy)
  - `n8n-postgres` (internal only, di network `n8n-stack-internal`)
  - `n8n-caddy` (port 80 + 443 exposed publik, reverse proxy ke n8n:5678, auto Let's Encrypt TLS)
- 4 named Docker volumes:
  - `n8n-stack-n8n-data` — workflow, credentials, settings n8n
  - `n8n-stack-postgres-data` — DB postgres
  - `n8n-stack-caddy-data` — Caddy certificates & state
  - `n8n-stack-caddy-config` — Caddy runtime config
- Tidak menyentuh stack lain yang sudah ada di VPS (`aidms`, `traefik` on port 4200, `weaviate`)

---

## Stack Commands (Run on VPS)

```bash
# Status
cd /opt/n8n-stack && docker compose ps

# Logs
docker compose logs -f n8n
docker compose logs -f postgres

# Restart
docker compose restart n8n

# Update n8n ke versi terbaru
docker compose pull && docker compose up -d

# Stop semua
docker compose down

# Stop + hapus data (DESTRUCTIVE)
docker compose down -v
```

---

## Backup Strategy (Belum Setup — TODO)

Yang perlu di-backup berkala:
1. Volume `n8n-stack-postgres-data` (database — workflow & execution history)
2. Volume `n8n-stack-n8n-data` (config files, encryption metadata)
3. File `/opt/n8n-stack/.env` (encryption key — TANPA INI workflow credentials TIDAK BISA didecrypt)

Snippet backup manual (jalankan dari VPS):
```bash
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p /var/backups/n8n
docker run --rm -v n8n-stack-postgres-data:/data -v /var/backups/n8n:/backup alpine \
  tar czf /backup/postgres-$TS.tar.gz -C /data .
docker run --rm -v n8n-stack-n8n-data:/data -v /var/backups/n8n:/backup alpine \
  tar czf /backup/n8n-data-$TS.tar.gz -C /data .
cp /opt/n8n-stack/.env /var/backups/n8n/env-$TS.bak
```

---

## Known Warnings (Tidak Blocking)

1. **`Failed to start Python task runner ... Python 3 is missing`**
   → Hanya warning. Tidak butuh Python runner untuk workflow Bitrix kita (JS runner sudah jalan).
2. **`N8N_RUNNERS_ENABLED deprecated`**
   → Sudah jadi default di v2. Bisa dihapus dari compose pada maintenance berikutnya (non-urgent).

---

## Next Steps

1. **Buka http://<YOUR_VPS_IP>:5678 di browser** → buat owner account (email + password)
2. Setelah owner account dibuat, masuk ke Settings → Personal → simpan login credentials
3. Setup credential OpenRouter di n8n: Credentials → Add → "OpenAI" type → masukkan API key OpenRouter + ganti base URL ke `https://openrouter.ai/api/v1`
4. Lanjut: build workflow Bitrix ↔ AI

---

## Rollback / Cleanup (Kalau Perlu)

```bash
# Hapus stack & data (DESTRUCTIVE)
cd /opt/n8n-stack
docker compose down -v
rm -rf /opt/n8n-stack

# Hapus images (opsional)
docker rmi n8nio/n8n:latest postgres:16-alpine
```

Ini **tidak akan menyentuh** AIDMS / Traefik / Weaviate.
