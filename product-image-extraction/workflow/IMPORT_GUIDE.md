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

## Bitrix Automation Rule Setup

Sales workflow requires Bitrix Automation Rule to trigger the webhook when Sales moves
an item to a specific stage (e.g. "Prepare Extraction").

1. In Bitrix, buka **CRM → Automation → SPA "Estimates" (entityTypeId 1038)**
2. Pilih stage yang jadi trigger (misal: "Extract Quotation")
3. **Create automation rule** → **Webhook**
4. URL: `https://n8n.askarasoft.com/webhook/product-image-extract`
5. Method: **POST**
6. Body (JSON):
   ```json
   { "item_id": "{{ID}}" }
   ```
   (Bitrix akan substitute `{{ID}}` dengan actual item ID)
7. Save & activate

## Testing (End-to-End)

### Test Case 1: DOCX
1. Create new SPA item at any stage
2. Attach `Sample QT1-15m Mq Tent (850)….docx` (from `docs/`) ke field "Quotation DOCX"
3. Move stage → trigger
4. Wait ~30-60s
5. Refresh item — expect fields populated (Product, Width, Length, etc.) + additional items created for line 2, 3
6. Check n8n Executions log — should be all green

### Test Case 2: PDF
Same as above but attach PDF version.

### Test Case 3: PNG
Same but attach a screenshot / photo of quotation.

### Test Case 4: Unsupported
Attach `.xlsx` or `.zip` → expect no field update but a timeline comment
"[b]Unsupported file format[/b]".

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
