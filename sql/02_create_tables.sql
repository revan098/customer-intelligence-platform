USE customer_intelligence;

CREATE TABLE transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    invoice VARCHAR(20) NOT NULL,
    stock_code VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    quantity INT NOT NULL,
    invoice_date DATETIME NOT NULL,
    price DECIMAL(12,4) NOT NULL,
    customer_id INT,
    country VARCHAR(100),
    revenue DECIMAL(14,2) NOT NULL,

    INDEX idx_invoice (invoice),
    INDEX idx_customer (customer_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_invoice_date (invoice_date)
);

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    country VARCHAR(100),
    first_purchase_date DATETIME,
    last_purchase_date DATETIME,
    total_orders INT,
    total_revenue DECIMAL(14,2),

    INDEX idx_customer_country (country)
);

CREATE TABLE products (
    stock_code VARCHAR(50) PRIMARY KEY,
    description VARCHAR(255),
    average_price DECIMAL(12,4),
    total_quantity BIGINT,
    total_revenue DECIMAL(14,2)
);

show tables;
DESCRIBE transactions;
describe CUSTOMERS;
describe PRODUCTS;


ALTER TABLE transactions
ADD COLUMN is_cancellation BOOLEAN DEFAULT FALSE,
ADD COLUMN is_return BOOLEAN DEFAULT FALSE;

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
    
USE customer_intelligence;

CREATE TABLE IF NOT EXISTS churn_predictions (
    customer_id INT PRIMARY KEY,

    churn_probability DECIMAL(8,6) NOT NULL,

    prediction TINYINT NOT NULL,

    risk_level VARCHAR(20) NOT NULL,

    prediction_date DATETIME NOT NULL,

    INDEX idx_risk_level (risk_level),

    INDEX idx_churn_probability (churn_probability),

    CONSTRAINT fk_churn_prediction_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer_churn_modeling(customer_id)
);

USE customer_intelligence;

SHOW CREATE TABLE customer_churn_modeling;

SHOW INDEX FROM customer_churn_modeling;
ALTER TABLE customer_churn_modeling
ADD PRIMARY KEY (customer_id);

SELECT
    COUNT(*) AS total_rows,
    COUNT(customer_id) AS non_null_customer_ids,
    COUNT(DISTINCT customer_id) AS unique_customer_ids
FROM customer_churn_modeling;

ALTER TABLE customer_churn_modeling
ADD PRIMARY KEY (customer_id);

USE customer_intelligence;

CREATE TABLE IF NOT EXISTS churn_predictions (
    customer_id INT PRIMARY KEY,
    churn_probability DECIMAL(8,6) NOT NULL,
    prediction TINYINT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    prediction_date DATETIME NOT NULL,

    INDEX idx_risk_level (risk_level),
    INDEX idx_churn_probability (churn_probability),

    CONSTRAINT fk_churn_prediction_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer_churn_modeling(customer_id)
);

DESCRIBE churn_predictions;

SELECT COUNT(*)
FROM churn_predictions;

SELECT
    risk_level,
    COUNT(*) AS customers
FROM churn_predictions
GROUP BY risk_level
ORDER BY
    FIELD(
        risk_level,
        'LOW',
        'MEDIUM',
        'HIGH'
    );
    
SELECT
    customer_id,
    churn_probability,
    prediction,
    risk_level,
    prediction_date
FROM churn_predictions
ORDER BY churn_probability DESC
LIMIT 10;

