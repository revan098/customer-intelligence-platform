# Customer Intelligence & Automated Reporting Platform

An end-to-end customer analytics platform that transforms retail transaction data into customer intelligence, churn-risk predictions, explainable ML insights, and automated executive reporting.

---

## 📌 Project Overview

The **Customer Intelligence & Automated Reporting Platform** is an end-to-end analytics solution built on retail transaction data.

The platform combines:

- Data cleaning and ETL
- MySQL data storage
- Customer behavior analytics
- RFM customer segmentation
- Churn prediction using XGBoost
- SHAP-based model explainability
- Customer-level 360° analysis
- Streamlit business intelligence dashboard
- Gemini-powered automated executive reporting

The goal is to move from **raw transactional data → business intelligence → predictive analytics → actionable customer insights** within a single workflow.

---

## 🎯 Business Problem

Retail businesses generate large volumes of transaction data, but raw transaction records alone do not provide enough visibility into:

- Which customers generate the most revenue?
- Which customers are highly engaged?
- Which customers may be at risk of churn?
- What customer behaviors are associated with churn risk?
- Which products and countries contribute most to revenue?
- How can management receive concise insights without manually analyzing dashboards?

This project addresses these questions through an integrated analytics and machine-learning platform.

---

# 🏗️ Solution Architecture

```text
                         ┌──────────────────────┐
                         │   Retail Excel Data  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Data Cleaning & ETL  │
                         │       Python         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │        MySQL         │
                         │  Customer + Sales    │
                         │       Data           │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │ Customer / RFM │ │ Churn Features │ │ Revenue /      │
        │   Analytics    │ │   Engineering  │ │ Product /      │
        │                │ │                │ │ Country        │
        └───────┬────────┘ └───────┬────────┘ │ Analytics      │
                │                  │           └───────┬────────┘
                │                  ▼                   │
                │         ┌────────────────┐          │
                │         │    XGBoost     │          │
                │         │ Churn Model    │          │
                │         └───────┬────────┘          │
                │                 │                   │
                │                 ▼                   │
                │         ┌────────────────┐          │
                │         │ SHAP Explain-  │          │
                │         │    ability     │          │
                │         └───────┬────────┘          │
                │                 │                   │
                └────────────┬────┴───────────────────┘
                             │
                             ▼
                   ┌────────────────────┐
                   │ Streamlit Dashboard │
                   │                    │
                   │ • Executive View   │
                   │ • Revenue Intel     │
                   │ • Churn Intel       │
                   │ • Customer 360      │
                   │ • AI Reports        │
                   └──────────┬─────────┘
                              │
                              ▼
                   ┌────────────────────┐
                   │ Gemini Executive   │
                   │     Reporting      │
                   └────────────────────┘