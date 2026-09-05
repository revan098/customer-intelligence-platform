CREATE TABLE IF NOT EXISTS transactions (
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
    is_cancellation BOOLEAN DEFAULT FALSE,
    is_return BOOLEAN DEFAULT FALSE,

    INDEX idx_invoice (invoice),
    INDEX idx_customer (customer_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_invoice_date (invoice_date)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    country VARCHAR(100),
    first_purchase_date DATETIME,
    last_purchase_date DATETIME,
    total_orders INT,
    total_revenue DECIMAL(14,2),

    INDEX idx_customer_country (country)
);

CREATE TABLE IF NOT EXISTS products (
    stock_code VARCHAR(50) PRIMARY KEY,
    description VARCHAR(255),
    average_price DECIMAL(12,4),
    total_quantity BIGINT,
    total_revenue DECIMAL(14,2)
);

CREATE TABLE IF NOT EXISTS customer_features (
    customer_id INT NOT NULL PRIMARY KEY,
    country VARCHAR(100),
    first_purchase_date DATETIME,
    last_purchase_date DATETIME,
    recency_days INT,
    frequency BIGINT NOT NULL DEFAULT 0,
    monetary_value DECIMAL(36,2),
    average_order_value DECIMAL(37,2),
    unique_products BIGINT NOT NULL DEFAULT 0,
    total_quantity DECIMAL(32,0),
    average_order_gap DECIMAL(11,2),
    return_line_items BIGINT NOT NULL DEFAULT 0,
    returned_quantity DECIMAL(32,0) NOT NULL DEFAULT 0,
    returned_value DECIMAL(43,2) NOT NULL DEFAULT 0.00,
    return_value_rate DECIMAL(49,2),
    customer_tenure_days INT
);

CREATE TABLE IF NOT EXISTS customer_rfm (
    customer_id INT NOT NULL PRIMARY KEY,
    country VARCHAR(100),
    first_purchase_date DATETIME,
    last_purchase_date DATETIME,
    recency_days INT,
    frequency BIGINT NOT NULL DEFAULT 0,
    monetary_value DECIMAL(36,2),
    average_order_value DECIMAL(37,2),
    unique_products BIGINT NOT NULL DEFAULT 0,
    total_quantity DECIMAL(32,0),
    average_order_gap DECIMAL(11,2),
    return_line_items BIGINT NOT NULL DEFAULT 0,
    returned_quantity DECIMAL(32,0) NOT NULL DEFAULT 0,
    returned_value DECIMAL(43,2) NOT NULL DEFAULT 0.00,
    return_value_rate DECIMAL(49,2),
    customer_tenure_days INT,
    r_score BIGINT UNSIGNED NOT NULL DEFAULT 0,
    f_score BIGINT UNSIGNED NOT NULL DEFAULT 0,
    m_score BIGINT UNSIGNED NOT NULL DEFAULT 0,
    rfm_score VARCHAR(3),
    customer_segment VARCHAR(50),
    segment VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS customer_churn_features (
    customer_id INT NOT NULL PRIMARY KEY,
    recency_days INT,
    frequency BIGINT NOT NULL DEFAULT 0,
    monetary_value DECIMAL(58,2),
    average_order_value DECIMAL(59,2),
    unique_products BIGINT NOT NULL DEFAULT 0,
    total_quantity DECIMAL(32,0),
    average_order_gap DECIMAL(13,2),
    customer_tenure_days INT
);

CREATE TABLE IF NOT EXISTS customer_churn_labels (
    customer_id INT NOT NULL PRIMARY KEY,
    churned INT NOT NULL DEFAULT 0,
    future_purchase_lines BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS customer_churn_modeling (
    customer_id INT NOT NULL PRIMARY KEY,
    recency_days INT,
    frequency BIGINT NOT NULL DEFAULT 0,
    monetary_value DECIMAL(58,2),
    average_order_value DECIMAL(59,2),
    unique_products BIGINT NOT NULL DEFAULT 0,
    total_quantity DECIMAL(32,0),
    average_order_gap DECIMAL(13,2),
    customer_tenure_days INT,
    churned INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS churn_predictions (
    customer_id INT NOT NULL PRIMARY KEY,
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