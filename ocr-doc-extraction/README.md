# Project 4 — OCR Doc Extraction

Otomatisasi ekstraksi metadata quotation dari PDF text-based ke Bitrix SPA "OCR Doc Extraction" untuk tracking outgoing quotation TFS.

## Status

✅ **LIVE (2026-09-05)** — end-to-end tested dengan 4 sample TFS PRJ quotation.

## Requirements (from Michael's WA 2026-09-05)

> "Ini saya mau ada tambahan project untuk OCR, tapi ini tinggal ambil informasi berikut mas.
> Reference, tanggal, nama perusahaan, item barang, validity, confirmation, delivery, dan timeline"
>
> "Nanti bisa dipisah saja mas, dibuatkan SPA baru begitu untuk keperluan POC ini saja"

## Bitrix Setup

| Item | Value |
|---|---|
| **Tenant** | `tfssbdemo.bitrix24.com` (shared with Project 3) |
| **SPA** | id **12**, entityTypeId **1046**, code `OCRDOC` — "OCR Doc Extraction" (Michael created via UI, renamed via API) |
| **Category** | id **20** "Default pipeline" |
| **Trigger stage** | `DT1046_20:PREPARATION` (Prepare) |
| **Custom fields** | 12 (see [`docs/bitrix-field-mapping.json`](docs/bitrix-field-mapping.json)) |
| **Product rows ownerType** | `T416` |
| **Catalog** | reuses Project 3's iblock 14 (parents) + iblock 16 (SKU offers) |

## Fields Extracted

| Field | Type | Sample value |
|---|---|---|
| Reference | string | `TFS / PRJ / 0099 / 06 / 2026. R3` |
| Quotation Date | date | 2026-07-15 |
| Company Name | string | Space Alliance Contracts Sdn Bhd |
| Attn (Contact) | string | Puan Faza (018-289 2566) |
| Subject (RE) | string | REVISED QUOTATION TENSILE MEMBRANE... |
| Validity | string | 30 days |
| Confirmation | string | Upon receiving your Purchase Order... |
| Delivery | string | 180 working days upon date of confirmation |
| Payment Schedule | string | 50% deposit upon confirmation, 40% prefabrication, 10% completion |
| Project Timeline Start | date | (if stated) |
| Project Timeline End | date | (if stated) |
| Source Document | file | uploaded PDF |

## Line Items → Products Tab

Setiap line item di pricing table quotation di-extract sebagai product row di Products tab. Uses same catalog SKU hierarchy sebagai Project 3:
- Parent product di iblock 14 (by `product_family`, e.g. "HDPE Shade Sail")
- SKU offer di iblock 16 (by full variant name)
- Product row link SKU ke SPA item

## Workflow

- File: [`workflow/ocr-doc-extraction.json`](workflow/ocr-doc-extraction.json) — n8n workflow (16 nodes)
- Endpoint: `https://n8n.askarasoft.com/webhook/ocr-doc-extract`
- Reuses Project 3 infra: pdf2png (200 DPI preprocess), Gotenberg (DOCX→PDF), OpenAI gpt-5.5

## Test Results (2026-09-05)

Test dengan 4 sample TFS PRJ quotation (semua text-based PDF):

| Sample | Ref extracted | Company | Line items |
|---|---|---|---|
| 0092 | TFS/PRJ/0092/05/2026 | Tower Build Steel | 2 (HDPE shade + PE Endorsement) |
| 0099 R3 | TFS/PRJ/0099/06/2026. R3 | Space Alliance Contracts | 6 (multi-option quotation) |
| 0125 R1 | TFS/PRJ/0125/07/2024 (R1) | Satar Empire | 3 |
| 0142 | TFS/PRJ/0142/08/2026 | Kinetics Play | 1 |

Semua 10-11 metadata field ke-extract dengan benar. Reference formatting preserved (slashes, dashes, revision markers R1/R3).

## Cost Estimate

- Text-based PDF: ~Rp 400-600 per file (cheaper than Project 3 tent image extraction)
- Image-scanned PDF: ~Rp 800-1200 per file (fallback via pdf2png)
- Duration: ~15-30 detik per file

## Trigger Setup (Michael via UI)

Automation Rule di SPA "OCR Doc Extraction" (entityTypeId 1046):
1. Buka https://tfssbdemo.bitrix24.com/crm/type/1046/kanban/category/20/
2. Klik **Automation rules** (top right)
3. Di kolom **Prepare**, klik `+ Create` → **Outbound webhook**
4. URL: `https://n8n.askarasoft.com/webhook/ocr-doc-extract`
5. Save

Sales flow:
1. Create new SPA item + attach PDF ke field "Source Document"
2. Drag ke stage **Prepare** (SENT)
3. Wait ~30 sec → refresh → semua field + Products tab populated

## Docs

- [`docs/bitrix-field-mapping.json`](docs/bitrix-field-mapping.json) — 12 UF field IDs
- [`docs/`](docs/) — 4 sample PDF Michael

## Related

- Project 3 (product-image-extraction): `../product-image-extraction/`
- Shared infra: `../deploy/`
