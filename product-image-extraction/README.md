# Project 3 — Product Image Extraction → Bitrix Estimate

Otomatisasi ekstraksi produk dari image / PDF / DOCX quotation → OpenAI → populate Bitrix SPA
"Estimates" (entityTypeId **1038**) dengan 22 spec + 6 meta field per line item.

## Status

🚧 **POC ready to deploy** — deadline Senin.

- ✅ Bitrix schema created (29 custom fields via API)
- ✅ Gotenberg sidecar added to docker-compose (DOCX→PDF)
- ✅ OpenAI PDF-direct extraction verified on 3 sample quotations (QT1/QT2/QT3)
- ✅ n8n workflow JSON built (20 nodes, handles 4 attachment formats)
- ⏳ Deploy env var + gotenberg to VPS (blocked: SSH key needs re-add)
- ⏳ Import workflow to n8n instance
- ⏳ Setup Bitrix Automation Rule trigger
- ⏳ End-to-end test

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

- [PRD](docs/PRD.md)
- [Bitrix Schema Reference](docs/BITRIX_SCHEMA_REFERENCE.md)
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
