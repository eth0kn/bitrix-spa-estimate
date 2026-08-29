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

### v2 + v3 (LIVE, 2026-08-25) → superseded by v4
- v2/v3 baseline: SPA 1038, 1 quotation = 1 SPA item + N productrows

### v4 (LIVE, 2026-08-28)
- ✅ R10: Migrated SPA 1038 → **native Bitrix Quote (entityTypeId 7)**
- ✅ R11: **1 line item = 1 Quote record**
- ✅ Enum values populate: 19 fields, 104 values, mapping [`docs/quote-enum-map.json`](docs/quote-enum-map.json)
- ✅ Enum lookup fuzzy matcher; Idempotent re-fire; Products tab via `crm.quote.productrows.set`
- ✅ SPA 1038 test items deleted; type kept
- ✅ Automation Rule live pada Quote entity stage SENT (verified auto-fire on stage change)

### v4.3 (LIVE, 2026-08-29) — Michael's Sample_1.pdf feedback
- ✅ R12: Multi-quotation multi-revision extraction (Sample_1.pdf: 5 raw quotations → 4 unique after merge → 13 records)
- ✅ Merge by ref: R2 variants (Grey/White colors) merged as 1 quotation via line_no dedup
- ✅ Empty-ref placeholder: quotations without visible ref → `Untitled-{date}-Q{N}`
- ⏳ R13 (Phase 5): DPI preprocess for ref suffix `/sf/jc` — deferred, OpenAI credit exhausted mid-test

### Blocker: OpenAI credits exhausted (2026-08-29)
- Workflow deployed but new extracts fail with HTTP 429 until topup
- Affects Project 1, 2, 3 (shared API key)

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
