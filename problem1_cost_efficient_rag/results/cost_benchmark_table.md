# Cost comparison assumptions

- 384-dimensional float32 vectors (1,536 bytes) plus 512 bytes average metadata/index allowance per vector.
- 50,000 queries/month; the embedded price includes a $25 shared application VM, $0.08/GB-month disk, and $0.023/GB-month backup.
- Managed prices are deliberately illustrative planning assumptions for an always-on managed vector service, not a vendor quote; pricing, replicas, throughput and region can change the outcome.
- Embedding/generation API spend is excluded because it is comparable across stores.

| Vectors | Estimated disk | Embedded SQLite deployment | Illustrative managed DB | Savings |
|---:|---:|---:|---:|---:|
| 100,000 | 0.19 GB | $25.02/mo | $70.00/mo | 64.3% |
| 1,000,000 | 1.91 GB | $25.20/mo | $280.00/mo | 91.0% |
| 10,000,000 | 19.07 GB | $26.96/mo | $1200.00/mo | 97.8% |
