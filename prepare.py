"""
Build the Tableau data source for the delivery and seller performance dashboard.
Reuses the SQLite database from the MarketplaceUnitEconomics project (olist.db).
Run:  python prepare.py     (needs pandas and matplotlib)
Output: data/state performance.csv, data/seller scorecard.csv, data/monthly delivery.csv, charts/preview.png
"""
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).parent
con = sqlite3.connect(ROOT / "olist.db")

base = """
WITH o AS (
  SELECT o.order_id, c.customer_state AS state, o.order_purchase_timestamp AS ts,
         JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp) AS days,
         DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date) AS late
  FROM orders o JOIN customers c ON c.customer_id = o.customer_id
  WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
),
v AS (SELECT order_id, SUM(price) AS gmv, SUM(freight_value) AS freight FROM items GROUP BY order_id),
r AS (SELECT order_id, AVG(review_score) AS score FROM reviews GROUP BY order_id)
"""
state = pd.read_sql_query(base + """
SELECT state AS "state", COUNT(*) AS "orders", ROUND(SUM(gmv), 0) AS "gmv brl",
       ROUND(AVG(days), 1) AS "avg delivery days", ROUND(AVG(late), 4) AS "late rate",
       ROUND(AVG(score), 2) AS "avg review", ROUND(SUM(freight) / SUM(gmv), 4) AS "freight share of price"
FROM o JOIN v USING (order_id) LEFT JOIN r USING (order_id)
GROUP BY state ORDER BY 2 DESC""", con)

monthly = pd.read_sql_query(base + """
SELECT SUBSTR(ts, 1, 7) AS "month", COUNT(*) AS "orders", ROUND(AVG(days), 1) AS "avg delivery days",
       ROUND(AVG(late), 4) AS "late rate", ROUND(AVG(score), 2) AS "avg review"
FROM o LEFT JOIN r USING (order_id)
WHERE ts BETWEEN '2017-01-01' AND '2018-08-31'
GROUP BY 1 ORDER BY 1""", con)

seller = pd.read_sql_query("""
WITH x AS (
  SELECT i.seller_id, i.order_id, SUM(i.price) AS gmv,
         MAX(DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date)) AS late,
         MAX(JULIANDAY(o.order_delivered_carrier_date) - JULIANDAY(o.order_approved_at)) AS handover
  FROM items i JOIN orders o ON o.order_id = i.order_id
  WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
  GROUP BY i.seller_id, i.order_id
),
r AS (SELECT order_id, AVG(review_score) AS score FROM reviews GROUP BY order_id)
SELECT s.seller_state AS "seller state", COUNT(*) AS "orders", ROUND(SUM(gmv), 0) AS "gmv brl",
       ROUND(AVG(late), 4) AS "late rate", ROUND(AVG(handover), 1) AS "avg days to hand to carrier",
       ROUND(AVG(score), 2) AS "avg review"
FROM x JOIN sellers s ON s.seller_id = x.seller_id LEFT JOIN r USING (order_id)
GROUP BY x.seller_id HAVING COUNT(*) >= 50 ORDER BY 3 DESC""", con)
con.close()

# Anonymous seller number instead of the long hash id
seller.insert(0, "seller", [f"Seller {i + 1}" for i in range(len(seller))])
seller["tier"] = pd.cut(seller["late rate"], [-1, 0.05, 0.10, 1], labels=["On time (under 5 pct late)", "Watch (5 to 10 pct)", "Problem (over 10 pct)"])

(ROOT / "data").mkdir(exist_ok=True)
state.to_csv(ROOT / "data" / "state performance.csv", index=False)
monthly.to_csv(ROOT / "data" / "monthly delivery.csv", index=False)
seller.to_csv(ROOT / "data" / "seller scorecard.csv", index=False)

print(state.to_string(index=False))
print(monthly.to_string(index=False))
print(seller["tier"].value_counts())
print(seller.groupby("tier", observed=True)[["orders", "gmv brl"]].sum(), seller.groupby("tier", observed=True)["avg review"].mean())
print("sellers:", len(seller))

# Preview chart (the Tableau dashboard is built from the same files)
fig, ax = plt.subplots(figsize=(7.5, 4.8))
ax.scatter(state["late rate"] * 100, state["avg review"], s=state["orders"] / 60, color="#333333", alpha=0.7)
for _, r in state.iterrows():
    ax.annotate(r["state"], (r["late rate"] * 100, r["avg review"]), fontsize=8, xytext=(4, 2), textcoords="offset points")
ax.set_xlabel("Late deliveries (pct of orders)"); ax.set_ylabel("Average review score")
ax.set_title("States with more late deliveries get lower reviews (bubble size = orders)")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout(); plt.savefig(ROOT / "charts" / "preview.png", dpi=110); plt.close()
