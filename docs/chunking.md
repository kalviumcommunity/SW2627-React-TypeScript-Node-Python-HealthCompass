# Document chunking — Sprint task 3.21

Chunking consumes extracted or cleaned `DocumentPage` records and produces exact
text slices. It does not call an embedding API or require credentials.

## Strategies and default

- `fixed`: consecutive windows of at most `max_chars` Unicode code points.
- `paragraph` (default): prefer the last blank-line paragraph boundary inside
  the window. If a paragraph exceeds the limit, use a hard character cut.

Both strategies respect page boundaries, preserve all non-whitespace content,
and make forward progress even with very small limits. No overlap is added.
Whitespace-only slices and empty pages emit no chunks. A document cleaned down
to no usable text therefore emits an empty list, rather than a fabricated chunk.

The default limit is 1,000 characters. This is a configurable engineering default,
not a measured model context limit. Token-aware sizing/overlap belongs to 3.23.
Character cuts may divide words or multi-code-point graphemes; this is particularly
relevant for oversized paragraphs. Prefer cleaned NFC text for consistency.

## Reproduce the comparison

```bash
python experiments/chunking_comparison.py tests/fixtures/chunking_guidance.txt --max-chars 160
```

Measured on the committed synthetic fixture after cleaning, with a 160-character
limit and five paragraphs:

| Strategy | Chunks | Minimum chars | Maximum chars | Mean chars | Split paragraphs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fixed | 3 | 134 | 160 | 151.33 | 2 |
| Paragraph | 4 | 82 | 151 | 113.50 | 0 |

Paragraph-aware chunking is the default because it preserves these short sections
at the cost of more, smaller chunks. This is a structural sanity comparison on
one synthetic document, not evidence of better retrieval recall or answer quality.
Re-evaluate on the selected real corpus before tuning production settings.

## Source contract

Each chunk includes its document ID, source path, filename, PDF page number,
per-page zero-based chunk index, and a copy of source metadata. `start_char` is
inclusive and `end_char` exclusive: `chunk.text == page.text[start_char:end_char]`.
These offsets reference the supplied text, not PDF coordinates or original bytes.
When `input_kind=cleaned`, they reference cleaned text, not `original_text`.

IDs hash the original document ID, page position, supplied text hash, input kind,
strategy, size limit, offsets, and chunking version. Identical content copied to
another path intentionally shares IDs; source path is retained separately.
Changes to input text or chunking settings produce different IDs. Metadata-only
changes do not change IDs and must be propagated separately during future indexing.

`input_sha256` allows a consumer to check that it is using the matching page text.
Chunking version is currently `1`. This establishes basic source traceability;
more detailed citation metadata and index integration are separate sprint work.


## Compatibility with the earlier single-page baseline

The merged Task-3.21 baseline remains available through `fixed_size_chunks`,
`paragraph_chunks`, `Chunk`, `ChunkingStats`, and `calculate_chunk_stats`.
`chunk_document(page, strategy="fixed", chunk_size=500, overlap=100)` retains
that API. Fixed overlap settings are validated to prevent a non-advancing loop.
The baseline paragraph helper emits one chunk per paragraph without a size limit.

For bounded chunks with page offsets and content-based IDs, use `chunk_page(page)`
or `chunk_document(pages, max_chars=1000)` with a page iterable. The baseline's
sequential integer IDs must not be treated as globally unique index identifiers.
Character overlap in that baseline is not token-aware sizing (Task 3.23).
Its earlier comparison script is retained at `experiments/basic_chunking_comparison.py`;
use `experiments/chunking_comparison.py` for the bounded strategies documented above.

## Tagging chunks for citations

Use `tag_chunks` when an index expects a uniform text-plus-metadata record:

```python
from healthcompass.ingestion import tag_chunks

records = tag_chunks(
  "refund-policy.pdf",
  [("Refunds are available within 30 days.", 120)],
  metadata={"section": "Eligibility", "page": 3, "effective_date": "2026-01-01"},
)
```

Every record contains `text` and a metadata dictionary with `source`,
`chunk_index`, and `char_start`. Additional fields such as section, page, and
effective date are copied to every chunk. Required fields win if caller metadata
contains the same keys, and the input metadata is never mutated. Pass bare text
strings when character positions are unavailable; `char_start` will be `None`.
