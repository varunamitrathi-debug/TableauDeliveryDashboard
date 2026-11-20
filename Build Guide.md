# Build guide: delivery dashboard in Tableau Public

One or two evenings. Tableau Public is free: download it from public.tableau.com and create an account.

## 1. Connect the data

* Open Tableau Public, Connect, Text file, and choose `data/state performance.csv`.
* Add the other two files as separate data sources (Data menu, New Data Source): `monthly delivery.csv` and `seller scorecard.csv`.
* In the state source, right click the state field, Geographic Role, State/Province. Tableau recognises Brazilian state codes once the country is set: Map menu, Edit Locations, Country = Brazil.

## 2. Calculated fields

In the state source (Analysis, Create Calculated Field):

* `Late orders` = `[Orders] * [Late rate]`
* `Weighted late rate` = `SUM([Late orders]) / SUM([Orders])`
* `Weighted review` = `SUM([Avg review] * [Orders]) / SUM([Orders])`

Use the weighted versions in any total or KPI tile, so that small states do not count as much as São Paulo.

In the seller source:

* `Problem seller` = `IF [Late rate] > 0.10 THEN "Problem" ELSE "Other" END`

## 3. Sheets

* **KPI tiles:** four small sheets showing total orders, weighted late rate, weighted review and number of problem sellers. Use a large font and no axes.
* **Map:** drag State to the view, Weighted late rate to Colour (sequential grey to black), Orders to Tooltip. Title it with the finding: "Rio de Janeiro and the north east break the delivery promise".
* **Trend:** from the monthly source, Month on Columns (continuous month), Late rate and Avg review on Rows, then right click the second axis, Dual Axis. Mark November 2017 and February to March 2018 with an annotation.
* **Seller scatter:** Late rate on Columns, Avg review on Rows, Seller on Detail, Orders on Size, Tier on Colour. Add a reference line at 10% late.

## 4. Dashboard

* New Dashboard, size Automatic, layout: KPI tiles across the top, map on the left, trend on the right, seller scatter across the bottom.
* Use the map as a filter (click the funnel icon on the map sheet) so clicking a state filters the tooltip text; keep colours to greys plus one accent for problem sellers.
* Add a short text box with the three findings from the README.

## 5. Publish

File, Save to Tableau Public. Copy the link and paste it into the README where it says "link to be added after publishing". Take a screenshot of the dashboard and save it in `charts/` so people who do not open Tableau can still see it.
