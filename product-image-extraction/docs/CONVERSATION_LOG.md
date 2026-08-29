# Conversation Log — Michael Chandra (Askarasoft/TFSSB)

Historical record of requirement messages received during Project 3 development.
Used to trace back decisions to original customer intent.

---

## v1 kickoff — 2026-08-24 (WA, Sunday)

Michael's original WA (paraphrased from screenshot):

> Mas, ada task baru untuk client TFSSB.
> 1. Extract text dari image
> 2. Kirim ke AI untuk parsing
> 3. Populate Bitrix "estimates" dengan harga + product attribute
>
> Bonus: buat 22 Product Attribute di Bitrix sesuai Excel taxonomy (attached MQ Details.xlsx).
>
> Deadline: hari Senin (POC scope).
> Budget: Rp 500.000.
> Model AI: sama seperti project sebelumnya (OpenAI gpt-5.5).

**Attachments** received:
- `MQ Details.xlsx` — 22 tent attribute taxonomy dengan allowed values per column
- `Sample QT1-15m Mq Tent (850) (Open Tent), Awning (560).docx`
- `Sample QT2 - 15m MQ Tent (850).docx`
- `Sample QT3 - 15m MQ Tent (850).docx`

**Bitrix instance**: `tfssbdemo.bitrix24.com` (demo tenant, user 16 punya full-permission webhook)

**v1 delivery** (completed 2026-08-24 evening):
- 29 custom field dibuat via API di SPA "Estimates" (entityTypeId 1038)
- n8n workflow live: `https://n8n.askarasoft.com/webhook/product-image-extract`
- Handle 4 attachment format: PNG/JPG, PDF, DOCX (via Gotenberg), other (Bitrix comment)
- Bitrix Outbound Webhook automation rule fires di stage change "Prepare"
- Multi-line extraction working (QT1 → 3 line items: main tent + awning + transport)
- Taxonomy hint di AI prompt supaya nilai output snap ke Excel taxonomy

---

## v2 follow-up — 2026-08-24 (later, after v1 handoff draft shown)

Michael reviewed the draft handoff and screenshot of live Bitrix items, kemudian request 2 tambahan:

### v2 Req 1 — Products tab

> "Mas, bisa ngisi yg di product ini ndak mas? Kalau sekarang perlakuannya gimana kalau ada bbrp item?"

**Screenshot attached**: Bitrix SPA Estimates #40 detail view, **Products tab** kosong dengan:
- Kolom: Product / Price / Quantity / Amount
- "Add product" button
- Total without discounts and taxes / Delivery price / Discount amount / Total before tax / Tax total / Total amount

**Interpretation**: Michael wants line items also populate ke NATIVE Bitrix Products tab (di samping custom field), bukan cuma custom fields. Ini bagian standard Bitrix untuk quotation dengan built-in subtotal/tax/discount calculation.

**Design decision** (user-approved 2026-08-24):
- **Products tab + custom fields (dual mode)** — line items go to BOTH
- Original SPA item: custom fields from line 1 (main product spec) + ALL line items sebagai product rows di Products tab
- Additional SPA items untuk line 2+: custom fields dari line specific + also product row untuk transparency
- Bitrix API: `crm.item.productrow.add` dengan `productName` (free-text, tidak wajib linked ke Product Catalog)

### v2 Req 2 — Multi-quotation in 1 file

> "Ada tambahan mas, kalau misal satu dokumen ada beberapa quotation seperti ini apakah bisa buat beberapa estimates sekaligus?"

**Scenario**: 1 PDF berisi 2-3 quotation berbeda (misal supplier kirim batch QT1 + QT2 + QT3 di-scan/consolidate jadi 1 file). Sales upload sekali, workflow otomatis bikin 3 estimate SPA item terpisah.

**Design decision** (user-approved 2026-08-24):
- **First quotation updates original, rest create new**
- AI extract output structure berubah: `{ quotations: [ { ref, date, grand_total, line_items: [...] } ] }`
- `quotations[0]` → update SPA item yang Sales attach filenya
- `quotations[1..N]` → create new SPA item baru di category 16 (Estimates)
- Semua share ufCrm8QuotationDocx attach yang sama? Atau file cuma di item pertama? — **TBD**: file stays on original item only; new items have Qref reference to trace back

---

## v3 follow-up — 2026-08-24 (after v2 doc review)

Michael's message (before v2 implementation started):

> "Mas, ini coba simpannya di SKU property disini mas untuk attribute snya, jadi nanti waktu create estimates, dia akan membuat product dengan attribute yang sesuai"
>
> "Simpannya nanti di product tadi mas"

**Screenshot attached**: Bitrix "New product" creation UI showing:
- General Parameters (Name, Detailed description)
- **ADD SKU** section with SKU rows
- Columns: Retail price, Available stock, Width (mm), Width
- Circled: "add new value" dropdown showing values `3m, 6m, 9m, 19m`
- "Create SKU property" link at bottom

**Interpretation**: Michael wants extracted attributes stored ON the Product entity (as SKU properties), not just as custom fields on Estimate SPA. When workflow creates an Estimate, it should also create/find a Product with matching attributes.

### v3 API scope constraint (initial) → resolved 2026-08-24

Initial test: webhook `qipn7bi17pp91co5` had `catalog.*` access denied.

**Resolution** (after user asked Michael): Michael granted catalog module scope. Re-test:
- `catalog.catalog.list` → ✅ Works
- `catalog.product.list` → ✅ Works
- `catalog.section.list` → ✅ Works
- `catalog.productproperty.list` → ✅ Works
- Catalog structure discovered:
  - `iblockId=14` = "CRM Product Catalog" (parent products)
  - `iblockId=16` = "CRM Product Catalog (offers)" — SKU offers (linked ke parent via property `CML2_LINK` id=46)
- Existing properties: `MORE_PHOTO` (Image, iblock 14) + `CML2_LINK` (SKU link, iblock 16)

### v3 Design decision (user-approved 2026-08-24) — REVISED after scope granted

**Option B — TRUE SKU hierarchy** (chosen after catalog.* access granted)
- **Parent products** di iblock 14 by `product_family` (e.g. "Aluminium Free Span Structure")
- **SKU offers** di iblock 16 dengan 22 attribute properties + price + parent link (CML2_LINK=46)
- AI prompt extended: extract `product_family` per line item (grouping key)
- Per line item flow:
  1. Find/create parent in iblock 14 by `product_family`
  2. Create SKU offer in iblock 16 dengan property values (Width, Length, Frame, dll) + parent link
  3. Add product row to Estimate → Products tab, reference SKU offer ID

**Deduplication** (chosen): **Parent by family name, SKU by attribute combo**
- Parent: 2 quotations dengan family "Aluminium Free Span Structure" → 1 parent
- SKU: 2 quotations dengan same family + same specs (Width+Length+Frame) → 1 SKU reused
- Different specs → new SKU under same parent

**SPA custom fields** (chosen): **Keep dual mode**
- Custom fields tetap populate dari line 1 (summary di General tab)
- Products tab menampilkan linked SKU offers (detail per line)

**API usage**:
- `catalog.product.add`, `catalog.product.list` (iblockId=14 filter, parent products)
- `catalog.product.add`, `catalog.product.list` (iblockId=16 filter, SKU offers)
- `catalog.productproperty.add` (setup 22 attribute properties on iblock 16)
- `catalog.price.add` (set SKU price)
- `crm.item.productrow.add` (link SKU to Estimate)

---

## v4 follow-up — 2026-08-28 (after v3 handoff test)

Michael's feedback after testing v3:

> "Mas, ini saya cek masih perlu ada adjustment karena yg terinput sekarang hanya atributnya milik produk pertama, sedangkan atribut milik produk kedua dan ketiga tidak terisi. Perlu buat 3 estimate apabila ada 3 produk dalam 1 quotation."
>
> "Goalsnya nanti:
> 1. Mengubah dari SPA estimates ke fitur estimate bawaan bitrix
> 2. Satu quotation yang ada 3 product akan membuat 3 record berbeda, jadi 1 product 1 record, untuk keperluan analytics agar lebih mudah"

**Interpretation & design decisions (user-approved 2026-08-28)**:

### v4 R10 — Migrate SPA (1038) → native Bitrix Quote (entityTypeId 7)
- Team lain sudah setup 29 UF field di Quote entity dan 19 enum values (dengan minor typos: Alumunium, Continous, Concreate, PVC bracke, Semi - Permanent dengan spaces)
- Quote statuses sudah di-rename team match SPA flow: DRAFT=Start, SENT=Prepare (trigger), UC_PXE68A=Approval, APPROVED=Accepted, DECLAINED=Declined, APOLOGY=Analyze decline
- Team's draft n8n workflow modified but never published (couldn't solve)
- Enum populate via API confirmed WORKS on Quote (previously failed on SPA)

### v4 R11 — 1 line item = 1 Quote record (bukan 1 quotation = 1 record)
- Previous v3 design: 1 quotation dengan 3 line items → 1 SPA item + 3 productrows (only line 1's specs in fields)
- New design: 1 quotation dengan 3 line items → 3 SEPARATE Quote records, each with own specs + own 1 productrow
- Rationale (Michael): easier analytics, each product = 1 analytics unit
- Multi-quotation still supported: M quotations × N lines each = M×N Quote records (all flat, grouped by shared ufCrmQuoteQref)

### v4 Idempotency strategy
- On re-fire: lookup existing Quotes by `ufCrmQuoteQref`, delete siblings (except origItemId), re-create fresh
- Product rows on Quote use `crm.quote.productrows.set` (atomic replace, no dup)

### v4 SPA 1038 cleanup
- SPA 1038 test items deleted
- SPA type 8 KEPT (not deleted) — schema reference for team, no runtime cost

### v4 Ambiguities resolved (user-approved via question rounds)
1. Enum handling: **populate via API from Excel taxonomy** (team already did this, my script confirmed values via crm.item.fields)
2. SPA cleanup: **delete test items, keep type as reference** (not fully archive since no clean archive API)
3. Multi-quot combo: **5 Quote records if 1 file has 2 quotations of 3+2 lines** (flat, share quotationRef for analytics grouping)
4. Automation rule: **API first (denied), fallback UI** — Michael setup on Quote entity, SENT stage

## Requirement Status Matrix

| # | Requirement | Source | Status |
|---|---|---|---|
| R1 | Extract text from image → AI → Bitrix | v1 kickoff | ✅ Live |
| R2 | Handle 4 attachment format (PNG/PDF/DOCX/other) | User expansion of R1 | ✅ Live |
| R3 | Populate 22 custom field per Excel taxonomy | v1 kickoff | ✅ Live |
| R4 | Multi-line item extraction | v1 handoff feedback | ✅ Live |
| R5 | Snap AI values ke Excel taxonomy | v1 handoff feedback | ✅ Live |
| R6 | Populate Products tab | v2 Req 1 | ✅ Live (via crm.quote.productrows.set) |
| R7 | Multi-quotation → multi-record | v2 Req 2 | ✅ Live (now flat, 1 line = 1 record) |
| R8 | Store attributes on Product entity (SKU hierarchy) | v3 Req 1 | ✅ Live (parent iblock 14 + SKU iblock 16) |
| R9 | Product deduplication by NAME | v3 design decision | ✅ Live |
| R10 | Migrate SPA 1038 → native Quote 7 | v4 Req | ✅ Live |
| R11 | 1 line item = 1 Quote record | v4 Req | ✅ Live |
| R12 | Multi-quotation multi-revision extract (Michael's Sample_1.pdf) | v4.1 Req | ✅ v4.3 Live |
| R13 | Ref extraction with slash suffix (e.g. /sf/jc) | v4.1 Req | ⏳ Partial (DPI Phase 5 deferred — OpenAI credit exhausted) |

---

## v4.1-v4.3 iteration — 2026-08-29 (Michael's Sample_1.pdf feedback)

Michael's feedback: "PDF Masih perlu adjustment, quotenya yang dibaca sepertinya hanya 1 mas... untuk QT-10/24-0014-R1/sf/jc tidak tergenrate... nama quotationnya hanya QT-10/24-0014-R2 tidak ada tambahan /sf/jc"

Michael's Sample_1.pdf (19MB, 25 pages, image-only PDF from EMF-embedded DOCX) analyzed:
- AI first pass extracts **5 quotations**: Q1-Q3 (empty ref), Q4-Q5 (both with truncated "QT-10/24-0014-R2")
- Q4 and Q5 are actually **variant options** of R2 (Grey vs White colors) — not true duplicates
- Ref suffix `/sf/jc` consistently truncated by AI Vision OCR (limitation on 25-page image PDF)

### Iterations tried
- **v4.1**: Prompt improvement (dedup rule, ref verbatim instruction) → no material change (AI-side rules ignored on complex layouts)
- **v4.2**: Workflow post-processing dedup (by signature) + placeholder for empty ref + 2nd AI pass for ref extraction → dedup didn't work (variants have different signatures) + 2nd pass still truncated
- **v4.3** (SHIPPED): Merge by ref (not signature) → variants merged into 1 quotation via line_no dedup → 13 records from 17 raw

### User decisions (v4.1-v4.3 rounds)
1. Empty-ref quotations → **placeholder** `Untitled-{date}-Q{N}` (Michael's Q1-Q3 preserved as separate records)
2. R2 variants (Grey/White) → **merge as 1 quotation** (keep first line per line_no, drop variant duplicates)
3. Ref truncation fix strategy: **DPI preprocess** (Phase 5, deferred due to OpenAI credit exhaustion)

### v4.3 Final result on Michael's Sample_1.pdf
```
- QT-10/24-0014-R2 (Marquee tent variants merged): 4 records
- Untitled-2024-09-30-Q2 (10x15 tent): 2 records
- Untitled-2024-10-28-Q3 (8x12 tent): 3 records
- Untitled-2025-01-31-Q4 (6x13 tent): 4 records
Total: 13 records (down from 17 in v4.2)
```

### Known limitations (v4.3)
- Ref suffix `/sf/jc` truncated for QT-10/24-0014-R2 (AI OCR limit at default resolution). Michael must manually append via UI if needed.
- Q1-Q3 refs use placeholder — AI couldn't OCR their refs on those pages. Michael must edit ufCrmQuoteQref via UI to correct if desired.
- Variant metadata (Grey vs White) lost during merge (kept first variant's product_variant_name).

### Phase 5 backlog (post-topup)
- Higher-DPI PDF preprocessing (pdf2image 200-300 DPI) → send hi-res image_url to OpenAI Vision → improved OCR for ref suffix
- Optional: multi-pass extraction (per section) for very long PDFs (>10 pages)

### OpenAI credit blocker (2026-08-29)
- Mid-test HTTP 429: "You have no credits remaining"
- Impact: workflow deployed but ANY new extract fails until Michael tops up
- Affects Project 1, 2, 3 (shared key)

---

## Handoff to Michael — Message Timeline

- **v1 handoff draft**: sent to user for review, user pointed out AI-generated tone
- **v1 handoff revised**: shorter, more human tone — pending Michael review
- **v2 handoff**: pending v2 implementation complete
