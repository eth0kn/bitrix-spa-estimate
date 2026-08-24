# PRD — Product Image Extraction (Project 3)

| | |
|---|---|
| **Customer** | Askarasoft / TFSSB (Tent Fabrication SSB) — PIC Michael Chandra |
| **Bitrix Instance** | `tfssbdemo.bitrix24.com` (demo tenant; user_id=16, full-permission webhook) |
| **SPA** | entityTypeId **1038** (id **8**) — "Estimates" |
| **Deadline** | Senin (POC) |
| **Budget** | Rp 500.000 |
| **AI Model** | OpenAI `gpt-5.5` (reuse shared `OPENAI_API_KEY`) |

## Problem

Sales team di TFSSB terima quotation dari supplier dalam bentuk **image / PDF / Word doc** (`.docx`). Selama ini data harga & spesifikasi tent harus diketik ulang manual ke Bitrix estimate. Slow + error-prone (22 attribute per line item).

## Goal

Sales upload file ke SPA Estimates → workflow otomatis:
1. Detect format
2. Convert kalau perlu (DOCX → PDF)
3. AI extract semua line item + spec
4. Populate 22 field custom di Bitrix, satu SPA item per line item

## Trigger

Bitrix **Automation Rule** on SPA 1038 fires ketika stage berubah ke "Prepare Extraction" (or equivalent), sends POST ke n8n webhook `/webhook/product-image-extract` with `{item_id}`.

## Input Format Handling (4 Scenarios)

| Scenario | Extension | Flow | Cost (est.) |
|---|---|---|---|
| **1. Image** | `.png` `.jpg` `.jpeg` `.webp` | Download → base64 → OpenAI Vision (`type:"image_url"`, `detail:"high"`) | ~Rp 550/call (hires vision) |
| **2. PDF** | `.pdf` | Download → base64 → OpenAI (`type:"file"`, `file_data`) | ~Rp 320/call (direct file input, cheapest) |
| **3. DOCX** | `.docx` `.doc` | Download → **Gotenberg** convert to PDF → base64 → OpenAI (`type:"file"`) | ~Rp 320/call + local conv (free) |
| **4. Other** | anything else | Add Bitrix timeline comment "Unsupported file format" + END | Rp 0 |

Detection: filename extension parsed in **Detect Format** Code node. Extension-based; MIME sniffing kalau perlu bisa ditambah later.

## Bitrix Schema

29 custom fields dibuat via API (Aug 2026):

**File field (Sales input)**:
- `ufCrm8QuotationDocx` — file upload untuk source quotation

**Line item output** (22 spec + 6 meta):

| Field | Type | Purpose |
|---|---|---|
| `ufCrm8Product` | string | Product name (e.g. "15m MQ Tent") |
| `ufCrm8Width`, `ufCrm8Length` | string | Dimensions |
| `ufCrm8Frame`, `ufCrm8Profile`, `ufCrm8CanvasMaterial`, `ufCrm8Colour` | string | Base spec |
| `ufCrm8StructureStr`, `ufCrm8CornerTypeStr`, `ufCrm8SideSupportTypeStr` | string | Structural (was enum, now string for POC) |
| `ufCrm8QtySideSupport` | string | Count |
| `ufCrm8GroundAnchoringS`, `ufCrm8RoofCanvas`, `ufCrm8Sidewall`, `ufCrm8SidewallOption` | string | Attachment specs |
| `ufCrm8GableEndCanvasS`, `ufCrm8GableEndCanvasDetails`, `ufCrm8GableEndStructureS` | string | Gable specs |
| `ufCrm8Gutter`, `ufCrm8Door`, `ufCrm8DoorQty`, `ufCrm8Accessories` | string | Options |
| `ufCrm8Qref` | string | Quotation reference number |
| `ufCrm8QuotationDate` | date | Quotation date |
| `ufCrm8LineItemNo` | integer | Line number within quotation |
| `ufCrm8UnitPriceRm`, `ufCrm8LineTotalRm`, `ufCrm8GrandTotalRm` | double | Prices in RM |

Complete mapping: `docs/bitrix-field-mapping.json`.

**Naming quirks**: `_Str` / `_S` suffix pada 6 field karena awalnya dibuat sebagai enum type (lalu dihapus & recreate as string). Bitrix nolak recreate dengan nama sama immediately, jadi disuffix. Field labels tetap clean di UI ("Structure", "Corner Type", dst).

## Multi Line Item Behavior

Kalau quotation punya >1 line item:
- Line **1** → `crm.item.update` ke item ASLI (yang Sales attach filenya)
- Line **2..N** → `crm.item.add` new items di SPA 1038 yang sama, dengan title `{quotation_ref} — Line {N}`, semua share `ufCrm8Qref` supaya bisa di-filter/group

## AI Prompt Design

System: "Precise data extractor for tent quotations. Output ONLY valid JSON. Match spec taxonomy exactly. Empty string for missing. Numbers as numbers, dates YYYY-MM-DD."

User: JSON schema template + attached file content.

Reasoning: gpt-5.5 dengan `response_format: {type: "json_object"}` untuk enforce valid JSON. `max_completion_tokens: 8000`.

## Cost Estimate (per quotation)

| Component | Estimated |
|---|---|
| OpenAI extract call (PDF/DOCX path) | ~Rp 320 |
| OpenAI extract call (image path) | ~Rp 550 |
| Gotenberg convert | Rp 0 (local) |
| Bitrix API calls (1 read + N writes) | Rp 0 |
| **Total per quotation** | **~Rp 320–550** |

Assume 100 quotations/month → **Rp 32k–55k/bulan** operational cost. Well within budget.

## Development Effort

- Bitrix schema setup: 2h (done via API automation)
- Gotenberg deployment: 30min (docker-compose sidecar)
- Workflow design + build: 3h
- Testing with 3 sample DOCX: 1h
- Docs + handover: 1h
- **Total: ~7-8h** (fits Rp 500k budget)

## Out of Scope for POC

- Multi-page image scanning (Sales attach 5 photos of quotation) — POC handle single-file only
- Currency conversion (USD/IDR to RM)
- Product catalog matching / SKU lookup
- Approval flow beyond Bitrix stage change
- OCR quality reporting / confidence score

## Success Criteria

1. Sales upload DOCX → within 60s, semua line item populate ke Bitrix ✓
2. Sales upload PDF → same ✓
3. Sales upload PNG/JPG → same ✓
4. Sales upload `.zip` / `.xlsx` → timeline comment "Unsupported" appears ✓
5. Cost per extraction < Rp 1.000 ✓
