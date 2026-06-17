# The Last Mile Logistics Auditor 

> Audit of delivery-estimate accuracy for **Veridi Logistics** using the Olist Brazilian
> E-Commerce dataset.

## A. Executive Summary

This work summarises the walkthrough that addresses the CEO's question on "Are we failing specific regions, or is this a nationwide problem?". Veridi's delivery problem is **regional, not nationwide**. The national late rate is only **~8%**,
but it is concentrated in the **North-eastern states** — Alagoas (~24%), Maranhão (~20%), Piauí,
Ceará and Sergipe (~15%), which run **2–3× the national average**, while the south-east hub region
is reliable. Lateness is the direct cause of the negative-review spike. Average review scores fall
from **4.29★ (On Time)** to **3.46★ (Late)** to **1.78★ (Super Late)**. On the note, Veridi is *not*
uniformly over-promising, nationally we deliver well than estimated, yet the North-east is *still* late despite that padding, meaning its last-mile
network is reallly under-resourced. **Recommendation** says we should work on the carrier network in the
North-east, tighten the wildly padded far-north estimates, and recalibrate the delivery promise per
region.

## B. Project Links

- **Notebook:** `notebook.ipynb` (+ `notebook.html`) in this repo · [Open in Google Colab](https://colab.research.google.com/drive/1oRdeySilAGEgb-0KKJCFTjEf82EHSPcy?usp=sharing)
- **Dashboard (Streamlit Cloud):** https://myrepo1-zuamrwnzg4metjyhsnfhgt.streamlit.app/
- **Presentation (slides PDF/PPT):** `presentation.pdf` in this repo · **<ADD LINK if hosted>**


## C. Technical Explanation

**Data cleaning and techniques.** (1) *Reviews were de-duplicated* — 547 orders had multiple reviews, which would
inflate a 1-to-many join and corrupt every percentage; we keep the **most recent** review per order
and assert the master table stays at exactly one row per order (no row inflation). (2) *Undelivered
orders excluded* — orders that are cancelled/unavailable or have a null `order_delivered_customer_date`
(2,971 of them) have no actual delivery date and are dropped from the lateness analysis rather than
mis-counted as on-time. (3) Dates are parsed to datetimes and `Days_Difference` is computed as
`estimated − actual` (positive = early), then classified **On Time / Late / Super Late (>5 days)**.

**Candidate's Choice.** Beyond the stories I added some
analyses to get more insights.


1. **Breakdown of the Lateness** — Breaking each delivery into *payment approval → seller handling →
   carrier transit* shows **carrier transit is ~74% of total time and triples (≈8 → 26 days) on late
   orders**. The delay is a **carrier / last-mile** problem, not a warehouse one which tells operations
   exactly *what* to fix.
2. **Revenue at risk** — joining order payment values, **≈ R$1.35M (8.8%) of delivered revenue** sits
   on late orders, concentrated in the high-volume south-east (**SP, RJ, MG**). This implies we should protect **revenue** in
   SP/RJ and protect **reputation** in the North-east.

**Reproducibility.** This notebook expects the Olist CSVs in the **same
folder** as the notebook. To re-run, download
the dataset from the Kaggle link below and extract the CSVs beside the notebook. The dashboard reads
some aggregate data to give us a dashboard experience to none technical fellows. So it deploys on Streamlit Cloud.




## D. The Data

You will use the **Olist E-Commerce Dataset**, a real commercial dataset from a Brazilian marketplace. These are multiple CSV files.

- **Source:** [Kaggle - Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **Key Files to Use:**
  - `olist_orders_dataset.csv` (The central table)
  - `olist_order_reviews_dataset.csv` (Sentiment)
  - `olist_customers_dataset.csv` (Location)
  - `olist_products_dataset.csv` (Categories)

**Tools/packages must have:** Python · Pandas · Matplotlib · Seaborn · GeoPandas · Streamlit · Google Colab