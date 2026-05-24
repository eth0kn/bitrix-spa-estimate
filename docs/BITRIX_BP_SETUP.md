# Bitrix24 Outbound Webhook Setup — Auto-Trigger n8n

Panduan setup **Automation Rule "Webhook"** di Bitrix24 SPA "Proposal Estimation" supaya saat item dipindah ke stage **"Request AI Estimation"**, Bitrix otomatis POST ke n8n endpoint — tanpa intervensi manual.

## TL;DR

Bitrix24 cloud punya **built-in automation rule "Webhook"** (kategori "Other") yang bisa drop di kolom stage manapun di Kanban. Tidak perlu Business Process designer, tidak perlu custom code.

**Setup singkat:**
1. Buka SPA "Proposal Estimation" → Kanban view
2. Klik **"Automation rules"** di atas board
3. Di kolom stage **"Request AI Estimation"** → klik `+ Create`
4. Pilih kategori **Other → Webhook**
5. Isi: Handler URL = `http://<VPS_IP>:5678/webhook/bitrix-spa-estimate`, Method = POST, Parameter `id` value = pick `{{ID}}` dari picker
6. Save → done

---

## Step-by-Step Detail

1. **Login** ke `<your-bitrix-domain>.bitrix24.com` sebagai user dengan akses edit SPA.
2. Buka **CRM → Automated solutions** (atau "Smart Process") → klik solution berisi SPA **"Proposal Estimation"** (entityTypeId 2098).
3. Pastikan kamu di **Kanban view** dan pipeline **"Default pipeline"** (categoryId 891) aktif (dropdown pipeline di kiri atas).
4. Di atas board, klik tombol **"Automation rules"** (atau "Robots" — sebutan tergantung versi/lokal UI).
5. Editor automation terbuka, menampilkan kolom per stage. Cari kolom stage **"Request AI Estimation"** (`DT2098_891:PREPARATION`).
6. Klik **"+ Create"** (atau ikon `+`) di bawah header stage itu.
7. Di panel kanan "Select automation rule", pilih grup **"Other"** → pilih **"Webhook"** (kalau bahasa Indonesia: "Webhook keluar" / "Outbound webhook").
8. Isi konfigurasi:
   - **Name**: `Notify n8n estimate` (atau bebas)
   - **Handler URL**: `http://<YOUR_VPS_IP>:5678/webhook/bitrix-spa-estimate`
     - ⚠️ n8n endpoint **harus reachable dari internet**. Bitrix24 cloud tidak bisa hit `localhost` atau IP private. Pakai public IP atau domain.
   - **Send method / HTTP method**: **POST**
   - **Authentication**: pilih **No / None** (Bitrix auto-append `auth[application_token]` untuk verifikasi opsional)
9. **Parameter / Custom field** section — klik **"Add field"**:
   - **Name**: `id`
   - **Value**: klik ikon `...` di sebelah kanan field → **"Insert value"** → pilih field **"ID"** dari current item.
   - ⚠️ **Jangan ketik `{{ID}}` manual** — selalu pilih dari picker supaya binding benar. Setelah pick, value tampil sebagai chip.
10. **Save** automation rule.
11. **Trigger condition**: default jalan saat item *masuk* ke stage. Tidak perlu config tambahan.
12. **Test**: buat item baru di stage "New", drag ke "Request AI Estimation". Cek n8n Executions tab — harus ada incoming POST.

---

## Format Payload yang Diterima n8n

Webhook robot bawaan Bitrix kirim **`application/x-www-form-urlencoded`** by default, **bukan raw JSON**. Body sebenarnya seperti ini:

```
id=42&auth[application_token]=xxxxx&auth[domain]=askarasoftdemo.bitrix24.com&event=ONCRMDYNAMICITEMUPDATE
```

**Good news:** n8n Webhook node otomatis parse form-encoded → `$json.body.id = "42"`. Workflow kita sudah handle kedua format (JSON dari curl test + form-encoded dari Bitrix) lewat expression di node "Extract Item ID":

```javascript
{{ $json.body?.id ?? $json.body?.data?.FIELDS?.ID ?? $json.body?.document_id?.[2]?.split('_').pop() ?? $json.query?.id }}
```

→ Tidak perlu ubah apa-apa di n8n.

---

## Placeholder Syntax yang Valid

Saat fill value field di automation rule:

| Syntax | Konteks | Valid? |
|---|---|---|
| `{{ID}}` | Automation rules UI baru (recommended) | ✅ Pakai picker |
| `{{=Document:ID}}` | UI lama / Business Process | ✅ Pakai picker |
| `#ID#` | Business Process template lama | ❌ Tidak valid di Automation Rule |

**Selalu pakai picker (icon `...`)** — jangan ketik manual. Bitrix akan render syntax yang benar otomatis.

---

## Troubleshooting

| Gejala | Penyebab & Fix |
|---|---|
| n8n tidak terima request sama sekali | Port 5678 tidak reachable dari internet. Test: `curl http://<VPS_IP>:5678/healthz` dari mesin di luar VPS. Pastikan firewall allow 5678. |
| `id` kosong / `undefined` di n8n | Kamu mengetik `{{ID}}` manual. Hapus, klik picker `...`, pilih field ID. |
| Webhook fire dua kali per stage change | Ada automation rule lain juga listen ke event yang sama. Cek list rules di stage tersebut. |
| Tidak ada opsi "Webhook" di list "Other" | User permission kurang, atau plan Bitrix24 Free batasi jumlah rules. Coba upgrade plan atau minta admin grant. |
| Bitrix tolak `http://` minta HTTPS | Beberapa portal enforce HTTPS untuk webhook security. Pasang reverse proxy (Caddy/Cloudflare Tunnel) di depan n8n untuk dapat HTTPS gratis. |
| Item lama (yang sudah di stage target sebelum rule dibuat) tidak fire | Rule hanya trigger untuk *new entry* ke stage. Test dengan item baru atau pindahin item lama keluar-masuk stage. |

---

## Alternatif Kalau Automation Rule Tidak Cukup

Untuk kebutuhan lebih kompleks (multi-step logic, conditional, parallel branch):

- **Bitrix Business Process designer** — workflow visual yang lebih powerful, support if/else, parallel, sub-process. Setup-nya lebih kompleks tapi flexible.
- **REST API `bizproc.activity.add`** — register custom HTTP activity untuk dipakai di BP designer.
- **Third-party connector** (Make/Zapier/n8n) — kalau mau orchestrate cross-system flow. Tapi untuk case kita, langsung webhook lebih simple.

Untuk use case kita (1 trigger, 1 webhook call), **Automation Rule "Webhook" sudah cukup** — tidak perlu ke BP designer.

---

## References

- [Inbound and outbound webhooks (Bitrix24 Helpdesk)](https://helpdesk.bitrix24.com/courses/index.php?COURSE_ID=268&LESSON_ID=26002)
- [Create webhooks and apps in Bitrix24](https://helpdesk.bitrix24.com/open/21133100/)
- [Automation rules: Workflow automation](https://helpdesk.bitrix24.com/open/25846259/)
- [Create SPA for automated solutions](https://helpdesk.bitrix24.com/open/19175578/)
- [Incoming and Outgoing Webhooks — API docs](https://apidocs.bitrix24.com/local-integrations/local-webhooks.html)
- [EMC Soft: CRM Robots course (Outbound webhook)](https://emcsoft.io/case/bitrix24-training-course-15-crm-robots-other-2-2/)
- [n8n × Bitrix24 integration](https://n8n.io/integrations/bitrix24/)
