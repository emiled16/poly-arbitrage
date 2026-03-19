# poly-arbitrage

Initial local-first workspace for Polymarket market ingestion and downstream ELT.

## Current slice

- dispatcher-based raw ingestion contracts
- raw Polymarket Gamma and CLOB connectors
- separate ELT normalization layer for source-to-canonical transforms

## Quickstart

```bash
PYTHONPATH=src python3 scripts/ingest_polymarket.py --source polymarket_gamma --dataset markets --limit 3
```
