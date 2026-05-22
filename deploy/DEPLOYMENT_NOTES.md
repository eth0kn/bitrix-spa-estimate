# Deployment Notes — n8n Stack on VPS

| | |
|---|---|
| **Deployed** | 2026-05-21 |
| **VPS IP** | <YOUR_VPS_IP> |
| **OS** | Ubuntu 24.04.4 LTS |
| **n8n Version** | 2.21.5 (latest as of deployment) |
| **Stack Location** | `/opt/n8n-stack/` on VPS |
| **Stack Mode** | HTTP only (Opsi A — IP+port, no domain/TLS) |

---

## Access

| Service | URL | Catatan |
|---|---|---|
| n8n UI | http://<YOUR_VPS_IP>:5678 | Set up owner account on first visit |
| n8n Healthcheck | http://<YOUR_VPS_IP>:5678/healthz | Returns `{"status":"ok"}` |
| Webhook base | http://<YOUR_VPS_IP>:5678/webhook/... | Pattern URL untuk webhook trigger |
| Postgres | (internal only) | Tidak exposed ke publik |

---

## Credentials

Lihat `deploy/.env.backup` — **JANGAN commit ke Git public!**

| Variable | Purpose |
|---|---|
| `POSTGRES_PASSWORD` | Password DB internal n8n |
| `N8N_ENCRYPTION_KEY` | Key untuk encrypt credentials di n8n (jangan ganti setelah ada credentials tersimpan, akan kehilangan akses) |

---

## What's Running

- 2 container Docker:
  - `n8n` (port 5678 exposed publik)
  - `n8n-postgres` (internal only, di network `n8n-stack-internal`)
- 2 named Docker volumes:
  - `n8n-stack-n8n-data` — workflow, credentials, settings n8n
  - `n8n-stack-postgres-data` — DB postgres
- Tidak menyentuh stack lain yang sudah ada di VPS (`aidms`, `traefik`, `weaviate`)

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
