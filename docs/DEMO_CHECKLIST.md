# Judge-ready demo checklist

1. Open `/api/health`; show that the deterministic safety policy is enabled.
2. Run **20-case safety evaluation**. Target: 20/20 cases and zero unsafe approvals.
3. Upload the 50-bag challan and submit: “55 bags arrived, 5 are wet.”
4. Show provenance, the quantity/condition conflicts, and the deterministic `HOLD_FOR_REVIEW` state.
5. Download the JSON review packet to show the audit record.
6. Disable the network or use an invalid key once; Sakshi must show `PENDING_REVIEW`, not fabricate a recommendation.
7. At 10,000 users, use object storage, a job queue, retries, rate limits, caching, and an audit database.
