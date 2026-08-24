# Bitrix24 Leads API Reference (project scope only)

For **standard CRM Lead** module (bukan SPA seperti Project 1).

## Identity

- Domain: `askarasoft.bitrix24.com` (PRODUCTION — beda dari Project 1 yang di demo)
- Webhook base: `https://askarasoft.bitrix24.com/rest/1/<TOKEN>/` (user_id `1`, token disimpan di env `BITRIX_PROD_URL`)
- ⚠️ Berbeda dengan Project 1 (SPA Proposal Estimation) yang point ke `askarasoftdemo.bitrix24.com` (demo, SPA 2098 hanya ada di sana)

## Endpoints We Use

### 1. crm.lead.get — Get single lead by ID

```
POST /rest/1/<TOKEN>/crm.lead.get
Content-Type: application/json
Body: { "ID": 4759 }
```

Response:
```json
{
  "result": {
    "ID": "4759",
    "TITLE": "PT ABC Lead",
    "NAME": "Budi",
    "LAST_NAME": "Setiawan",
    "STATUS_ID": "NEW",
    "SOURCE_ID": "CALL",
    "EMAIL": [{ "ID": "1", "VALUE": "budi@ptabc.com", "VALUE_TYPE": "WORK" }],
    "PHONE": [{ ... }],
    "COMPANY_TITLE": "PT ABC",
    "OPPORTUNITY": "20000000",
    "CURRENCY_ID": "IDR",
    "ASSIGNED_BY_ID": "15345",
    "DATE_CREATE": "2026-05-01T10:00:00+03:00",
    "COMMENTS": "..."
  }
}
```

Use this for **validation** before posting comment: if 404 or empty result → lead ID invalid.

### 2. crm.lead.list — Search leads (fallback)

```
POST /rest/1/<TOKEN>/crm.lead.list
Content-Type: application/json
Body: {
  "filter": { "ID": 4759 },
  "select": ["ID", "TITLE"]
}
```

Filter operators:
- `=` exact match
- `%` LIKE substring
- `%=` LIKE with wildcards
- `@` IN array

Pagination: fixed 50/page. Use `start` param, response has `next` + `total`.

**When to use:** as fallback if regex fails to extract ID from title, and we want to fuzzy-search by title substring.

### 3. crm.timeline.comment.add — Post comment to lead timeline

```
POST /rest/1/<TOKEN>/crm.timeline.comment.add
Content-Type: application/json
Body: {
  "fields": {
    "ENTITY_ID": 4759,
    "ENTITY_TYPE": "lead",
    "COMMENT": "[b]Header[/b]\n- Item 1\n- Item 2"
  }
}
```

Required fields:
- `ENTITY_ID` (integer) — Lead ID
- `ENTITY_TYPE` (string) — "lead" (also valid: "deal", "contact", "company", "order", "dynamic_XXXX")
- `COMMENT` (string) — Body text

Optional:
- `FILES` (array of `[filename, base64]` pairs)
- `AUTHOR_ID` — NOT documented as param; defaults to webhook's owning user (`1` di production Bitrix)

Response:
```json
{ "result": 123 }  // new comment ID
```

## Comment Format — BBCode (NOT HTML)

Bitrix timeline comments support **BBCode markup**, NOT HTML or markdown.

| Effect | BBCode | Wrong |
|---|---|---|
| Bold | `[b]text[/b]` | `<b>` or `**` |
| Italic | `[i]text[/i]` | `<i>` or `_` |
| Underline | `[u]text[/u]` | |
| URL | `[url=https://x]text[/url]` | `<a href>` or `[text](url)` |
| Line break | `\n` (actual newline char in JSON string) | `<br>` or `\n\n` |
| List | Manual `- item` per line | `<ul><li>` |

Length limit not documented — practical safe limit ~20,000 chars. Chunk longer summaries.

## Sample Request (full)

```bash
curl -X POST "https://askarasoft.bitrix24.com/rest/1/<TOKEN>/crm.timeline.comment.add" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "ENTITY_ID": 4759,
      "ENTITY_TYPE": "lead",
      "COMMENT": "[b]Meeting Summary[/b]\n\n[b]Attendees:[/b]\n- Michael (michael@askarasoft.com)\n- Budi (budi@ptabc.com)\n\n[b]Next Steps:[/b]\n- Send proposal by Friday"
    }
  }'
```

## Rate Limits

- ~2 req/sec per token (soft)
- For our volume (~10-20 meetings/day) — negligible risk

## Gotchas

- ENTITY_TYPE = "lead" (lowercase string), NOT numeric type code
- Newline in JSON must be `\n` (2 chars) not literal newline
- BBCode rendering may vary by Bitrix theme — test with actual output first
- Comment API auto-adds "system" user attribution — no way to override via webhook auth
