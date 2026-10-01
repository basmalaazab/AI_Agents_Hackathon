# Demo Data — AI BI Agent Hackathon

> ⚠️ **ALL DATA IN THIS DIRECTORY IS SYNTHETIC AND FICTIONAL.**
> Generated solely for hackathon demonstration purposes. No real customer or business data is included.

## Files

| File | Description | Records | Quality Issues |
|------|-------------|---------|----------------|
| `sample_sales.csv` | Sales/order records from a simulated CSV upload | 21 rows | Duplicate row (SO-2001), missing required fields (SO-2008), negative amount (SO-2013), invalid date (SO-2020), currency symbol in amount (SO-2003), US-format date (SO-2005) |
| `sample_customers.csv` | Customer records from a simulated CSV upload | 14 rows | Duplicate (CUST-101), missing email (CUST-106), all-caps names (CUST-102), invalid email (CUST-112), completely empty row (CUST-113) |

## Expected Pipeline Behaviour

### sales CSV ingestion
- **Fetched:** 21 rows  
- **Invalid (rejected):** SO-2008 (missing required fields), SO-2013 (negative amount), SO-2020 (invalid date)  
- **Duplicate (intra-batch):** SO-2001 appears twice → 1 removed  
- **Inserted:** ≈ 17 rows on first run  
- **Second run:** 0 inserted, all marked as duplicates  

### customers CSV ingestion
- **Fetched:** 14 rows  
- **Invalid (rejected):** CUST-113 (all fields empty, missing customer_id)  
- **Duplicate (intra-batch):** CUST-101 appears twice → 1 removed  
- **Inserted:** 12 rows on first run  
- **Cleaned:** CUST-102 names title-cased; CUST-103 names title-cased; CUST-112 invalid email set to null  

## Column Name Inconsistency Examples

The validator/cleaner handles these common aliases automatically:
- `sale_id` → `order_id`
- `amount` / `grand_total` / `revenue` → `total_amount`
- `sale_date` / `purchase_date` → `order_date`
- `cust_id` / `client_id` → `customer_id`
