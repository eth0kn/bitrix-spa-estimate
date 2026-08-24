# Bitrix24 Schema Reference — SPA Proposal Estimation

> Data ini di-verify lewat live API call ke `askarasoftdemo.bitrix24.com` pada 2026-05-22.
> Reference untuk build workflow n8n.

## Identity

| Item | Value |
|---|---|
| Bitrix domain | `askarasoftdemo.bitrix24.com` |
| Webhook base | `https://askarasoftdemo.bitrix24.com/rest/1177/<YOUR_WEBHOOK_TOKEN>` |
| Entity Type ID | `2098` |
| SPA name | "Proposal Estimation" |
| Category ID (default) | `891` |
| Direct list URL | `https://askarasoftdemo.bitrix24.com/crm/type/2098/list/category/891/` |

## Pipeline Stages

| Order | Display Name | STATUS_ID | Role in Flow |
|---|---|---|---|
| 1 | New | `DT2098_891:NEW` | Initial — Sales fill data |
| 2 | **Request AI Estimation** | `DT2098_891:PREPARATION` | **TRIGGER POINT — webhook to n8n fires here** |
| 3 | Pending | `DT2098_891:CLIENT` | n8n finished, awaiting Michael review |
| 4 | Done | `DT2098_891:UC_79LL63` | Reviewed, accepted |
| 5 | Success (= "Finish" in UI) | `DT2098_891:SUCCESS` | Final |
| 6 | Failed (hidden) | `DT2098_891:FAIL` | Error / rejected |

## Field Schema (verified from sample item id=1)

### Standard Fields
| Field | Type | Sample Value |
|---|---|---|
| `id` | integer | 1 |
| `title` | string | "Proposal PT Sukses Jaya Abadi" |
| `stageId` | string | "DT2098_891:NEW" |
| `categoryId` | integer | 891 |
| `entityTypeId` | integer | 2098 |
| `createdTime` | datetime | "2026-05-12T12:15:24+03:00" |
| `assignedById` | user | 1177 |
| `currencyId` | string | "IDR" |

### Custom Fields (INPUT — diisi Sales, masuk ke prompt AI)

| Field Code | Type | Sample Value | Catatan |
|---|---|---|---|
| `ufCrm497Summary` | string | "Sistem internal untuk manajemen permintaan proyek..." | Free text deskripsi project |
| `ufCrm497FeatureList` | string | "Dashboard project, role management, approval workflow, notification email, export PDF report." | Free text daftar fitur |
| `ufCrm497UploadRfp` | file object | `{id, url, urlMachine}` | File RFP. **Pakai `urlMachine`** untuk download (token-based, machine-readable) |
| `ufCrm497Platform` | array of enum ID | `["9011","9015"]` | **Multi-select!** |
| `ufCrm497IsIntegrate` | enum ID | `9019` | Single value |
| `ufCrm497IntegrationDetail` | string | "Integrasi dengan ERP SAP dan email SMTP perusahaan." | |
| `ufCrm497Complexity` | enum ID | `9025` | Single value |
| `ufCrm497UserScale` | double | 250 | Number of users |
| `ufCrm497Timeline` | enum ID | `9029` | Single value |

### Custom Field (OUTPUT — diisi n8n setelah AI selesai)
| Field Code | Type | Current Sample | Format |
|---|---|---|---|
| `ufCrm497AiTotalMandays` | string | "15 mandays" | **Plain text.** Saat ini cuma "15 mandays" — Michael mungkin mau format breakdown multi-line (lihat PRD §6.3). Field accept newline. |

## Enumeration Mappings

### Platform (`ufCrm497Platform` — MULTI-SELECT)
| ID | Label |
|---|---|
| 9011 | Web |
| 9013 | Mobile |
| 9015 | Portal |
| 9017 | API |

### Integration Required (`ufCrm497IsIntegrate`)
| ID | Label |
|---|---|
| 9019 | Yes |
| 9021 | No |

### Complexity Level (`ufCrm497Complexity`)
| ID | Label |
|---|---|
| 9023 | Low |
| 9025 | Medium |
| 9027 | High |

### Timeline Expectation (`ufCrm497Timeline`)
| ID | Label |
|---|---|
| 9029 | Normal |
| 9031 | Dipercepat |

## API Calls Recap

```bash
# List items
POST /rest/1177/<YOUR_WEBHOOK_TOKEN>/crm.item.list
Body: {"entityTypeId": 2098, "filter": {...}, "select": [...]}

# Get one item
POST /rest/1177/<YOUR_WEBHOOK_TOKEN>/crm.item.get
Body: {"entityTypeId": 2098, "id": <id>}

# Update item (target operation)
POST /rest/1177/<YOUR_WEBHOOK_TOKEN>/crm.item.update
Body: {"entityTypeId": 2098, "id": <id>, "fields": {"ufCrm497AiTotalMandays": "..."}}

# Download file (use urlMachine from item)
GET <urlMachine from ufCrm497UploadRfp.urlMachine>

# Optional: move stage after AI done
POST /rest/1177/<YOUR_WEBHOOK_TOKEN>/crm.item.update
Body: {"entityTypeId": 2098, "id": <id>, "fields": {"stageId": "DT2098_891:CLIENT"}}
```

## Test Data Available

- **1 sample item** at id=1 ("Proposal PT Sukses Jaya Abadi")
- Sudah lengkap semua field termasuk file RFP attachment (file: "Kabinet Logo.png" — bukan RFP asli, cuma placeholder)
- AI Total Mandays Output saat ini: "15 mandays" (sudah diisi sebelumnya)
- Stage saat ini: New

Bisa langsung dipakai untuk test workflow end-to-end. Tinggal pindahkan ke "Request AI Estimation" untuk fire trigger.
