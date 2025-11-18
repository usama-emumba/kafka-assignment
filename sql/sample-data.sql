-- Sample data for testing

-- Insert customers
INSERT INTO customers (name, email, phone, address) VALUES
('Alice Johnson', 'alice.johnson@email.com', '555-0101', '123 Maple Street, Springfield, IL 62701'),
('Bob Smith', 'bob.smith@email.com', '555-0102', '456 Oak Avenue, Austin, TX 78701'),
('Carol White', 'carol.white@email.com', '555-0103', '789 Pine Road, Seattle, WA 98101'),
('David Brown', 'david.brown@email.com', '555-0104', '321 Elm Street, Portland, OR 97201'),
('Eve Davis', 'eve.davis@email.com', '555-0105', '654 Birch Lane, Denver, CO 80201');

-- Insert products
INSERT INTO products (name, description, price, stock_quantity, category) VALUES
('Laptop Pro 15', 'High-performance laptop with 16GB RAM', 1299.99, 50, 'Electronics'),
('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 29.99, 200, 'Electronics'),
('Office Chair', 'Comfortable ergonomic office chair', 249.99, 75, 'Furniture'),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 39.99, 150, 'Furniture'),
('USB-C Cable', '6ft USB-C charging cable', 12.99, 500, 'Accessories'),
('Smartphone X', 'Latest smartphone with 128GB storage', 899.99, 100, 'Electronics'),
('Backpack', 'Durable laptop backpack', 59.99, 120, 'Accessories'),
('Water Bottle', 'Insulated stainless steel water bottle', 24.99, 300, 'Accessories');

-- Insert orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address) VALUES
(1, CURRENT_TIMESTAMP - INTERVAL '5 days', 1329.98, 'delivered', '123 Maple Street, Springfield, IL 62701'),
(2, CURRENT_TIMESTAMP - INTERVAL '4 days', 279.98, 'shipped', '456 Oak Avenue, Austin, TX 78701'),
(3, CURRENT_TIMESTAMP - INTERVAL '3 days', 52.98, 'processing', '789 Pine Road, Seattle, WA 98101'),
(4, CURRENT_TIMESTAMP - INTERVAL '2 days', 924.98, 'shipped', '321 Elm Street, Portland, OR 97201'),
(5, CURRENT_TIMESTAMP - INTERVAL '1 day', 84.98, 'pending', '654 Birch Lane, Denver, CO 80201');

-- Insert order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 1299.99),
(1, 2, 1, 29.99),
(2, 3, 1, 249.99),
(2, 4, 1, 29.99),
(3, 5, 2, 12.99),
(3, 8, 1, 24.99),
(4, 6, 1, 899.99),
(4, 8, 1, 24.99),
(5, 7, 1, 59.99),
(5, 8, 1, 24.99);
