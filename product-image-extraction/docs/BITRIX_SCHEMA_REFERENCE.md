# Bitrix Schema Reference — SPA 1038 (Estimates)

Bitrix instance: `tfssbdemo.bitrix24.com`
Webhook base: `https://tfssbdemo.bitrix24.com/rest/16/qipn7bi17pp91co5`
SPA id: **8** (entityTypeId **1038**)

> **Note**: Bitrix has a naming quirk — `entityId` in `userfieldconfig.*` uses `CRM_8` (SPA id),
> while `crm.item.*` uses `entityTypeId=1038`. Both refer to the same SPA. Field names in
> `userfieldconfig.*` are UPPER_SNAKE (`UF_CRM_8_PRODUCT`), in `crm.item.*` they're camelCase
> (`ufCrm8Product`).

## Custom Fields (29 total)

Full mapping: [`bitrix-field-mapping.json`](bitrix-field-mapping.json)

### Input (Sales fills)

| camelCase (item API) | UPPER_SNAKE (config API) | Type | Purpose |
|---|---|---|---|
| `ufCrm8QuotationDocx` | `UF_CRM_8_QUOTATION_DOCX` | file | Source quotation (PNG/PDF/DOCX) |

### AI-populated line item

| camelCase | UPPER_SNAKE | Type | Label |
|---|---|---|---|
| `ufCrm8Product` | `UF_CRM_8_PRODUCT` | string | Product |
| `ufCrm8Width` | `UF_CRM_8_WIDTH` | string | Width |
| `ufCrm8Length` | `UF_CRM_8_LENGTH` | string | Length |
| `ufCrm8Frame` | `UF_CRM_8_FRAME` | string | Frame |
| `ufCrm8Profile` | `UF_CRM_8_PROFILE` | string | Profile |
| `ufCrm8CanvasMaterial` | `UF_CRM_8_CANVAS_MATERIAL` | string | Canvas Material |
| `ufCrm8Colour` | `UF_CRM_8_COLOUR` | string | Colour |
| `ufCrm8StructureStr` | `UF_CRM_8_STRUCTURE_STR` | string | Structure |
| `ufCrm8CornerTypeStr` | `UF_CRM_8_CORNER_TYPE_STR` | string | Corner Type |
| `ufCrm8SideSupportTypeStr` | `UF_CRM_8_SIDE_SUPPORT_TYPE_STR` | string | Side Support Type |
| `ufCrm8QtySideSupport` | `UF_CRM_8_QTY_SIDE_SUPPORT` | string | Qty Side Support |
| `ufCrm8GroundAnchoringS` | `UF_CRM_8_GROUND_ANCHORING_S` | string | Ground Anchoring |
| `ufCrm8RoofCanvas` | `UF_CRM_8_ROOF_CANVAS` | string | Roof Canvas |
| `ufCrm8Sidewall` | `UF_CRM_8_SIDEWALL` | string | Sidewall |
| `ufCrm8SidewallOption` | `UF_CRM_8_SIDEWALL_OPTION` | string | Sidewall Option |
| `ufCrm8GableEndCanvasS` | `UF_CRM_8_GABLE_END_CANVAS_S` | string | Gable End Canvas |
| `ufCrm8GableEndCanvasDetails` | `UF_CRM_8_GABLE_END_CANVAS_DETAILS` | string | Gable End Canvas Details |
| `ufCrm8GableEndStructureS` | `UF_CRM_8_GABLE_END_STRUCTURE_S` | string | Gable End Structure |
| `ufCrm8Gutter` | `UF_CRM_8_GUTTER` | string | Gutter |
| `ufCrm8Door` | `UF_CRM_8_DOOR` | string | Door |
| `ufCrm8DoorQty` | `UF_CRM_8_DOOR_QTY` | string | Door Qty |
| `ufCrm8Accessories` | `UF_CRM_8_ACCESSORIES` | string | Accessories |

### Meta fields

| camelCase | UPPER_SNAKE | Type | Label |
|---|---|---|---|
| `ufCrm8Qref` | `UF_CRM_8_QREF` | string | Quotation Ref |
| `ufCrm8QuotationDate` | `UF_CRM_8_QUOTATION_DATE` | date | Quotation Date |
| `ufCrm8LineItemNo` | `UF_CRM_8_LINE_ITEM_NO` | integer | Line Item No |
| `ufCrm8UnitPriceRm` | `UF_CRM_8_UNIT_PRICE_RM` | double | Unit Price RM |
| `ufCrm8LineTotalRm` | `UF_CRM_8_LINE_TOTAL_RM` | double | Line Total RM |
| `ufCrm8GrandTotalRm` | `UF_CRM_8_GRAND_TOTAL_RM` | double | Grand Total RM |

## API Recipes

### Read an item

```bash
POST https://tfssbdemo.bitrix24.com/rest/16/qipn7bi17pp91co5/crm.item.get
Content-Type: application/json

{ "entityTypeId": 1038, "id": <ITEM_ID> }
```

Alt: pass `entityTypeId` as query string, `id` as body — either works.

### Update an item

```bash
POST .../crm.item.update?entityTypeId=1038&id=<ITEM_ID>
Content-Type: application/json

{ "fields": { "ufCrm8Product": "15m MQ Tent", "ufCrm8UnitPriceRm": 15000 } }
```

**Gotcha**: `entityTypeId` **must be in query string**, not JSON body — else Bitrix returns
`Could not find value for parameter {entityTypeId}`.

### Add a new item

```bash
POST .../crm.item.add?entityTypeId=1038
Content-Type: application/json

{ "fields": { "title": "QT4 — Line 2", "ufCrm8Qref": "QT4", "ufCrm8LineItemNo": 2, ... } }
```

### List all custom fields (config view)

```bash
POST .../userfieldconfig.list
Content-Type: application/json

{ "moduleId": "crm", "filter": { "entityId": "CRM_8" } }
```

## Products Tab (native Bitrix quotation line items)

Selain custom fields, SPA "Estimates" punya **Products tab** built-in dengan kolom Product / Price / Quantity / Amount + auto-calc subtotal/tax/discount. Populate via `crm.item.productrow.*` API.

### Add product row

```bash
POST .../crm.item.productrow.add
Content-Type: application/json

{
  "fields": {
    "ownerType": "T",              # T = Smart Process Automation
    "ownerId": <SPA_ITEM_ID>,
    "productName": "6m x 15m Aluminium Free Span Structure",
    "price": 34711,
    "quantity": 1,
    "measureName": "block",        # optional: "block", "set", "job", "pcs", etc.
    "measureCode": 796             # optional Bitrix measure ID
  }
}
```

**Notes:**
- `productName` bebas free-text; **tidak wajib** linked ke Bitrix Product Catalog
- `ownerType="T"` untuk SPA items (T = Type — Smart Process Automation)
- Kalau mau linked ke catalog: pakai `productId` instead of `productName`
- Return `productRowId` yang bisa dipakai untuk update/delete row nanti

### List product rows

```bash
POST .../crm.item.productrow.list
{ "filter": { "=ownerType": "T", "=ownerId": <SPA_ITEM_ID> } }
```

### Delete product row (untuk cleanup ulang)

```bash
POST .../crm.item.productrow.delete
{ "id": <PRODUCT_ROW_ID> }
```

**Best practice for workflow re-run**: sebelum add product rows, delete existing rows untuk avoid duplicate accumulation kalau webhook fires 2x.

## Catalog SKU Hierarchy (v3, catalog.* API)

Bitrix Catalog module structure:
- `iblockId=14` — "CRM Product Catalog" (parent products)
- `iblockId=16` — "CRM Product Catalog (offers)" — SKU offers linked ke parent via `CML2_LINK` property (id=46)

Access enabled via Michael grant (2026-08-24).

### List catalogs

```bash
POST .../catalog.catalog.list
{ "select": ["*"] }
```

Returns `{catalogs: [{iblockId: 14, name: "CRM Product Catalog", ...}, {iblockId: 16, productIblockId: 14, skuPropertyId: 46, name: "CRM Product Catalog (offers)", ...}]}`.

### List existing properties (per iblock)

```bash
POST .../catalog.productproperty.list
{ "select": ["*"], "filter": { "iblockId": 16 } }
```

### Add property to SKU offers iblock (v3 setup)

```bash
POST .../catalog.productproperty.add
{
  "fields": {
    "iblockId": 16,
    "name": "Width",
    "code": "WIDTH",
    "propertyType": "S",     # S = string
    "multiple": "N",
    "isRequired": "N",
    "sort": 100
  }
}
```

### Find parent product

```bash
POST .../catalog.product.list
{
  "select": ["id","iblockId","name"],
  "filter": { "iblockId": 14, "=name": "Aluminium Free Span Structure" }
}
```

### Create parent product

```bash
POST .../catalog.product.add
{
  "fields": {
    "iblockId": 14,
    "name": "Aluminium Free Span Structure",
    "active": "Y"
  }
}
```

### Create SKU offer with attributes + parent link

```bash
POST .../catalog.product.add
{
  "fields": {
    "iblockId": 16,
    "name": "6m x 15m Aluminium Free Span Structure, extendible in 5m bays",
    "active": "Y",
    "property46": { "value": <parent_product_id> },
    "property<WIDTH_ID>": { "value": "6m" },
    "property<LENGTH_ID>": { "value": "15m" },
    "property<FRAME_ID>": { "value": "Aluminium" }
    # ... other 22 attributes
  }
}
```

**Note**: property values pass as `propertyN: { value: "..." }` where N is property ID.

### Set price on SKU offer

```bash
POST .../catalog.price.add
{
  "fields": {
    "productId": <sku_offer_id>,
    "catalogGroupId": 1,      # base price group
    "price": 34711,
    "currency": "MYR"
  }
}
```

### Link SKU to Estimate Products tab

```bash
POST .../crm.item.productrow.add
{
  "fields": {
    "ownerType": "T",
    "ownerId": <spa_item_id>,
    "productId": <sku_offer_id>,
    "quantity": 1,
    "price": 34711
  }
}
```

## Legacy CRM Products API (crm.product.*)

Still available for compatibility. See Bitrix docs for `crm.product.add`, `crm.product.property.add`. Not used in v3 design.

## Recreation Script

Idempotent bulk field creation script that produced current schema: see project
memory / migration notes. If schema needs full rebuild, run against a fresh SPA — but
be aware the 6 `_Str`/`_S` suffixed fields are legacy from a mid-development enum→string
conversion. On a clean rebuild use plain names (`UF_CRM_8_STRUCTURE`, etc.).
