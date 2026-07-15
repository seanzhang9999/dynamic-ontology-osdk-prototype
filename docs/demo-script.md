# Demo Script

## 10-minute dual-scenario flow

1. Open Demo Console and show product count, authorization count, job count, and audit event count.
2. Show Product Factory table: two products, purpose-bound output granularity, raw export disabled.
3. Run `企业征信链路`.
4. Explain that the same bank app executes in Grid and Integrated Energy runtimes through the same Product OSDK contract.
5. Inspect jobs and latest receipt: product version, mapping version, input hash, output hash, Ed25519 signature.
6. Run `长春开挖风险`.
7. Show that the result contains risk level, asset types, segment count, recommendations, and quality summary only.
8. Click `坐标升为核心数据`.
9. Show Changchun product version changed and exact coordinate read surface remains absent while the risk action remains available.
10. Close with the proof points: heterogeneous adaptation, data boundary, governance-driven interface, verifiable result.

## API smoke commands

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/demo/run/power-credit \
  -H 'Content-Type: application/json' \
  -d '{"enterprise_id":"91300000DEMO0007"}'
curl -X POST http://127.0.0.1:8000/demo/run/changchun
curl -X POST http://127.0.0.1:8000/demo/recompile-coordinate-core
```

