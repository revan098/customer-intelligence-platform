USE customer_intelligence;

SELECT
    DATE_ADD(MAX(invoice_date), INTERVAL 1 DAY) AS analysis_date
FROM transactions;

WITH analysis_date AS (
    SELECT
        DATE_ADD(MAX(invoice_date), INTERVAL 1 DAY) AS reference_date
    FROM transactions
),

customer_metrics AS (
    SELECT
        t.customer_id,

        MIN(t.invoice_date) AS first_purchase_date,

        MAX(t.invoice_date) AS last_purchase_date,

        COUNT(DISTINCT t.invoice) AS frequency,

        ROUND(SUM(t.revenue), 2) AS monetary_value,

        ROUND(
            SUM(t.revenue) /
            COUNT(DISTINCT t.invoice),
            2
        ) AS average_order_value,

        COUNT(DISTINCT t.stock_code) AS unique_products,

        SUM(t.quantity) AS total_quantity

    FROM transactions t

    WHERE t.customer_id IS NOT NULL

    GROUP BY t.customer_id
)

SELECT
    cm.*,

    DATEDIFF(
        ad.reference_date,
        cm.last_purchase_date
    ) AS recency_days,

    DATEDIFF(
        cm.last_purchase_date,
        cm.first_purchase_date
    ) AS customer_tenure_days

FROM customer_metrics cm

CROSS JOIN analysis_date ad

ORDER BY cm.monetary_value DESC;

WITH order_dates AS (

    SELECT DISTINCT
        customer_id,
        invoice,
        DATE(invoice_date) AS order_date

    FROM transactions

    WHERE customer_id IS NOT NULL
),

order_gaps AS (

    SELECT
        customer_id,
        order_date,

        LAG(order_date) OVER (
            PARTITION BY customer_id
            ORDER BY order_date
        ) AS previous_order_date

    FROM order_dates
),

customer_gap AS (

    SELECT
        customer_id,

        AVG(
            DATEDIFF(
                order_date,
                previous_order_date
            )
        ) AS average_order_gap

    FROM order_gaps

    WHERE previous_order_date IS NOT NULL

    GROUP BY customer_id
)

SELECT *
FROM customer_gap
ORDER BY average_order_gap DESC;

SELECT
    customer_id,

    COUNT(*) AS return_line_items,

    SUM(ABS(quantity)) AS returned_quantity,

    ROUND(
        SUM(ABS(quantity) * price),
        2
    ) AS returned_value

FROM transactions

WHERE customer_id IS NOT NULL
  AND quantity < 0

GROUP BY customer_id
ORDER BY returned_value DESC;


CREATE TABLE customer_features AS

WITH analysis_date AS (

    SELECT
        DATE_ADD(
            MAX(invoice_date),
            INTERVAL 1 DAY
        ) AS reference_date

    FROM transactions
),

customer_metrics AS (

    SELECT
        t.customer_id,

        MAX(t.country) AS country,

        MIN(t.invoice_date) AS first_purchase_date,

        MAX(t.invoice_date) AS last_purchase_date,

        COUNT(DISTINCT t.invoice) AS frequency,

        ROUND(
            SUM(t.revenue),
            2
        ) AS monetary_value,

        ROUND(
            SUM(t.revenue) /
            COUNT(DISTINCT t.invoice),
            2
        ) AS average_order_value,

        COUNT(DISTINCT t.stock_code)
            AS unique_products,

        SUM(t.quantity)
            AS total_quantity

    FROM transactions t

    WHERE t.customer_id IS NOT NULL

    GROUP BY t.customer_id
),

order_dates AS (

    SELECT DISTINCT
        customer_id,
        invoice,
        DATE(invoice_date) AS order_date

    FROM transactions

    WHERE customer_id IS NOT NULL
),

order_gaps AS (

    SELECT
        customer_id,
        order_date,

        LAG(order_date) OVER (
            PARTITION BY customer_id
            ORDER BY order_date
        ) AS previous_order_date

    FROM order_dates
),

customer_gap AS (

    SELECT
        customer_id,

        AVG(
            DATEDIFF(
                order_date,
                previous_order_date
            )
        ) AS average_order_gap

    FROM order_gaps

    WHERE previous_order_date IS NOT NULL

    GROUP BY customer_id
),

return_metrics AS (

    SELECT
        customer_id,

        COUNT(*) AS return_line_items,

        SUM(ABS(quantity))
            AS returned_quantity,

        ROUND(
            SUM(
                ABS(quantity) * price
            ),
            2
        ) AS returned_value

    FROM transactions

    WHERE customer_id IS NOT NULL
      AND quantity < 0

    GROUP BY customer_id
)

SELECT

    cm.customer_id,

    cm.country,

    cm.first_purchase_date,

    cm.last_purchase_date,

    DATEDIFF(
        ad.reference_date,
        cm.last_purchase_date
    ) AS recency_days,

    cm.frequency,

    cm.monetary_value,

    cm.average_order_value,

    cm.unique_products,

    cm.total_quantity,

    ROUND(
        cg.average_order_gap,
        2
    ) AS average_order_gap,

    COALESCE(
        rm.return_line_items,
        0
    ) AS return_line_items,

    COALESCE(
        rm.returned_quantity,
        0
    ) AS returned_quantity,

    COALESCE(
        rm.returned_value,
        0
    ) AS returned_value,

    ROUND(
        COALESCE(rm.returned_value, 0)
        / NULLIF(cm.monetary_value, 0)
        * 100,
        2
    ) AS return_value_rate,

    DATEDIFF(
        cm.last_purchase_date,
        cm.first_purchase_date
    ) AS customer_tenure_days

FROM customer_metrics cm

CROSS JOIN analysis_date ad

LEFT JOIN customer_gap cg
    ON cm.customer_id = cg.customer_id

LEFT JOIN return_metrics rm
    ON cm.customer_id = rm.customer_id;
    
    
SELECT COUNT(*)
FROM customer_features;

DESCRIBE customer_features;

SELECT *
FROM customer_features
LIMIT 10;

SELECT
    SUM(recency_days IS NULL) AS null_recency,
    SUM(frequency IS NULL) AS null_frequency,
    SUM(monetary_value IS NULL) AS null_monetary,
    SUM(average_order_value IS NULL) AS null_aov,
    SUM(unique_products IS NULL) AS null_products,
    SUM(customer_tenure_days IS NULL) AS null_tenure
FROM customer_features;

CREATE TABLE customer_rfm AS

SELECT
    cf.*,

    NTILE(5) OVER (
        ORDER BY recency_days DESC
    ) AS r_score,

    NTILE(5) OVER (
        ORDER BY frequency ASC
    ) AS f_score,

    NTILE(5) OVER (
        ORDER BY monetary_value ASC
    ) AS m_score

FROM customer_features cf;

ALTER TABLE customer_rfm
ADD COLUMN rfm_score VARCHAR(3);
ALTER TABLE customer_rfm
ADD COLUMN customer_segment VARCHAR(50);

SET SQL_SAFE_UPDATES = 0;

UPDATE customer_rfm
SET rfm_score = CONCAT(r_score, f_score, m_score)
WHERE customer_id IS NOT NULL;

SELECT
    customer_id,
    r_score,
    f_score,
    m_score,
    rfm_score
FROM customer_rfm
LIMIT 10;
    
UPDATE customer_rfm
SET customer_segment =
    CASE

        WHEN r_score >= 4
         AND f_score >= 4
         AND m_score >= 4
            THEN 'Champions'

        WHEN r_score >= 4
         AND f_score >= 3
         AND m_score >= 3
            THEN 'Loyal Customers'

        WHEN r_score >= 4
         AND f_score <= 2
            THEN 'New / Promising'

        WHEN r_score <= 2
         AND f_score >= 3
         AND m_score >= 3
            THEN 'At Risk'

        WHEN r_score <= 2
         AND f_score <= 2
            THEN 'Lost / Inactive'

        ELSE 'Potential Loyalists'

    END;
select * from customer_rfm;

SELECT
    customer_segment,
    COUNT(*) AS customers,
    ROUND(
        SUM(monetary_value),
        2
    ) AS revenue
FROM customer_rfm
GROUP BY customer_segment
ORDER BY revenue DESC;

SELECT
    customer_segment,
    COUNT(*) AS customers,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM customer_rfm),
        2
    ) AS customer_percentage
FROM customer_rfm
GROUP BY customer_segment
ORDER BY customers DESC;

CREATE TABLE customer_churn_modeling AS

SELECT
    f.customer_id,

    f.recency_days,
    f.frequency,
    f.monetary_value,
    f.average_order_value,
    f.unique_products,
    f.total_quantity,
    f.average_order_gap,
    f.customer_tenure_days,

    l.churned

FROM customer_churn_features f

INNER JOIN customer_churn_labels l
    ON f.customer_id = l.customer_id;


SELECT COUNT(*) AS total_customers
FROM customer_churn_modeling;

SELECT
    churned,
    COUNT(*) AS customers,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM customer_churn_modeling
GROUP BY churned
ORDER BY churned;

SELECT
    MIN(recency_days) AS min_recency,
    MAX(recency_days) AS max_recency,

    MIN(frequency) AS min_frequency,
    MAX(frequency) AS max_frequency,

    MIN(monetary_value) AS min_monetary,
    MAX(monetary_value) AS max_monetary,

    MIN(average_order_value) AS min_aov,
    MAX(average_order_value) AS max_aov,

    MIN(customer_tenure_days) AS min_tenure,
    MAX(customer_tenure_days) AS max_tenure
FROM customer_churn_modeling;

SELECT *
FROM customer_churn_modeling
LIMIT 10;

USE customer_intelligence;

ALTER TABLE customer_rfm
ADD COLUMN segment VARCHAR(50);

SELECT
    segment,
    COUNT(*) AS customers,
    SUM(monetary_value) AS revenue
FROM customer_rfm
GROUP BY segment
ORDER BY revenue DESC;

SELECT
    customer_id,
    r_score,
    f_score,
    m_score,
    rfm_score,
    monetary_value,
    segment
FROM customer_rfm
LIMIT 20;

