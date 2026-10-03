"""
Synthetic demo data for the mock e-commerce API.

⚠️  ALL RECORDS ARE FICTIONAL — generated for hackathon demonstration purposes only.
No real customer data is used.
"""

MOCK_CUSTOMERS = [
    {"customer_id": "C001", "email": "alice@example.com", "first_name": "Alice", "last_name": "Johnson", "phone": "+1-555-0101", "city": "New York", "country": "USA"},
    {"customer_id": "C002", "email": "bob@example.com", "first_name": "Bob", "last_name": "Smith", "phone": "+1-555-0102", "city": "Los Angeles", "country": "USA"},
    {"customer_id": "C003", "email": "carol@example.com", "first_name": "Carol", "last_name": "Williams", "phone": "+44-20-7946-0001", "city": "London", "country": "UK"},
    {"customer_id": "C004", "email": "david@example.com", "first_name": "David", "last_name": "Brown", "phone": "+1-555-0104", "city": "Chicago", "country": "USA"},
    {"customer_id": "C005", "email": "eva@example.com", "first_name": "Eva", "last_name": "Davis", "phone": "+49-30-12345", "city": "Berlin", "country": "Germany"},
    {"customer_id": "C006", "email": "frank@example.com", "first_name": "Frank", "last_name": "Miller", "phone": "+1-555-0106", "city": "Houston", "country": "USA"},
    {"customer_id": "C007", "email": "grace@example.com", "first_name": "Grace", "last_name": "Wilson", "phone": "+1-555-0107", "city": "Phoenix", "country": "USA"},
    {"customer_id": "C008", "email": "henry@example.com", "first_name": "Henry", "last_name": "Taylor", "phone": "+61-2-5550-1234", "city": "Sydney", "country": "Australia"},
    {"customer_id": "C009", "email": "iris@example.com", "first_name": "Iris", "last_name": "Anderson", "phone": "+1-555-0109", "city": "Philadelphia", "country": "USA"},
    {"customer_id": "C010", "email": "jack@example.com", "first_name": "Jack", "last_name": "Thomas", "phone": "+1-555-0110", "city": "San Antonio", "country": "USA"},
]

MOCK_PRODUCTS = [
    {"product_id": "P001", "product_name": "Wireless Headphones Pro", "sku": "WHP-001", "category": "Electronics", "unit_price": 149.99, "currency": "USD"},
    {"product_id": "P002", "product_name": "Ergonomic Office Chair", "sku": "EOC-002", "category": "Furniture", "unit_price": 299.99, "currency": "USD"},
    {"product_id": "P003", "product_name": "Stainless Steel Water Bottle", "sku": "SWB-003", "category": "Sports", "unit_price": 34.99, "currency": "USD"},
    {"product_id": "P004", "product_name": "Mechanical Keyboard", "sku": "MKB-004", "category": "Electronics", "unit_price": 119.99, "currency": "USD"},
    {"product_id": "P005", "product_name": "Yoga Mat Premium", "sku": "YMP-005", "category": "Sports", "unit_price": 59.99, "currency": "USD"},
    {"product_id": "P006", "product_name": "Coffee Maker Deluxe", "sku": "CMD-006", "category": "Kitchen", "unit_price": 89.99, "currency": "USD"},
    {"product_id": "P007", "product_name": "USB-C Hub 7-in-1", "sku": "UCH-007", "category": "Electronics", "unit_price": 49.99, "currency": "USD"},
    {"product_id": "P008", "product_name": "Bamboo Desk Organiser", "sku": "BDO-008", "category": "Office", "unit_price": 29.99, "currency": "USD"},
    {"product_id": "P009", "product_name": "Portable Bluetooth Speaker", "sku": "PBS-009", "category": "Electronics", "unit_price": 79.99, "currency": "USD"},
    {"product_id": "P010", "product_name": "Resistance Bands Set", "sku": "RBS-010", "category": "Sports", "unit_price": 24.99, "currency": "USD"},
]

MOCK_ORDERS = [
    {"order_id": "ORD-1001", "customer_id": "C001", "order_date": "2024-01-05T10:30:00Z", "status": "completed", "total_amount": 149.99, "currency": "USD", "product_name": "Wireless Headphones Pro", "quantity": 1, "unit_price": 149.99},
    {"order_id": "ORD-1002", "customer_id": "C002", "order_date": "2024-01-08T14:15:00Z", "status": "completed", "total_amount": 359.98, "currency": "USD", "product_name": "Ergonomic Office Chair", "quantity": 1, "unit_price": 299.99},
    {"order_id": "ORD-1003", "customer_id": "C003", "order_date": "2024-01-12T09:45:00Z", "status": "completed", "total_amount": 34.99, "currency": "USD", "product_name": "Stainless Steel Water Bottle", "quantity": 1, "unit_price": 34.99},
    {"order_id": "ORD-1004", "customer_id": "C001", "order_date": "2024-01-18T16:00:00Z", "status": "completed", "total_amount": 119.99, "currency": "USD", "product_name": "Mechanical Keyboard", "quantity": 1, "unit_price": 119.99},
    {"order_id": "ORD-1005", "customer_id": "C004", "order_date": "2024-01-22T11:30:00Z", "status": "cancelled", "total_amount": 59.99, "currency": "USD", "product_name": "Yoga Mat Premium", "quantity": 1, "unit_price": 59.99},
    {"order_id": "ORD-1006", "customer_id": "C005", "order_date": "2024-02-01T08:00:00Z", "status": "completed", "total_amount": 89.99, "currency": "USD", "product_name": "Coffee Maker Deluxe", "quantity": 1, "unit_price": 89.99},
    {"order_id": "ORD-1007", "customer_id": "C002", "order_date": "2024-02-05T13:45:00Z", "status": "completed", "total_amount": 49.99, "currency": "USD", "product_name": "USB-C Hub 7-in-1", "quantity": 1, "unit_price": 49.99},
    {"order_id": "ORD-1008", "customer_id": "C006", "order_date": "2024-02-10T10:00:00Z", "status": "completed", "total_amount": 29.99, "currency": "USD", "product_name": "Bamboo Desk Organiser", "quantity": 1, "unit_price": 29.99},
    {"order_id": "ORD-1009", "customer_id": "C007", "order_date": "2024-02-14T15:20:00Z", "status": "completed", "total_amount": 79.99, "currency": "USD", "product_name": "Portable Bluetooth Speaker", "quantity": 1, "unit_price": 79.99},
    {"order_id": "ORD-1010", "customer_id": "C008", "order_date": "2024-02-18T09:10:00Z", "status": "completed", "total_amount": 24.99, "currency": "USD", "product_name": "Resistance Bands Set", "quantity": 1, "unit_price": 24.99},
    {"order_id": "ORD-1011", "customer_id": "C009", "order_date": "2024-02-22T14:00:00Z", "status": "completed", "total_amount": 269.98, "currency": "USD", "product_name": "Wireless Headphones Pro", "quantity": 2, "unit_price": 149.99},
    {"order_id": "ORD-1012", "customer_id": "C010", "order_date": "2024-03-01T11:45:00Z", "status": "completed", "total_amount": 299.99, "currency": "USD", "product_name": "Ergonomic Office Chair", "quantity": 1, "unit_price": 299.99},
    {"order_id": "ORD-1013", "customer_id": "C003", "order_date": "2024-03-05T10:30:00Z", "status": "completed", "total_amount": 119.99, "currency": "USD", "product_name": "Mechanical Keyboard", "quantity": 1, "unit_price": 119.99},
    {"order_id": "ORD-1014", "customer_id": "C001", "order_date": "2024-03-10T16:15:00Z", "status": "completed", "total_amount": 89.99, "currency": "USD", "product_name": "Coffee Maker Deluxe", "quantity": 1, "unit_price": 89.99},
    {"order_id": "ORD-1015", "customer_id": "C004", "order_date": "2024-03-15T09:00:00Z", "status": "refunded", "total_amount": 49.99, "currency": "USD", "product_name": "USB-C Hub 7-in-1", "quantity": 1, "unit_price": 49.99},
]
