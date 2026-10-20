-- ====================================================================
-- TradeIQ E-Commerce Business Intelligence Database Schema (MySQL 8)
-- Database Name: ecommerce_bi
-- ====================================================================

-- 1. Create Database if not exists
CREATE DATABASE IF NOT EXISTS ecommerce_bi
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ecommerce_bi;

-- 2. Drop existing tables if re-initializing (child tables first)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;

-- 3. Products Table
-- Stores catalog details across diverse e-commerce retail categories.
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_products_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Orders Table
-- Stores high-level order metadata, date of occurrence, status, and sales region.
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    order_date DATETIME NOT NULL,
    order_status VARCHAR(50) NOT NULL,
    region VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_orders_date (order_date),
    INDEX idx_orders_status (order_status),
    INDEX idx_orders_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Order Items Table
-- Stores line-item transactions linking orders to products.
-- Unit prices, discounts, and return amounts are stored with DECIMAL(10,2) precision.
-- Note: 'discount' and 'return_amount' represent absolute monetary values in currency units.
CREATE TABLE order_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (discount >= 0),
    return_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (return_amount >= 0),
    CONSTRAINT fk_items_order FOREIGN KEY (order_id) 
        REFERENCES orders (order_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) 
        REFERENCES products (product_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    INDEX idx_items_order_id (order_id),
    INDEX idx_items_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
