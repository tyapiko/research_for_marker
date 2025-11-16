# Amazon Product Research Skill

## Purpose
This skill provides a standardized workflow for researching Amazon products, from keyword search to data collection and organization. Primarily used by the Market Research Agent.

## Prerequisites
- RainforestAPI credentials configured in `.env`
- Keepa API credentials configured in `.env`
- Active internet connection
- Sufficient API tokens (Keepa: 1 token/minute on free plan)

## Workflow Steps

### Step 1: Keyword Search via RainforestAPI
**Objective**: Find relevant ASINs on Amazon.co.jp for the target keyword

**Implementation**:
```python
# modules/keepa_analyzer_simple.py (lines 76-114)
params = {
    "api_key": RAINFOREST_API_KEY,
    "type": "search",
    "amazon_domain": "amazon.co.jp",
    "search_term": keyword,
    "page": "1"  # Currently limited to first page
}
response = requests.get("https://api.rainforestapi.com/request", params=params, timeout=30)
```

**Expected Output Format**:
```python
{
    "search_results": [
        {
            "asin": "B09XYZ1234",
            "title": "商品タイトル",
            "price": {"value": 2980, "currency": "JPY"},
            "rating": 4.2,
            "ratings_total": 1523
        },
        # ... more results
    ]
}
```

**Error Handling**:
- Timeout (>30s): Retry once with increased timeout to 60s
- 429 Rate Limit: Wait 60 seconds and retry
- 503 Service Error: Skip and continue with available data
- Invalid response: Log error and return empty list

**Data Validation**:
- Check `response.status_code == 200`
- Verify `search_results` key exists
- Filter out results without ASIN
- Limit to first 10 ASINs to conserve Keepa tokens

---

### Step 2: Retrieve Product Data via Keepa API
**Objective**: Get detailed sales, pricing, and ranking data for each ASIN

**Implementation**:
```python
# modules/keepa_analyzer_simple.py (lines 127-176)
url = 'https://api.keepa.com/product'
params = {
    'key': KEEPA_API_KEY,
    'domain': '5',  # Amazon.co.jp
    'asin': ','.join(asin_list),
    'stats': '180',  # 180 days of statistics
    'history': '1',  # Include price history
    'rating': '1'    # Include rating history
}
response = requests.get(url, params=params, timeout=60)
```

**Expected Data Fields** (from Keepa response):
```python
{
    "products": [
        {
            "asin": "B09XYZ1234",
            "title": "商品タイトル",
            "stats": {
                "current": [
                    [0, 298000],  # Index 0: Amazon price (¥2,980)
                    [18, 1523]     # Index 18: Rating count
                ]
            },
            "csv": [
                0,  # Amazon price history array
                18, # Rating count history array
                # ... more arrays
            ],
            "monthlySoldHistory": [
                timestamp1, sales1,
                timestamp2, sales2,
                # ... pairs continue
            ]
        }
    ]
}
```

**Critical Data Transformations**:
1. **Price Conversion**: `keepa_price / 100` → actual JPY (e.g., 24.03 → ¥2,403)
2. **Sales History Parsing**: Extract pairs from `monthlySoldHistory` array
   - Even indices: timestamps (minutes since epoch)
   - Odd indices: monthly sales counts
3. **NaN Handling**: Filter out `-1` and NaN values from numpy arrays

**Error Handling**:
- Token exhaustion: Display "Keepa APIトークンが不足しています" + wait time
- Timeout: Retry with extended timeout (up to 90s)
- Invalid product data: Skip product, log warning, continue
- Missing `monthlySoldHistory`: Set sales trend to N/A, score = 0

---

### Step 3: Data Organization and Storage
**Objective**: Structure collected data into analyzable format

**Output DataFrame Schema**:
```python
pd.DataFrame({
    "asin": str,           # Product ASIN
    "title": str,          # Product title
    "price": float,        # Current price (JPY)
    "rating": float,       # Average rating (1-5)
    "review_count": int,   # Total review count
    "bsr": int,            # Best Seller Rank
    "category": str,       # BSR category name
    "seller_count": int,   # Number of sellers (COUNT_NEW)
    "current_sales": int,  # Monthly sales (current)
    "sales_6mo_ago": int,  # Monthly sales (6 months ago)
    "sales_growth": float, # Growth rate (%)
    "product_score": int   # Entry score (0-100)
})
```

**Data Quality Checks**:
1. Remove duplicates by ASIN
2. Filter out products with price = 0 or NaN
3. Set default values for missing fields:
   - `bsr = -1` (not ranked)
   - `seller_count = 0` (unknown)
   - `sales_growth = 0` (no data)
4. Sort by `product_score` descending

**Session State Storage**:
```python
# Store in Streamlit session state for UI access
st.session_state.search_results = results_df
st.session_state.search_completed = True
st.session_state.last_keyword = keyword
```

---

## Performance Considerations

### API Rate Limits
- **Keepa Free Plan**: 1 token per minute
  - Processing 10 ASINs = ~10 minutes wait time
  - Display progress bar with estimated completion time
  - Consider batch processing for larger datasets

- **RainforestAPI**: ~100 requests/hour on free plan
  - Cache search results when possible
  - Avoid redundant searches for same keyword

### Token Optimization
1. **Limit ASIN Count**: Default to 10 ASINs per search
2. **Reuse Data**: Cache Keepa responses for 24 hours
3. **Batch Requests**: Send multiple ASINs in single Keepa call

---

## Common Issues and Solutions

### Issue 1: "Keepa API returned no products"
**Cause**: Invalid ASINs or API token exhausted
**Solution**:
- Verify ASIN format (10 characters, alphanumeric)
- Check token balance at keepa.com
- Wait for token refresh (1 per minute)

### Issue 2: Missing `monthlySoldHistory`
**Cause**: Keepa doesn't track sales for all products
**Solution**:
- Set sales metrics to N/A
- Use alternative signals (review growth, BSR changes)
- Focus on products with complete data

### Issue 3: Timeout errors
**Cause**: Keepa API slow response (especially for multiple ASINs)
**Solution**:
- Increase timeout to 60-90 seconds
- Reduce ASIN batch size to 5
- Implement exponential backoff retry

---

## Testing Checklist

Before deploying changes:
- [ ] Test with 1 ASIN first (verify API connectivity)
- [ ] Test with 5 ASINs (verify batch processing)
- [ ] Test with invalid ASIN (verify error handling)
- [ ] Test with exhausted Keepa token (verify user messaging)
- [ ] Test with no search results (verify graceful degradation)
- [ ] Verify data quality (no NaN, no negative values)
- [ ] Check session state persistence across UI interactions

---

## Output Deliverables

**For Market Research Agent**:
1. DataFrame with 10-20 analyzed products
2. Summary statistics (avg rating, avg price, total market size)
3. Recommendations for further investigation (top 3-5 ASINs)

**For Next Workflow Stage**:
- Pass `search_results` DataFrame to Product Evaluation skill
- Pass top ASINs (score > 70) to Competitor Analysis skill
- Store raw Keepa data for historical trend analysis

---

## Integration Points

**Called by**: `app.py` main search function (lines 189-204)
**Calls**:
- `modules/keepa_analyzer_simple.py::search_and_analyze_products()`
- `modules/keepa_analyzer_simple.py::analyze_products_detailed()`

**Session State Dependencies**:
- Reads: `st.session_state.keepa_api_key`, `st.session_state.rainforest_api_key`
- Writes: `st.session_state.search_results`, `st.session_state.search_completed`
