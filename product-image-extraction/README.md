# Project 3 — Product Image Extraction → Bitrix Estimate

Otomatisasi ekstraksi produk dari image / PDF / DOCX quotation → OpenAI → populate Bitrix SPA
"Estimates" (entityTypeId **1038**) dengan 22 spec + 6 meta field per line item.

## Status

🚧 **v2 in progress** — v1 POC live, v2 (Products tab + multi-quotation) approved & implementing.

### v1 (LIVE, 2026-08-24)
- ✅ Bitrix schema created (29 custom fields via API)
- ✅ Gotenberg sidecar deployed (DOCX→PDF conversion)
- ✅ n8n workflow live (20 nodes) at `https://n8n.askarasoft.com/webhook/product-image-extract`
- ✅ Bitrix Outbound Webhook auto-fire on stage "Prepare"
- ✅ 4 attachment format handling: PNG/PDF/DOCX/other
- ✅ Multi-line extraction (QT1 → 3 lines correctly)
- ✅ Taxonomy hints in AI prompt untuk consistent output values
- ✅ End-to-end verified

### v2 + v3 (LIVE, 2026-08-25)
- ✅ R6: Products tab populated via `crm.item.productrow.add` (ownerType `T40e` for SPA 1038)
- ✅ R7: Multi-quotation logic in AI prompt (untested with real multi-quotation file, but code handles N quotations)
- ✅ R8: TRUE SKU hierarchy — parent products in iblock 14, SKU offers in iblock 16 dengan 22 property attributes + parent link (CML2_LINK property 46)
- ✅ R9: Dedup — parent by family name, SKU by variant name; idempotent re-fire
- ✅ End-to-end verified dengan QT1 (PDF + PNG): 3 line items → 3 SKUs → 3 product rows
- ✅ Delete-existing-rows retry logic (Bitrix delete sometimes silently fails on first call)

## Attachment Format Handling

| # | Format | Flow |
|---|---|---|
| 1 | **PNG / JPG / JPEG / WEBP** | Download → base64 → OpenAI Vision (`image_url`, `detail:"high"`) |
| 2 | **PDF** | Download → base64 → OpenAI (`type:"file"`) |
| 3 | **DOCX / DOC** | Download → Gotenberg convert to PDF → OpenAI (`type:"file"`) |
| 4 | **Other** (`.zip`, `.xlsx`, dll) | Skip + timeline comment "Unsupported file format" |

## Multi Line-Item Handling

Sales attach 1 quotation → AI extract semua line item → workflow:
- **Line 1** overwrites original SPA item
- **Line 2+** creates new items di SPA 1038 (linked by `ufCrm8Qref`)

## Docs

- [PRD](docs/PRD.md) (includes v2 requirements)
- [Conversation Log](docs/CONVERSATION_LOG.md) — Michael's WA requests + design decisions
- [Bitrix Schema Reference](docs/BITRIX_SCHEMA_REFERENCE.md) — includes Products tab API
- [Field Mapping (JSON)](docs/bitrix-field-mapping.json)
- [Import Guide](workflow/IMPORT_GUIDE.md)
- Sample files: `docs/Sample QT1/QT2/QT3….docx`

## Cost & Budget

| Item | Estimate |
|---|---|
| Per quotation (PDF/DOCX path) | ~Rp 320 |
| Per quotation (image path) | ~Rp 550 |
| Monthly (100 quotations) | Rp 32k–55k |
| Development effort | ~7–8 hours (fits Rp 500k POC budget) |

## Shared Infrastructure

- VPS + n8n stack: `../deploy/`
- n8n UI: https://n8n.askarasoft.com
- AI provider: OpenAI `gpt-5.5` (reuse `OPENAI_API_KEY`)
- Bitrix instance: `tfssbdemo.bitrix24.com`, user_id 16 full-permission webhook

## Related

- Project 1 (Proposal Estimation): `../proposal-estimation/`
- Project 2 (TLDV Meeting Summary): `../tldv-meeting-summary/`
- Root overview: `../README.md`
