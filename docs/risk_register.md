# Risk register

| # | Risk | Likelihood | Impact | Mitigation | Trigger |
|---|---|---|---|---|---|
| R1 | API list price rises or the Flash-Lite tier is retired | Medium | Medium | Provider-agnostic tagger; benchmarked open-model fallback; workbook shows the new break-even in one edit | Price notice from Google |
| R2 | Real token use is above the 4 chars/token estimate | Medium | Low | Log `usage_metadata` on every call; replace A1 | Measured cost > 1.5x estimate |
| R3 | Open-model quality is below ReviewPulse v3 | Medium | Medium | Bench measures F1 on the same test set before any switch | Bench F1 < 0.878 |
| R4 | Spot VM pre-emption delays digests | High (if spot) | Medium | Use on-demand for anything owner-facing; spot only for batch back-fills | Any missed Monday digest |
| R5 | Owners' willingness to pay is below cost of acquisition | Medium | High | Van Westendorp before pricing; kill rule at INR 150 | Optimal price point < INR 150 |
| R6 | WhatsApp rates change (they did on 1 Oct 2026) | Medium | Low | Rate is one input cell; digest count per tier is adjustable | Meta rate-card update |
| R7 | Hosting share and gateway fee, not AI, dominate COGS | Known | Low | Yearly billing to cut per-transaction fees; shared hosting | Either > 50% of COGS |
