SELECT COUNT(*)
FROM transactions;

SELECT
    MIN(invoice_date) AS first_transaction,
    MAX(invoice_date) AS last_transaction
FROM transactions;

SELECT
    COUNT(DISTINCT customer_id) AS customers
FROM transactions
WHERE customer_id IS NOT NULL;

SELECT
    country,
    COUNT(DISTINCT customer_id) AS customers,
    COUNT(DISTINCT invoice) AS orders,
    ROUND(SUM(revenue), 2) AS revenue
FROM transactions
WHERE customer_id IS NOT NULL
GROUP BY country
ORDER BY revenue DESC;

SELECT
    YEAR(invoice_date) AS year,
    MONTH(invoice_date) AS month,
    ROUND(SUM(revenue), 2) AS revenue
FROM transactions
GROUP BY
    YEAR(invoice_date),
    MONTH(invoice_date)
ORDER BY
    year,
    month;

SELECT
    customer_id,
    COUNT(DISTINCT invoice) AS orders,
    SUM(quantity) AS units,
    ROUND(SUM(revenue), 2) AS revenue
FROM transactions
WHERE customer_id IS NOT NULL
GROUP BY customer_id
ORDER BY revenue DESC
LIMIT 20;

SELECT COUNT(*) FROM transactions;

SELECT COUNT(DISTINCT customer_id)
FROM transactions
WHERE customer_id IS NOT NULL;

SELECT
    MIN(invoice_date),
    MAX(invoice_date)
FROM transactions;

SELECT
    YEAR(invoice_date) AS year,
    MONTH(invoice_date) AS month,
    ROUND(SUM(revenue), 2) AS revenue
FROM transactions
GROUP BY
    YEAR(invoice_date),
    MONTH(invoice_date)
ORDER BY
    year,
    month;
    
SELECT
    r_score,
    COUNT(*) AS customers
FROM customer_rfm
GROUP BY r_score
ORDER BY r_score;

SELECT
    f_score,
    COUNT(*) AS customers
FROM customer_rfm
GROUP BY f_score
ORDER BY f_score;

SELECT
    m_score,
    COUNT(*) AS customers
FROM customer_rfm
GROUP BY m_score
ORDER BY m_score;

SELECT
    customer_segment,

    ROUND(AVG(recency_days), 2) AS avg_recency,

    ROUND(AVG(frequency), 2) AS avg_frequency,

    ROUND(AVG(monetary_value), 2) AS avg_monetary,

    ROUND(AVG(average_order_value), 2) AS avg_aov,

    ROUND(AVG(unique_products), 2) AS avg_unique_products,

    ROUND(AVG(average_order_gap), 2) AS avg_order_gap

FROM customer_rfm

GROUP BY customer_segment

ORDER BY avg_monetary DESC;

SELECT
    customer_id,
    country,
    frequency,
    monetary_value,
    average_order_value,
    recency_days,
    customer_segment
FROM customer_rfm
ORDER BY monetary_value DESC
LIMIT 20;

SELECT
    customer_id,
    country,
    recency_days,
    frequency,
    monetary_value,
    customer_segment
FROM customer_rfm
ORDER BY recency_days DESC
LIMIT 20;

SELECT
    COUNT(*) AS one_order_customers
FROM customer_rfm
WHERE frequency = 1;

SELECT
    customer_segment,
    COUNT(*) AS customers
FROM customer_rfm
WHERE frequency = 1
GROUP BY customer_segment
ORDER BY customers DESC;

SELECT
    MIN(average_order_gap) AS min_gap,
    ROUND(AVG(average_order_gap), 2) AS avg_gap,
    MAX(average_order_gap) AS max_gap
FROM customer_rfm;

SELECT
    COUNT(*) AS customers_without_gap
FROM customer_rfm
WHERE average_order_gap IS NULL;

SELECT
    frequency,
    COUNT(*) AS customers,
    SUM(average_order_gap IS NULL) AS missing_gap
FROM customer_rfm
GROUP BY frequency
ORDER BY frequency;

SELECT
    customer_segment,
    COUNT(*) AS customers,
    ROUND(AVG(return_value_rate), 2) AS avg_return_rate,
    ROUND(MAX(return_value_rate), 2) AS max_return_rate
FROM customer_rfm
GROUP BY customer_segment
ORDER BY avg_return_rate DESC;

SELECT
    COUNT(*) AS return_rows,
    SUM(ABS(quantity)) AS returned_quantity,
    ROUND(SUM(ABS(revenue)), 2) AS returned_value
FROM transactions
WHERE quantity < 0;

SELECT
    COUNT(*) AS return_rows_with_customer,
    COUNT(DISTINCT customer_id) AS customers_with_returns,
    SUM(ABS(quantity)) AS returned_quantity,
    ROUND(SUM(ABS(revenue)), 2) AS returned_value
FROM transactions
WHERE quantity < 0
  AND customer_id IS NOT NULL;
  
SELECT
    SUM(return_line_items > 0) AS customers_with_returns,
    SUM(returned_quantity > 0) AS customers_with_returned_qty,
    SUM(returned_value > 0) AS customers_with_returned_value,
    MAX(return_value_rate) AS max_return_rate
FROM customer_features;

SELECT
    MIN(invoice_date) AS first_date,
    MAX(invoice_date) AS last_date,
    DATEDIFF(MAX(invoice_date), MIN(invoice_date)) AS total_days
FROM transactions;

CREATE TABLE customer_churn_labels AS

SELECT
    c.customer_id,

    CASE
        WHEN COUNT(
            CASE
                WHEN t.invoice_date > '2011-09-10'
                 AND t.invoice_date <= '2011-12-09'
                THEN 1
            END
        ) = 0
        THEN 1
        ELSE 0
    END AS churned,

    COUNT(
        CASE
            WHEN t.invoice_date > '2011-09-10'
             AND t.invoice_date <= '2011-12-09'
            THEN 1
        END
    ) AS future_purchase_lines

FROM (
    SELECT DISTINCT customer_id
    FROM transactions
    WHERE customer_id IS NOT NULL
) c

LEFT JOIN transactions t
    ON c.customer_id = t.customer_id

GROUP BY c.customer_id;

SELECT
    churned,
    COUNT(*) AS customers
FROM customer_churn_labels
GROUP BY churned;

SELECT
    ROUND(
        100.0 * SUM(churned) / COUNT(*),
        2
    ) AS churn_rate
FROM customer_churn_labels;

CREATE TABLE customer_churn_features AS

WITH customer_orders AS (

    SELECT
        customer_id,
        invoice,
        DATE(MIN(invoice_date)) AS order_date,
        SUM(revenue) AS order_revenue
    FROM transactions
    WHERE customer_id IS NOT NULL
      AND invoice_date <= '2011-09-10'
    GROUP BY customer_id, invoice

),

order_gaps AS (

    SELECT
        customer_id,
        order_date,
        DATEDIFF(
            order_date,
            LAG(order_date) OVER (
                PARTITION BY customer_id
                ORDER BY order_date
            )
        ) AS order_gap
    FROM customer_orders

),

customer_summary AS (

    SELECT
        customer_id,

        MIN(order_date) AS first_purchase_date,
        MAX(order_date) AS last_purchase_date,

        COUNT(*) AS frequency,

        SUM(order_revenue) AS monetary_value,

        COUNT(DISTINCT order_date) AS purchase_days,

        AVG(order_gap) AS average_order_gap

    FROM order_gaps
    JOIN customer_orders USING (customer_id, order_date)

    GROUP BY customer_id
),

product_summary AS (

    SELECT
        customer_id,
        COUNT(DISTINCT stock_code) AS unique_products,
        SUM(quantity) AS total_quantity

    FROM transactions

    WHERE customer_id IS NOT NULL
      AND invoice_date <= '2011-09-10'

    GROUP BY customer_id
)

SELECT
    cs.customer_id,

    DATEDIFF(
        '2011-09-10',
        cs.last_purchase_date
    ) AS recency_days,

    cs.frequency,

    ROUND(
        cs.monetary_value,
        2
    ) AS monetary_value,

    ROUND(
        cs.monetary_value / NULLIF(cs.frequency, 0),
        2
    ) AS average_order_value,

    ps.unique_products,

    ps.total_quantity,

    ROUND(
        cs.average_order_gap,
        2
    ) AS average_order_gap,

    DATEDIFF(
        cs.last_purchase_date,
        cs.first_purchase_date
    ) AS customer_tenure_days

FROM customer_summary cs

JOIN product_summary ps
    ON cs.customer_id = ps.customer_id;
    
    
SELECT COUNT(*) AS customers
FROM customer_churn_features;

SELECT *
FROM customer_churn_features
LIMIT 10;

SELECT
    MIN(recency_days) AS min_recency,
    MAX(recency_days) AS max_recency,
    MIN(frequency) AS min_frequency,
    MAX(frequency) AS max_frequency,
    MIN(monetary_value) AS min_monetary,
    MAX(monetary_value) AS max_monetary
FROM customer_churn_features;

SELECT
    COUNT(*) AS total_feature_customers,
    SUM(churned = 1) AS churned,
    SUM(churned = 0) AS active
FROM customer_churn_features f
JOIN customer_churn_labels l
    ON f.customer_id = l.customer_id;
    
SELECT
    COUNT(*) AS customers_without_label
FROM customer_churn_features f
LEFT JOIN customer_churn_labels l
    ON f.customer_id = l.customer_id
WHERE l.customer_id IS NULL;

SELECT
    l.churned,
    COUNT(*) AS customers
FROM customer_churn_features f
JOIN customer_churn_labels l
    ON f.customer_id = l.customer_id
GROUP BY l.churned;