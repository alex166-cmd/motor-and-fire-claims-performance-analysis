"""
MOTOR AND FIRE CLAIMS PERFORMANCE
Input  : data/monthly_performance.csv, data/claims.csv, data/macro_indicators.csv
Output : outputs/results.json, outputs/kpi_tables.xlsx, outputs/charts/title.png

"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"          
OUT = HERE / "outputs"
CH = OUT / "charts"
CH.mkdir(parents=True, exist_ok=True)

TARGET_LR = 60.0  # target loss ratio, %
PRODUCTS = ["Motor Private", "Motor Commercial", "Fire & Property", "Personal Accident"]
COL = {"Motor Private": "#1f4e79", "Motor Commercial": "#d97706", "Fire & Property": "#2e7d32", "Personal Accident": "#7b6aa6"}

plt.rcParams.update({
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 11, "figure.dpi": 100, "savefig.dpi": 160,
    "axes.grid": True, "grid.alpha": 0.25,
})

m = pd.read_csv(DATA / "monthly_performance.csv")
c = pd.read_csv(DATA / "claims.csv", parse_dates=["loss_date"])
macro = pd.read_csv(DATA / "macro_indicators.csv")

m["date"] = pd.PeriodIndex(m["month"], freq="M").to_timestamp()
m["year"] = m["date"].dt.year
m["quarter"] = m["date"].dt.to_period("Q").astype(str)
m["expenses_mwk"] = m["commission_mwk"] + m["management_expenses_mwk"]
m["policy_months"] = m["policies_in_force"]  # one policy-month per policy in force each month

R = {}  # results for the report


# Data checks and cleaning
_chk = c.groupby(["loss_month", "branch", "product"]).agg(n=("claim_id", "count"), amt=("claim_amount_mwk", "sum")).reset_index()
_chk = m.merge(_chk, left_on=["month", "branch", "product"], right_on=["loss_month", "branch", "product"], how="left").fillna({"n": 0, "amt": 0})
R["checks"] = {
    "monthly_rows": int(len(m)),
    "claim_rows": int(len(c)),
    "duplicate_claim_ids": int(c["claim_id"].duplicated().sum()),
    "missing_values_monthly": int(m.isna().sum().sum()),
    "missing_values_claims": int(c.isna().sum().sum()),
    "negative_amounts": int((c["claim_amount_mwk"] <= 0).sum()),
    "claim_count_mismatches": int((_chk["n"] != _chk["claim_count"]).sum()),
    "claim_amount_mismatches": int((abs(_chk["amt"] - _chk["claims_incurred_mwk"]) > 1).sum()),
    "claims_total_mwk_bn": round(float(c["claim_amount_mwk"].sum() / 1e9), 2),
    "premium_total_mwk_bn": round(float(m["earned_premium_mwk"].sum() / 1e9), 2),
}


def ratios(df):
    ep = df["earned_premium_mwk"].sum()
    cl = df["claims_incurred_mwk"].sum()
    ex = df["expenses_mwk"].sum()
    n = df["claim_count"].sum()
    pm = df["policy_months"].sum()
    return pd.Series({
        "earned_premium_mwk_m": ep / 1e6,
        "claims_incurred_mwk_m": cl / 1e6,
        "loss_ratio_pct": cl / ep * 100,
        "expense_ratio_pct": ex / ep * 100,
        "combined_ratio_pct": (cl + ex) / ep * 100,
        "claim_count": n,
        "claim_frequency_pct": n / (pm / 12) * 100,  # claims per 100 policy-years
        "avg_claim_mwk": cl / n if n else np.nan,
        "avg_premium_mwk": ep / (pm / 12),  # per policy-year
    })


# Headline KPIs by year (2026 = Jan-Sep)
kpi_year = m.groupby("year").apply(ratios, include_groups=False).round(1)
pif_end = m[m["month"].isin(["2023-12", "2024-12", "2025-12", "2026-09"])].groupby("year")["policies_in_force"].sum()
kpi_year["policies_in_force_end"] = pif_end.values
R["kpi_year"] = kpi_year.reset_index().to_dict("records")

kpi_prod_year = m.groupby(["product", "year"]).apply(ratios, include_groups=False).round(1).reset_index()
R["kpi_prod_year"] = kpi_prod_year.to_dict("records")
lr_py = kpi_prod_year.pivot(index="product", columns="year", values="loss_ratio_pct").reindex(PRODUCTS)
cr_py = kpi_prod_year.pivot(index="product", columns="year", values="combined_ratio_pct").reindex(PRODUCTS)

# Same nine months of each year (Jan-Sep) so years are comparable
m9 = m[m["date"].dt.month <= 9]
ytd = m9.groupby("year").apply(ratios, include_groups=False).round(1)
R["ytd_jan_sep"] = ytd.reset_index().to_dict("records")


# 2. Premium growth against inflation (real growth)
ep_ytd = m9.groupby("year")["earned_premium_mwk"].sum()
_mac = macro.assign(year=macro["month"].str[:4].astype(int), mon=macro["month"].str[5:7].astype(int))
infl_avg_ytd = _mac[_mac["mon"] <= 9].groupby("year")["inflation_yoy_pct"].mean()
growth = pd.DataFrame({
    "earned_premium_mwk_m": ep_ytd / 1e6,
    "nominal_growth_pct": ep_ytd.pct_change() * 100,
    "avg_inflation_pct": infl_avg_ytd,
})
growth["real_growth_pct"] = ((1 + growth["nominal_growth_pct"] / 100) / (1 + growth["avg_inflation_pct"] / 100) - 1) * 100
growth = growth.round(1)
R["premium_growth"] = growth.reset_index().to_dict("records")

# Frequency vs severity vs premium
#    LR = frequency x average claim / average premium  (all per policy-year)
def decompose(df, y0, y1):
    a = ratios(df[df["year"] == y0])
    b = ratios(df[df["year"] == y1])
    f = np.log(b["claim_frequency_pct"] / a["claim_frequency_pct"])
    s = np.log(b["avg_claim_mwk"] / a["avg_claim_mwk"])
    p = -np.log(b["avg_premium_mwk"] / a["avg_premium_mwk"])
    tot = np.log(b["loss_ratio_pct"] / a["loss_ratio_pct"])
    return {"from": y0, "to": y1, "lr_from": round(a["loss_ratio_pct"], 1), "lr_to": round(b["loss_ratio_pct"], 1),
            "frequency_effect": round(f * 100, 1), "severity_effect": round(s * 100, 1),
            "premium_effect": round(p * 100, 1), "total_log_change": round(tot * 100, 1)}


motor = m[m["product"].isin(["Motor Private", "Motor Commercial"])]
R["decomposition_motor"] = [decompose(motor, 2023, 2024), decompose(motor, 2024, 2025)]
# 2025 Jan-Sep vs 2026 Jan-Sep so that the two periods match
motor9 = motor[motor["date"].dt.month <= 9]
R["decomposition_motor"].append(decompose(motor9, 2025, 2026))


# Last 12 months by branch and product
l12 = m[m["date"] >= "2025-10-01"]
bp = l12.groupby(["branch", "product"]).apply(ratios, include_groups=False).reset_index()
heat = bp.pivot(index="branch", columns="product", values="loss_ratio_pct")[PRODUCTS].round(1)
cnt = bp.pivot(index="branch", columns="product", values="claim_count")[PRODUCTS]
R["heat_lr_last12"] = heat.reset_index().to_dict("records")
R["heat_claims_last12"] = cnt.reset_index().to_dict("records")
hot = bp[(bp["loss_ratio_pct"] > 70)].sort_values("loss_ratio_pct", ascending=False)
R["hotspots"] = hot[["branch", "product", "loss_ratio_pct", "claim_count", "earned_premium_mwk_m"]].round(1).to_dict("records")

br = l12.groupby("branch").apply(ratios, include_groups=False).round(1).reset_index()
R["branch_last12"] = br.to_dict("records")


# Statistical tests
# Did the motor loss ratio change after the devaluation? (Welch t-test on monthly LR)
mm = motor.groupby("date")[["earned_premium_mwk", "claims_incurred_mwk"]].sum()
mm["lr"] = mm["claims_incurred_mwk"] / mm["earned_premium_mwk"] * 100
pre = mm.loc["2023-01-01":"2023-10-01", "lr"]
post = mm.loc["2023-12-01":"2024-11-01", "lr"]
t, p = stats.ttest_ind(post, pre, equal_var=False)
R["ttest_devaluation"] = {"pre_months": len(pre), "post_months": len(post), "pre_mean_lr": round(pre.mean(), 1),
                          "post_mean_lr": round(post.mean(), 1), "t": round(float(t), 2), "p_value": float(p)}

# Do claim costs follow inflation? OLS on year-on-year growth in average motor claim
mon = motor.groupby("date")[["claims_incurred_mwk", "claim_count"]].sum()
mon["avg_claim"] = mon["claims_incurred_mwk"] / mon["claim_count"]
mon["yoy_claim_growth"] = mon["avg_claim"].pct_change(12) * 100
mac = macro.copy()
mac["date"] = pd.to_datetime(mac["month"] + "-01")
mon = mon.join(mac.set_index("date")["inflation_yoy_pct"])
mon["post_deval_base"] = ((mon.index >= "2023-12-01") & (mon.index <= "2024-11-01")).astype(int)
d = mon.dropna(subset=["yoy_claim_growth"]).copy()
X = np.column_stack([np.ones(len(d)), d["inflation_yoy_pct"].values, d["post_deval_base"].values])
y = d["yoy_claim_growth"].values
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
resid = y - X @ beta
dof = len(y) - X.shape[1]
sigma2 = resid @ resid / dof
cov = sigma2 * np.linalg.inv(X.T @ X)
se = np.sqrt(np.diag(cov))
tvals = beta / se
pvals = 2 * (1 - stats.t.cdf(np.abs(tvals), dof))
r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
R["ols_claim_cost"] = {
    "n": int(len(y)), "r2": round(float(r2), 2),
    "coef": {"intercept": round(float(beta[0]), 2), "inflation": round(float(beta[1]), 2), "post_devaluation_period": round(float(beta[2]), 2)},
    "se": {"intercept": round(float(se[0]), 2), "inflation": round(float(se[1]), 2), "post_devaluation_period": round(float(se[2]), 2)},
    "p": {"intercept": float(pvals[0]), "inflation": float(pvals[1]), "post_devaluation_period": float(pvals[2])},
}

# Settlement time by branch (settled claims only), one-way ANOVA on log days
sc = c[c["status"] == "Settled"].copy()
settle = sc.groupby("branch")["settlement_days"].agg(["count", "median", "mean"]).round(1)
groups = [np.log(g["settlement_days"].values) for _, g in sc.groupby("branch")]
F, pF = stats.f_oneway(*groups)
R["settlement_by_branch"] = settle.reset_index().to_dict("records")
R["anova_settlement"] = {"F": round(float(F), 1), "p_value": float(pF), "n_settled": int(len(sc))}
over30 = (sc["settlement_days"] + sc["report_lag_days"] > 30).groupby(sc["branch"]).mean().mul(100).round(1)
R["share_over_30_days"] = over30.to_dict()
R["open_claims"] = {"count": int((c["status"] == "Open").sum()),
                    "amount_mwk_m": round(float(c.loc[c["status"] == "Open", "claim_amount_mwk"].sum() / 1e6), 1)}

# Large claims and fraud flags
q99 = c.groupby("product")["claim_amount_mwk"].transform(lambda s: s.quantile(0.90))
c["top10pct"] = c["claim_amount_mwk"] >= q99
conc = c.groupby("product").apply(lambda g: g.loc[g["top10pct"], "claim_amount_mwk"].sum() / g["claim_amount_mwk"].sum() * 100, include_groups=False).round(1)
R["top10pct_share_of_cost"] = conc.reindex(PRODUCTS).to_dict()
fr = c.groupby("product").agg(flag_rate=("fraud_flag", "mean"), flagged_cost=("claim_amount_mwk", lambda s: 0)).reset_index()
fr["flagged_cost_mwk_m"] = [c.loc[(c["product"] == pr) & (c["fraud_flag"] == 1), "claim_amount_mwk"].sum() / 1e6 for pr in fr["product"]]
fr["flag_rate"] = (fr["flag_rate"] * 100).round(1)
R["fraud_flags"] = fr[["product", "flag_rate", "flagged_cost_mwk_m"]].round(1).to_dict("records")
R["fraud_total_cost_mwk_m"] = round(float(c.loc[c["fraud_flag"] == 1, "claim_amount_mwk"].sum() / 1e6), 1)

# Reporting channel mix for last 12 months
ch = c[c["loss_date"] >= "2025-10-01"]["reporting_channel"].value_counts(normalize=True).mul(100).round(1)
R["channel_mix_last12"] = ch.to_dict()


# Retention (policy lapse) after price increases
# simple, transparent version: annualised lapse = (lapsed in period / average in force) x (12 / months in period)
def annual_lapse(df):
    months = df["month"].nunique()
    avg_pif = df.groupby("month")["policies_in_force"].sum().mean()
    return df["lapsed_policies"].sum() / avg_pif * (12 / months) * 100

lap = {}
for pr in PRODUCTS:
    sub = m[m["product"] == pr]
    lap[pr] = {str(y): round(annual_lapse(sub[(sub["year"] == y) & (sub["date"].dt.month <= 9)]), 1) for y in [2023, 2024, 2025, 2026]}
R["lapse_rate_jan_sep"] = lap


# 2027 rate need under three inflation scenarios
PASS = {"Motor Private": 0.80, "Motor Commercial": 0.80, "Fire & Property": 0.65, "Personal Accident": 0.60}
PREM_DRIFT = 0.35
scen = {"Low (inflation 18%)": 0.18, "Base (inflation 22%)": 0.22, "High (IMF view, 25%)": 0.25}
base12 = l12.groupby("product").apply(ratios, include_groups=False).reindex(PRODUCTS)
rate_rows = []
for pr in PRODUCTS:
    for sname, inf in scen.items():
        cost_next = base12.loc[pr, "avg_claim_mwk"] * (1 + PASS[pr] * inf)
        freq = base12.loc[pr, "claim_frequency_pct"] / 100
        exp_claim_cost = cost_next * freq
        needed_prem = exp_claim_cost / (TARGET_LR / 100)
        drift_prem = base12.loc[pr, "avg_premium_mwk"] * (1 + PREM_DRIFT * inf)
        rate_rows.append({
            "product": pr, "scenario": sname,
            "current_lr_pct": round(base12.loc[pr, "loss_ratio_pct"], 1),
            "needed_premium_mwk": round(needed_prem),
            "premium_with_drift_mwk": round(drift_prem),
            "extra_rate_needed_pct": round((needed_prem / drift_prem - 1) * 100, 1),
        })
rate_tbl = pd.DataFrame(rate_rows)
R["rate_need_2027"] = rate_tbl.to_dict("records")


# Charts
def save(fig, name):
    fig.tight_layout()
    fig.savefig(CH / name, bbox_inches="tight")
    plt.close(fig)


# Chart 1: premium growth vs inflation (monthly, rolling 12m earned premium growth)
ep_m = m.groupby("date")["earned_premium_mwk"].sum()
ep_yoy = ep_m.rolling(3).sum().pct_change(12) * 100
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(ep_yoy.index, ep_yoy.values, color="#1f4e79", lw=2, label="Earned premium growth (3-month, year on year)")
ax.plot(mac["date"], mac["inflation_yoy_pct"], color="#d97706", lw=2, ls="--", label="Inflation (year on year)")
ax.axvline(pd.Timestamp("2023-11-09"), color="grey", lw=1)
ax.text(pd.Timestamp("2023-11-20"), ax.get_ylim()[1] * 0.93, "Kwacha devalued\nNov 2023", fontsize=8, color="grey", va="top")
ax.set_ylabel("%")
ax.set_title("Premium growth fell behind inflation in 2024, then caught up")
ax.legend(loc="lower left", fontsize=8, frameon=False)
save(fig, "01_premium_growth_vs_inflation.png")

# Chart 2: quarterly loss ratio by product
q = m.groupby(["quarter", "product"])[["earned_premium_mwk", "claims_incurred_mwk"]].sum()
q["lr"] = q["claims_incurred_mwk"] / q["earned_premium_mwk"] * 100
qp = q["lr"].unstack()[PRODUCTS]
fig, ax = plt.subplots(figsize=(8.5, 4.2))
for pr in PRODUCTS:
    ax.plot(range(len(qp)), qp[pr].values, color=COL[pr], lw=2, label=pr, marker="o", ms=3)
ax.axhline(TARGET_LR, color="black", lw=1, ls=":")
ax.text(-0.4, TARGET_LR + 1.5, "Target 60%", ha="left", fontsize=8)
ax.set_xticks(range(len(qp)))
ax.set_xticklabels([s.replace("20", "'", 1) for s in qp.index], rotation=45, fontsize=8)
ax.set_ylabel("Loss ratio (%)")
ax.set_title("Motor loss ratios peaked in 2024 and are now back near target")
ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper right")
save(fig, "02_quarterly_loss_ratio_by_product.png")

# Chart 3: drivers (frequency vs average claim vs average premium), motor, indexed Jan-Mar 2023 = 100
mq = motor.groupby("quarter").apply(ratios, include_groups=False)
idx = pd.DataFrame({
    "Claims per 100 policies": mq["claim_frequency_pct"] / mq["claim_frequency_pct"].iloc[0] * 100,
    "Average claim cost": mq["avg_claim_mwk"] / mq["avg_claim_mwk"].iloc[0] * 100,
    "Average premium": mq["avg_premium_mwk"] / mq["avg_premium_mwk"].iloc[0] * 100,
})
fig, ax = plt.subplots(figsize=(8.5, 4.2))
cols = ["#7b6aa6", "#d97706", "#1f4e79"]
for cn, cc in zip(idx.columns, cols):
    ax.plot(range(len(idx)), idx[cn].values, label=cn, color=cc, lw=2)
ax.set_xticks(range(len(idx)))
ax.set_xticklabels([s.replace("20", "'", 1) for s in idx.index], rotation=45, fontsize=8)
ax.set_ylabel("Index (Q1 2023 = 100)")
ax.set_title("Motor: claim cost per claim drove the problem, not claim numbers")
ax.legend(frameon=False, fontsize=8)
save(fig, "03_motor_drivers_index.png")

# Chart 4: heatmap of LR by branch and product, last 12 months
fig, ax = plt.subplots(figsize=(7.5, 3.6))
im = ax.imshow(heat.values, cmap="RdYlGn_r", vmin=30, vmax=90, aspect="auto")
ax.set_xticks(range(len(PRODUCTS)))
ax.set_xticklabels(PRODUCTS, fontsize=8)
ax.set_yticks(range(len(heat)))
ax.set_yticklabels(heat.index)
ax.grid(False)
for i in range(heat.shape[0]):
    for j in range(heat.shape[1]):
        ax.text(j, i, f"{heat.values[i, j]:.0f}%\n({int(cnt.values[i, j])} claims)", ha="center", va="center", fontsize=8)
ax.set_title("Loss ratio by branch and product, Oct 2025 to Sep 2026")
save(fig, "04_heatmap_branch_product.png")

# Chart 5: settlement time by branch (settled claims)
fig, ax = plt.subplots(figsize=(7, 4))
order = ["Blantyre", "Lilongwe", "Mzuzu", "Zomba"]
data_box = [sc.loc[sc["branch"] == b, "settlement_days"].values for b in order]
bp_ = ax.boxplot(data_box, tick_labels=order, showfliers=False, patch_artist=True, medianprops=dict(color="black"))
for patch in bp_["boxes"]:
    patch.set_facecolor("#9db8d2")
ax.axhline(30, color="#d97706", ls="--", lw=1)
ax.text(4.45, 31, "30 days", fontsize=8, color="#d97706", ha="right")
ax.set_ylabel("Days from report to settlement")
ax.set_title("Zomba and Mzuzu settle claims more slowly")
save(fig, "05_settlement_days_by_branch.png")

# Chart 6: rate need 2027
fig, ax = plt.subplots(figsize=(8, 4))
w = 0.26
for k, sname in enumerate(scen):
    vals = [rate_tbl[(rate_tbl["product"] == pr) & (rate_tbl["scenario"] == sname)]["extra_rate_needed_pct"].iloc[0] for pr in PRODUCTS]
    ax.bar(np.arange(len(PRODUCTS)) + (k - 1) * w, vals, w, label=sname, color=["#9db8d2", "#1f4e79", "#d97706"][k])
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(range(len(PRODUCTS)))
ax.set_xticklabels(PRODUCTS, fontsize=8)
ax.set_ylabel("Extra rate increase needed (%)")
ax.set_title("Extra rate needed in 2027 to reach a 60% loss ratio")
ax.legend(frameon=False, fontsize=8)
save(fig, "06_rate_need_2027.png")

# Chart 7: lapse rate after price increases (motor private)
lp = pd.Series(lap["Motor Private"])
fig, ax = plt.subplots(figsize=(6, 3.6))
ax.bar(lp.index, lp.values, color=["#9db8d2", "#1f4e79", "#1f4e79", "#1f4e79"])
for i, v in enumerate(lp.values):
    ax.text(i, v + 0.4, f"{v:.0f}%", ha="center", fontsize=9)
ax.set_ylabel("Annualised lapse rate (%)")
ax.set_title("Motor Private: customers left after the rate increases")
save(fig, "07_motor_private_lapse.png")

# 9. Save tables and results
with pd.ExcelWriter(OUT / "kpi_tables.xlsx") as xw:
    kpi_year.reset_index().to_excel(xw, sheet_name="KPI by year", index=False)
    kpi_prod_year.to_excel(xw, sheet_name="KPI by product and year", index=False)
    growth.reset_index().to_excel(xw, sheet_name="Premium vs inflation", index=False)
    bp.round(1).to_excel(xw, sheet_name="Branch x product 12m", index=False)
    rate_tbl.to_excel(xw, sheet_name="2027 rate need", index=False)
    settle.reset_index().to_excel(xw, sheet_name="Settlement by branch", index=False)
    mm.reset_index().assign(date=lambda d: d["date"].dt.strftime("%Y-%m")).round(1).to_excel(xw, sheet_name="Motor monthly LR", index=False)

with open(OUT / "results.json", "w") as f:
    json.dump(R, f, indent=2, default=float)

# Console summary
pd.set_option("display.width", 200)
print("\nKPI by year\n", kpi_year)
print("\nLoss ratio by product and year\n", lr_py)
print("\nPremium vs inflation (Jan-Sep)\n", growth)
print("\nDecomposition (motor, % points of log change)")
for d_ in R["decomposition_motor"]:
    print(d_)
print("\nHeat map LR last 12m\n", heat)
print("\nClaims count last 12m\n", cnt)
print("\nHotspots >70%\n", hot[["branch", "product", "loss_ratio_pct", "claim_count"]])
print("\nT-test", R["ttest_devaluation"])
print("OLS", R["ols_claim_cost"])
print("ANOVA", R["anova_settlement"], "\n", settle)
print("share >30d", R["share_over_30_days"])
print("open", R["open_claims"])
print("top10 share", R["top10pct_share_of_cost"])
print("fraud", R["fraud_flags"], R["fraud_total_cost_mwk_m"])
print("lapse", lap)
print("channel", R["channel_mix_last12"])
print("\nRate need 2027\n", rate_tbl)
