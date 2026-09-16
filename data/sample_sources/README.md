# Sample sources

The curated, verified seed corpus lives in `../seed/sources.json` (loaded
automatically on backend startup). This directory is for **user-supplied**
source metadata that hasn't been through that curation/verification process.

If you have a document you can't legally redistribute in full, you can still
register its metadata and an ingestion path for others to supply the actual
text later, via `POST /api/v1/knowledge/ingest`:

```json
{
  "title": "Exact title of your source",
  "organization": "Publisher or author organization",
  "publication_year": 2023,
  "doi": "10.xxxx/yyyy",
  "url": "https://...",
  "source_type": "peer_reviewed_article",
  "abstract": "A short abstract or summary you have rights to store.",
  "text": null,
  "is_verified": false
}
```

Sources ingested this way are stored with `is_verified: false` and
`ingestion_status: "metadata_only"` if no `text`/`abstract` is supplied,
clearly distinguishing them from the seed corpus until a human confirms
their accuracy. See [../../docs/scientific-grounding.md](../../docs/scientific-grounding.md).
