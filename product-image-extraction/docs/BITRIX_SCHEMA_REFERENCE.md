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

## Recreation Script

Idempotent bulk field creation script that produced current schema: see project
memory / migration notes. If schema needs full rebuild, run against a fresh SPA — but
be aware the 6 `_Str`/`_S` suffixed fields are legacy from a mid-development enum→string
conversion. On a clean rebuild use plain names (`UF_CRM_8_STRUCTURE`, etc.).
