# Motor and Fire Claims Performance Analysis

**Investigating insurance profitability, claims severity, and pricing strategies in Malawi (2023–2026)**

## Project Overview

This project examines the financial and operational performance of a simulated short-term insurance portfolio in Malawi from January 2023 to September 2026. It investigates why motor insurance loss ratios deteriorated following the November 2023 kwacha devaluation, whether subsequent premium increases improved underwriting performance, and what additional pricing adjustments may be required for 2027.

The analysis combines insurance performance indicators, claims-level data, macroeconomic trends, and statistical testing to generate actionable recommendations for pricing, claims management, customer retention, and operational efficiency.

**Important:** All policy and claims records are simulated. Publicly reported macroeconomic indicators informed the assumptions, but the insurance results do not represent any actual insurance company.

## Business Problem

Currency depreciation and inflation can increase the cost of imported vehicle parts, repairs, and other claims-related expenses. When insurance premiums do not adjust quickly enough, claims costs can grow faster than earned premiums, putting pressure on underwriting profitability.

This project addresses five key business questions:

1. How did the November 2023 devaluation relate to changes in motor insurance loss ratios?
2. Were worsening loss ratios driven primarily by claims frequency or claims severity?
3. Did premium growth keep pace with inflation?
4. Which branches and insurance products require management intervention?
5. What additional premium adjustments could help motor insurance achieve a 60% target loss ratio in 2027?

## Objectives

- Evaluate loss ratios, expense ratios, and combined ratios across insurance products.
- Analyse claims frequency, average claim severity, and premium growth.
- Compare insurance premium growth against inflation.
- Assess branch-level differences in claims settlement times.
- Investigate policy lapse trends following premium increases.
- Apply statistical tests and regression analysis to examine patterns in the simulated data.
- Develop evidence-based recommendations for pricing, claims cost control, and customer retention.

## Dataset Description

The analysis covers 45 months, from January 2023 to September 2026, across four branches and four insurance products.

| Dataset | Records | Description |
|---|---:|---|
| `monthly_performance.csv` | 720 | Monthly policy counts, earned premiums, claims, commissions, and management expenses by branch and product |
| `claims.csv` | 9,938 | Claim-level records covering claim amounts, causes, reporting channels, reporting delays, settlement times, and unusual-claim flags |
| `macro_indicators.csv` | 45 | Monthly inflation, official MWK/USD exchange rates, and policy rates |

**Insurance products:** Motor Private, Motor Commercial, Fire & Property, and Personal Accident.

**Branches:** Blantyre, Lilongwe, Mzuzu, and Zomba.

## Key Findings

### 1. Motor insurance profitability deteriorated after 2023

The combined motor loss ratio increased from 57.7% in 2023 to 82.8% in 2024. It subsequently declined to 74.5% in 2025 and 63.2% for January–September 2026.

This pattern illustrates the potential impact of rising claims costs and delayed premium adjustments on insurance profitability.

### 2. Claims severity was a major driver

Average motor private claim size increased from approximately MWK 1.40 million in 2023 to MWK 3.29 million in 2026, an increase of approximately 135%.

The analysis suggests that the deterioration in motor loss ratios was associated more strongly with rising claim severity than with changes in claims frequency.

### 3. Premium growth initially lagged behind inflation

Real premium growth was estimated at -5.4% in 2024, followed by +3.9% in 2025 and +4.3% for January–September 2026.

The results demonstrate why insurers need to monitor premium adequacy alongside inflation and claims cost trends.

### 4. Commercial motor in Lilongwe requires attention

Lilongwe Commercial Motor recorded a 77.0% loss ratio over the 12 months ending September 2026, making it a priority for targeted pricing and claims cost reviews.

### 5. Customer retention is a concern

The annual lapse rate for Motor Private increased from 23.2% in 2023 to 29.6% in 2026. This highlights the importance of balancing premium adjustments with customer retention strategies.

### 6. Claims settlement performance varies by branch

Median settlement times for settled claims were:

- **Blantyre:** 22 days
- **Lilongwe:** 23 days
- **Mzuzu:** 31 days
- **Zomba:** 35 days

The differences suggest opportunities to improve claims processing and operational efficiency in the smaller branches.

### 7. Fire insurance results require cautious interpretation

Fire & Property recorded a 35.9% loss ratio in January–September 2026. However, relatively few claims make the results sensitive to individual large losses. Pricing decisions should therefore consider a longer observation period rather than relying on a single year's results.

## Statistical Analysis

The project applies statistical techniques to investigate patterns in the simulated portfolio.

| Business question | Method | Reported result |
|---|---|---|
| Did motor loss ratios change after the devaluation? | Welch's two-sample t-test | Average monthly loss ratio increased from 52.8% to 82.6%; p < 0.001 |
| Did claim cost growth relate to inflation and the devaluation period? | Regression analysis | R² = 0.80; devaluation-period coefficient statistically significant at p < 0.001 |
| Did settlement times differ across branches? | One-way ANOVA on log settlement days | F = 292; p < 0.001 |

These tests demonstrate how inferential statistics can complement descriptive analytics and business reporting.

Because the dataset is simulated, the results demonstrate the analytical methodology rather than establish causal findings about a real insurer.

## 2027 Pricing Scenario Analysis

Under the project's base-case inflation assumption of 22%, the estimated additional rate increases required to reach a 60% loss ratio, beyond automatic premium adjustments from sum-insured revaluation, are:

| Insurance product | Estimated additional rate adjustment |
|---|---:|
| Motor Private | 15.1% |
| Motor Commercial | 24.6% |
| Fire & Property | No additional increase indicated by this scenario |
| Personal Accident | No additional increase indicated by this scenario |

These are illustrative scenario estimates based on simulated portfolio assumptions, not actual pricing recommendations for a real insurer.

## Business Recommendations

1. **Review motor pricing:** Model phased increases for private and commercial motor, prioritising underperforming segments such as Lilongwe Commercial Motor.
2. **Control claims severity:** Review garage agreements, repair costs, spare-parts pricing, and repair network performance.
3. **Improve customer retention:** Monitor policy lapses monthly, communicate upcoming premium changes early, and assess flexible payment options.
4. **Improve claims turnaround:** Investigate settlement delays in Zomba and Mzuzu and assess additional staffing or digital claims intake.
5. **Strengthen claims oversight:** Review unusual-claim flags through a documented referral process. A flag is an indicator for investigation, not proof of fraud.
6. **Monitor fire insurance over a longer period:** Avoid making major pricing decisions from a small number of claims.
7. **Develop a monthly KPI report:** Track loss ratios, combined ratios, claims severity, lapse rates, and settlement times to support management decisions.

## Tools and Analytical Techniques

The project demonstrates insurance performance analysis, data interpretation, and statistical reasoning.

- **Data analysis:** Python and pandas
- **Statistical analysis:** Hypothesis testing, regression, and ANOVA
- **Business intelligence:** Insurance KPI monitoring and performance reporting
- **Data visualisation:** Trends in loss ratios, inflation, claims costs, and settlement performance
- **Business analysis:** Pricing scenarios, operational recommendations, and customer retention analysis

## Project Structure

```text
motor-fire-claims-performance-analysis/
├── data/
│   ├── monthly_performance.csv
│   ├── claims.csv
│   └── macro_indicators.csv
├── outputs/
│   └── charts
├── motor_and_fire_claims_performance_report.pdf
├── README.md
└── motor_fire_claims_performance_analysis.py
```

## Limitations

- The policy and claims datasets are simulated; they do not represent a real insurance company's experience.
- The relationship between devaluation, premium changes, and customer lapses is partly embedded in the simulation assumptions.
- Recent claims may develop further, changing the latest loss ratios.
- The analysis does not include reinsurance effects, and the expense ratio relies on an assumption.
- Results for products or branches with few claims are less stable.
- The regression uses a limited monthly time series and cannot fully isolate inflation from the effects of devaluation.

## Conclusion

This project demonstrates how insurance data, macroeconomic indicators, and statistical methods can be combined to investigate underwriting performance and inform business decisions.

The analysis highlights the importance of monitoring claims severity, maintaining adequate pricing, managing customer retention, and improving settlement efficiency. It also demonstrates how data analytics can turn insurance performance records into practical recommendations for management.

**Disclaimer:** This is an independent portfolio project using simulated insurance data for educational and analytical purposes. It is not financial, actuarial, or pricing advice for any actual insurer.
