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

## Success Criteria (v1 baseline)

1. Sales upload DOCX → within 60s, semua line item populate ke Bitrix ✓
2. Sales upload PDF → same ✓
3. Sales upload PNG/JPG → same ✓
4. Sales upload `.zip` / `.xlsx` → timeline comment "Unsupported" appears ✓
5. Cost per extraction < Rp 1.000 ✓

---

## v2 Additional Requirements (2026-08-24, from Michael follow-up)

Full context: [`CONVERSATION_LOG.md`](CONVERSATION_LOG.md) → v2 section.

### v2 R6 — Populate Bitrix Products tab

Michael: "bisa ngisi yg di product ini ndak mas? Kalau sekarang perlakuannya gimana kalau ada bbrp item?"

Line items harus juga masuk ke **native Bitrix Products tab** (di samping custom fields).

**Design (dual mode, user-approved)**:
- Line items populate BOTH: custom fields per SPA item AND Products tab rows on original item
- API: `crm.item.productrow.add` dengan `productName` free-text (tidak wajib product catalog entry)
- Fields per row: `productName`, `price`, `quantity`, `measureName` (block/set/job/pcs dari quotation)

Result di UI:
- **General tab**: custom field dari line 1 (Product, Width, Frame, dll) + Grand Total
- **Products tab**: SEMUA line items sebagai row (Line 1 tent + Line 2 awning + Line 3 transport)
- Additional SPA items untuk line 2+ tetap ada (spec detail per line)

### v2 R7 — Multi-quotation dalam 1 file

Michael: "kalau misal satu dokumen ada beberapa quotation seperti ini apakah bisa buat beberapa estimates sekaligus?"

Scenario: 1 PDF berisi 2-3 quotation berbeda (batch scan). Workflow bikin N SPA item terpisah, masing-masing dengan quotation-specific data.

**Design (user-approved)**:
- AI output structure baru:
  ```json
  {
    "quotations": [
      { "quotation_ref": "...", "quotation_date": "...", "grand_total_rm": 0, "line_items": [...] },
      { ... }
    ]
  }
  ```
- `quotations[0]` → update SPA item yang Sales attach filenya (original)
- `quotations[1..N]` → create SPA item baru di category 16
- Setiap SPA item ikuti flow v2 R6: line 1 fields + Products tab semua lines + additional SPA items untuk line 2+

### v2 Success Criteria

1. Sales upload PDF berisi 1 quotation → 1 SPA item updated + Products tab populated dengan semua lines
2. Sales upload PDF berisi 3 quotation → 3 SPA item (1 updated + 2 new), each with own Products tab
3. Values di Products tab consistent dengan sum di Grand Total
4. Backward compatible: v1 flow (single quotation, custom fields only) tetap jalan tanpa breaking

## v2 Out of Scope

- ~~Bitrix Product Catalog linking~~ → **moved to v3 (below)**
- Currency conversion (still RM only)
- Discount/tax split (grand total assumed = sum of lines, no tax logic)
- Multiple original items batch update (only 1 file → N items, tidak N files → M items)

---

## v3 Additional Requirements (2026-08-24, from Michael follow-up after v2 planning)

Full context: [`CONVERSATION_LOG.md`](CONVERSATION_LOG.md) → v3 section.

### v3 R8 — Store attributes on Product entity (TRUE SKU hierarchy)

Michael: "simpannya di SKU property untuk attribute snya, waktu create estimates dia akan membuat product dengan attribute yang sesuai"

**Intent**: Attributes di Product entity as SKU properties, per Michael's screenshot menampilkan Bitrix Catalog UI dengan "Add SKU" + property columns.

**Access granted 2026-08-24**: Michael grant catalog module scope untuk webhook → full `catalog.*` API available.

**Design (Option B, user-approved)**:
- **Parent products** di iblock 14 (base name = product family, e.g. "Aluminium Free Span Structure")
- **SKU offers** di iblock 16 dengan 22 attribute properties + price + parent link (`CML2_LINK` property id 46)
- AI extract tambah `product_family` field (grouping key)
- Per line item:
  1. Find/create parent product di iblock 14 by `product_family`
  2. Create SKU offer di iblock 16 dengan property values (22 attrs) + price + parent link
  3. Add product row to Estimate → Products tab, reference SKU offer ID

### v3 R9 — Deduplication strategy (revised for SKU hierarchy)

**Design (user-approved)**:
- **Parent**: dedup by family name (product_family exact match)
- **SKU**: dedup by parent + attribute combo (Width+Length+Frame+Colour signature)
- Same specs → reuse SKU
- Different specs → new SKU under same parent

### v3 SPA custom fields — Dual mode kept

**Design (user-approved)**:
- SPA custom fields tetap populate dari line 1 (summary view di General tab)
- Products tab menampilkan linked catalog products dengan attributes (detail per line)
- Redundancy for backward compat + easier at-glance view

### v3 Success Criteria

1. Sales upload quotation → workflow auto-create/find Product di catalog dengan attributes
2. Estimate Products tab reference `productId` (bisa klik ke Product detail, lihat attributes)
3. 2 quotation berbeda dengan product name identik → reuse product, no duplicates
4. SPA custom fields tetap populate (backward compat)
5. Backward compat: v1 flow (single quotation, no Products tab) tetap functional

## v3 Out of Scope

- ~~True SKU variants (Trade Offers)~~ → **now IN SCOPE after Michael grant catalog access**
- Product image auto-attach (from extracted quotation image)
- Currency conversion (RM only)
- Auto product-family normalization dengan fuzzy matching (misal "Aluminium Free Span Structure" vs "Alu FreeSpan Tent" — treated as different families unless AI extract same product_family)
- Product catalog sections (semua products flat di iblock 14 root)
