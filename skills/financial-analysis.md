---
name: financial-analysis
description: Run a deep financial review analyzing income streams, burn rate, runway, and revenue projections with optimization recommendations
---

# Financial Analysis Protocol

Use this skill for weekly financial reviews or whenever a financial decision requires data-backed analysis.

## Step 1: Load Financial State

Read `context/financial-snapshot.md` and extract:
- Current total monthly income (all streams)
- Current monthly burn rate
- Cash reserves / runway
- Progress toward quarterly milestones

## Step 2: Income Stream Analysis

Break down revenue by source and calculate contribution:

```
Stream Contribution = (Stream Monthly Revenue / Total Monthly Revenue) x 100

| Stream          | Monthly £ | % of Total | Trend (3mo) | Risk Level |
|-----------------|-----------|------------|-------------|------------|
| Salary          | £XXk      | XX%        | Stable/+/-  | Low/Med/Hi |
| Consulting      | £XXk      | XX%        | Stable/+/-  | Low/Med/Hi |
| Teaching        | £XXk      | XX%        | Stable/+/-  | Low/Med/Hi |
| Content/Digital | £XXk      | XX%        | Stable/+/-  | Low/Med/Hi |
```

Flag any stream contributing >60% of total (concentration risk).

## Step 3: Burn Rate Calculation

```
Monthly Burn Rate = Fixed Costs + Variable Costs + Discretionary

Fixed Costs:
  - Housing: £XX
  - Utilities: £XX
  - Subscriptions/Tools: £XX
  - Insurance: £XX

Variable Costs:
  - Food: £XX
  - Transport: £XX
  - Health: £XX

Discretionary:
  - Learning/Courses: £XX
  - Equipment: £XX
  - Entertainment: £XX

TOTAL MONTHLY BURN: £XX
```

## Step 4: Runway Calculation

```
Runway (months) = Cash Reserves / (Monthly Burn Rate - Monthly Income)

If income > burn:
  Surplus = Monthly Income - Monthly Burn Rate
  Annual Savings Rate = (Surplus x 12) / (Annual Income) x 100

If burn > income:
  Runway = Cash Reserves / (Monthly Burn Rate - Monthly Income)
  ALERT: [X] months until reserves depleted
```

## Step 5: Revenue Growth Tracking

Calculate month-over-month and quarter-over-quarter growth:

```
MoM Growth = ((This Month Revenue - Last Month Revenue) / Last Month Revenue) x 100
QoQ Growth = ((This Quarter Revenue - Last Quarter Revenue) / Last Quarter Revenue) x 100

Required Monthly Growth to Hit £250K Annual:
  Monthly Target = £250,000 / 12 = £20,833
  Current Gap = £20,833 - Current Monthly Revenue
  Required MoM Growth = (Gap / Remaining Months) per month
```

## Step 6: Revenue Projection Scenarios

Model three scenarios for the next 6 months:

**Conservative (current trajectory, no new streams)**
```
Month [N+1]: £XX (current + organic growth at X%)
Month [N+3]: £XX
Month [N+6]: £XX
Annual projection: £XXk
```

**Moderate (one new client or stream added)**
```
Month [N+1]: £XX
Month [N+3]: £XX
Month [N+6]: £XX
Annual projection: £XXk
```

**Aggressive (two new streams, rate increases, content monetization)**
```
Month [N+1]: £XX
Month [N+3]: £XX
Month [N+6]: £XX
Annual projection: £XXk
```

## Step 7: Optimization Recommendations

Evaluate and rank opportunities:

1. **Rate optimization**: Can any existing stream increase rates? What is the market rate?
2. **Stream diversification**: Which new revenue streams have highest ROI for time invested?
3. **Cost reduction**: Any subscriptions or costs that can be cut without impact?
4. **Leverage plays**: What existing assets (content, courses, tools) can generate passive income?
5. **Time reallocation**: Which hours currently spent on low-ROI activities could shift to higher-ROI work?

## Output Template

```
## Financial Review — [DATE]

### Summary
- Monthly Income: £XX,XXX
- Monthly Burn: £XX,XXX
- Net Position: +/- £XX,XXX
- Runway: XX months (or N/A if surplus)
- £250K Progress: XX% on track

### Key Metrics
- MoM Revenue Growth: X%
- Savings Rate: X%
- Concentration Risk: [Stream] at X%

### Top 3 Recommendations
1. [ACTION] → Expected impact: £XX/month → Effort: Low/Med/High
2. [ACTION] → Expected impact: £XX/month → Effort: Low/Med/High
3. [ACTION] → Expected impact: £XX/month → Effort: Low/Med/High

### Next Review: [DATE]
```
