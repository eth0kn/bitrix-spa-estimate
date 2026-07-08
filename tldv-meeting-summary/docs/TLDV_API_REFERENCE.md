# TLDV API Reference (project scope only)

Data verified via live API calls on 2026-07-08 using API key.

## Auth

Header: `x-api-key: <TLDV_API_KEY>`

## Base URL

`https://pasta.tldv.io/v1alpha1/` ⚠️ **Note**: alpha versioning — breaking changes possible

## Endpoints We Use

### 1. GET /meetings — List meetings (for exploration/backfill)

```
GET https://pasta.tldv.io/v1alpha1/meetings
```

Response (paginated):
```json
{
  "page": 1,
  "pageSize": 50,
  "pages": 14,
  "total": 657,
  "results": [
    {
      "id": "6a4dbd36912a5400133f688a",
      "name": "meeting title",
      "happenedAt": "2026-07-08T03:00:00.000Z",
      "duration": 7049.038,
      "invitees": [{ "name": "", "email": "..." }],
      "organizer": { "name": "...", "email": "..." },
      "url": "https://tldv.io/app/meetings/...",
      "extraProperties": { "conferenceId": "kdz-ppdt-ncg" }
    }
  ]
}
```

### 2. GET /meetings/{meetingId} — Get single meeting metadata

```
GET https://pasta.tldv.io/v1alpha1/meetings/{meetingId}
```

Response same shape as single result above, PLUS:
- `template`: `{ id, label }` — AI template used for summarization within TLDV

⚠️ Return 403 for non-existent ID (weird — some other endpoints return 404).

### 3. GET /meetings/{meetingId}/transcript

```
GET https://pasta.tldv.io/v1alpha1/meetings/{meetingId}/transcript
```

Response:
```json
{
  "id": "string",
  "meetingId": "string",
  "data": [
    { "speaker": "string", "text": "string", "startTime": 0, "endTime": 0 }
  ]
}
```

⚠️ 404 if transcript not yet ready. For our workflow, transcript **arrives inline** via TranscriptReady webhook, so this endpoint may be unnecessary (fallback only).

## Webhooks

### Events Available

| Event | Fires When | Includes |
|---|---|---|
| `MeetingReady` | Meeting record finalized | Meeting metadata (name, organizer, invitees, url, duration). NO transcript. |
| `TranscriptReady` | Transcript generation complete | Transcript inline. NO meeting metadata (no name/title). |

### Payload — TranscriptReady

```json
{
  "id": "webhook-<uuid>",
  "event": "TranscriptReady",
  "data": {
    "id": "<meetingId>",
    "meetingId": "<meetingId>",
    "data": {
      "transcript": "full text ...",
      "segments": [
        { "startTime": 0, "endTime": 5, "text": "..." }
      ]
    }
  },
  "executedAt": "2026-01-15T10:35:00Z"
}
```

### Auth

TLDV webhook has **no HMAC/signature** by default. Verification options:
- URL secret: `/webhook/tldv-transcript-ready/<random-secret>`, verify in n8n
- OR trust source (private endpoint, obscure path)

## Our Workflow Choice: Option B

Subscribe to `TranscriptReady` (reliable — transcript guaranteed ready) + separate `GET /meetings/{id}` for metadata (name/title needed for lead ID parsing).

## Gotchas

- Base host is `pasta.tldv.io` (not `api.tldv.io`)
- `/v1alpha1/` versioning — expect breakage; wrap all calls in error handler
- Rate limits not documented — implement retry with backoff
- Existing Askarasoft account has **657 meetings** historical → good for testing (Michael's approval needed to touch existing data)
