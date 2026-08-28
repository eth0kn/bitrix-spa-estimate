# Import Guide — Product Image Extraction Workflow

## Prerequisites

1. **Env var added to VPS `.env`**:
   ```
   BITRIX_TFSSB_URL=https://tfssbdemo.bitrix24.com/rest/16/qipn7bi17pp91co5
   ```

2. **`docker-compose.yml`** already updated with:
   - `BITRIX_TFSSB_URL` in n8n environment section
   - `gotenberg` sidecar service (for DOCX→PDF conversion)

3. **Recreate n8n container** to pick up new env var + gotenberg:
   ```bash
   cd /opt/n8n-stack
   docker compose up -d --force-recreate n8n
   docker compose up -d gotenberg
   docker compose ps
   ```

## Import Steps

1. Open **https://n8n.askarasoft.com**
2. Login as owner
3. Left sidebar → **Workflows** → **Add workflow** dropdown → **Import from file**
4. Choose `product-image-extraction.json`
5. Rename kalau perlu (default: "Product Image Extraction (SPA 1038)")
6. Click **Save** (Ctrl+S)
7. Toggle **Active** switch (top-right) to ON

## Webhook URL

After activate, the webhook URL is:
```
https://n8n.askarasoft.com/webhook/product-image-extract
```

Test with curl:
```bash
curl -X POST https://n8n.askarasoft.com/webhook/product-image-extract \
  -H 'Content-Type: application/json' \
  -d '{"item_id": <SOME_EXISTING_SPA_ITEM_ID>}'
```

## Bitrix Automation Rule Setup (v4 — native Quote entity)

Sales workflow requires Bitrix Automation Rule di **Quote entity (entityTypeId 7)** to trigger webhook when Sales moves quote to stage **SENT (Prepare)**.

1. In Bitrix, buka **CRM → Quotes** (Estimates in UI): https://tfssbdemo.bitrix24.com/crm/quote/
2. Click **Automation rules** (top right)
3. Di kolom stage **"Prepare"** (SENT), klik **"+ Create"**
4. Pilih **Outbound webhook** (kategori Recent / Other)
5. Handler URL: `https://n8n.askarasoft.com/webhook/product-image-extract?id=`
   - Klik ikon "..." di kanan → **Smart Process Automation / Quote fields** → pilih **ID** → token tersisip
6. Method: **POST** (default)
7. Save automation rule
8. Save automation config di bottom

**Alt approach**: URL bersih tanpa `?id=...`, workflow parse `document_id[2]` dari body payload (default Bitrix outbound webhook format). Both work.

## Testing (End-to-End)

### Test Case 1: DOCX single quotation
1. Create new **Quote** di https://tfssbdemo.bitrix24.com/crm/quote/
2. Fill title (e.g. "Test QT1")
3. Attach QT1 DOCX ke field **Quotation DOCX** (`ufCrmQuoteQuotationDocx`)
4. Drag ke stage **Prepare (SENT)** via Kanban
5. Wait ~30-60s → refresh
6. **Expect**:
   - Original Quote updated with line 1's specs (Product, Width, Length, dll)
   - **2 new Quote records created** (line 2 Awning, line 3 Transportation)
   - Semua share `ufCrmQuoteQref` — filter by ini untuk group
   - Each Quote has 1 product row di Products tab, linked ke catalog SKU
   - Catalog Products: klik Products tab → click product name → SKU attributes visible

### Test Case 2: PDF (same as DOCX)

### Test Case 3: PNG (same as DOCX)

### Test Case 4: Unsupported (xlsx/zip)
Expected: Quote tidak update, tapi timeline comment "[b]Unsupported file format[/b]" appears.

### Test Case 5: Multi-quotation (1 file berisi 2 quotations)
Expected: M×N Quote records created (e.g. QT-A dengan 3 line + QT-B dengan 2 line = 5 records total).

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Webhook 404 | Workflow not active | Toggle Active ON |
| "gotenberg not resolved" | Service not started | `docker compose up -d gotenberg` |
| "Could not find value for parameter {entityTypeId}" | Bitrix API call sent entityTypeId in body only | Ensure query string version — workflow already does this |
| AI response empty / parse error | gpt-5.5 rate limit or bad prompt | Check n8n execution → OpenAI node → view response |
| Fields not populated but no error | Wrong camelCase | Compare workflow "Build Bitrix Payload" node against `docs/bitrix-field-mapping.json` |

## Env Vars Referenced by Workflow

| Var | Value |
|---|---|
| `BITRIX_TFSSB_URL` | `https://tfssbdemo.bitrix24.com/rest/16/qipn7bi17pp91co5` |
| `OPENAI_API_KEY` | (shared with Project 1 + 2) |
