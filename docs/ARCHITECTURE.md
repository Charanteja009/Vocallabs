# Sakshi architecture

```mermaid
flowchart LR
  A["Challan photo"] --> B["Groq vision extraction"]
  C["Hindi/Hinglish voice note"] --> D["Groq Whisper transcription"]
  B --> E["Structured claims + provenance"]
  D --> E
  E --> F["AI conflict identification"]
  F --> G["Deterministic safety policy"]
  G -->|"Conflict / missing / low quality"| H["HOLD FOR REVIEW"]
  G -->|"Model or network failure"| I["PENDING REVIEW"]
  G -->|"Complete, consistent evidence"| J["RECOMMEND PROCEED"]
  H --> K["Evidence-specific next action + review packet"]
  I --> K
  L["20-case safety evaluation"] --> G
```

## Decision boundary

Models can read difficult handwriting, transcribe code-mixed speech, and identify candidate conflicts. They cannot authorize payment. The application enforces the final state: any conflict, unreadable critical field, missing evidence, or low evidence quality routes to review.

## Production path

At higher scale, keep uploads in object storage, process them through a job queue, cache safe repeated work, enforce rate limits and retries, and store immutable review packets in an audit database.
