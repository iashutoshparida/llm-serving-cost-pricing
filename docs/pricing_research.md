# Pricing research plan

Serving cost is not what limits price: COGS is under 13% of the Starter price. So pricing is a willingness-to-pay question, and this plan answers it before any price is set.

## Method: Van Westendorp price sensitivity

Ask 4 questions at the end of each owner interview and pilot exit interview (target n ≥ 30; the 12 discovery interviews give a first read only). Show the product first, then ask about a monthly subscription for one outlet:

1. At what price would this be so cheap you'd doubt it works? (`too_cheap`)
2. At what price would it feel like a bargain? (`cheap`)
3. At what price would it start to feel expensive, but you'd still consider it? (`expensive`)
4. At what price would it be too expensive to consider? (`too_expensive`)

Record answers in `results/wtp_survey_responses.csv`, then run:

```bash
python src/vanwestendorp.py results/wtp_survey_responses.csv
```

This returns the acceptable price range (marginal cheapness to marginal expensiveness) and the optimal price point.

## Hypotheses to test (H1)

| Tier | Hypothesis price | What's in it |
|---|---|---|
| Free | INR 0 | 30 reviews a month, template replies, no WhatsApp |
| Starter | INR 299 / month | 100 reviews, AI replies, weekly WhatsApp digest |
| Pro | INR 799 / month | 300 reviews, daily digest, multi-outlet later |

**Kill rule:** if the optimal price point from the survey is below INR 150, the paid tier does not cover acquisition at the assumed CAC (INR 1,500, payback over 10 months). The model would need to change, for example selling through POS or aggregator partners instead of direct.

## Also ask
- Who pays today for anything similar (POS add-ons, agency, listing boosts)?
- Monthly or yearly? UPI AutoPay or invoice?
