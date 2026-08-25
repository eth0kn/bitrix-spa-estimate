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

## Requirement Status Matrix

| # | Requirement | Source | Status |
|---|---|---|---|
| R1 | Extract text from image → AI → Bitrix | v1 kickoff | ✅ Live |
| R2 | Handle 4 attachment format (PNG/PDF/DOCX/other) | User expansion of R1 | ✅ Live |
| R3 | Populate 22 custom field per Excel taxonomy | v1 kickoff | ✅ Live |
| R4 | Multi-line item extraction | v1 handoff feedback (Grand > Line noted) | ✅ Live |
| R5 | Snap AI values ke Excel taxonomy | v1 handoff feedback | ✅ Live |
| R6 | Populate Products tab | v2 Req 1 | 🚧 In progress |
| R7 | Multi-quotation → multi-SPA item | v2 Req 2 | 🚧 In progress |
| R8 | Store attributes on Product entity (CRM Products with properties) | v3 Req 1 | 🚧 In progress |
| R9 | Product deduplication by NAME | v3 design decision | 🚧 In progress |

---

## Handoff to Michael — Message Timeline

- **v1 handoff draft**: sent to user for review, user pointed out AI-generated tone
- **v1 handoff revised**: shorter, more human tone — pending Michael review
- **v2 handoff**: pending v2 implementation complete
