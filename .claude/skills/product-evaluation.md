# Product Evaluation Skill

## Purpose
This skill defines standardized criteria and scoring methodology for evaluating whether to enter a specific Amazon product market. Primarily used by the Product Strategy Agent.

## Prerequisites
- Completed Amazon Product Research (Keepa data collected)
- Completed Competitor Analysis (review insights available)
- Historical sales data from `monthlySoldHistory`
- Competitor metrics (seller count, ratings distribution)

## Evaluation Framework

### 4-Pillar Scoring System (100 Points Total)

Our product scoring algorithm evaluates market entry potential across 4 key dimensions:

```
Total Score = Sales Trend (40) + Market Size (30) + Improvement Potential (20) + Entry Difficulty (10)
```

**Decision Thresholds**:
- **80-100 points**: 🟢 Excellent opportunity - High priority
- **60-79 points**: 🟡 Good opportunity - Worth considering
- **40-59 points**: 🟠 Moderate opportunity - Requires further analysis
- **0-39 points**: 🔴 Poor opportunity - Not recommended

---

## Pillar 1: Sales Trend Score (40 Points)
**Rationale**: Growing markets are easier to enter than declining ones

### Calculation Method
```python
# modules/keepa_analyzer_simple.py (lines 327-342)
def calculate_sales_trend_score(current_sales, sales_6mo_ago):
    """
    Args:
        current_sales: Monthly sales volume (current month)
        sales_6mo_ago: Monthly sales volume (6 months prior)

    Returns:
        Score (0-40) based on growth rate
    """
    if sales_6mo_ago == 0 or sales_6mo_ago is None:
        return 0  # No historical data

    growth_rate = (current_sales - sales_6mo_ago) / sales_6mo_ago * 100

    # Scoring tiers
    if growth_rate >= 100:    # 2x growth or more
        return 40
    elif growth_rate >= 50:   # 50-100% growth
        return 30
    elif growth_rate >= 20:   # 20-50% growth
        return 20
    elif growth_rate >= 0:    # 0-20% growth
        return 10
    else:                     # Declining market
        return 0
```

### Data Source
```python
# Extract from Keepa monthlySoldHistory
# Format: [timestamp1, sales1, timestamp2, sales2, ...]
monthly_sold = product.get("monthlySoldHistory", [])
if monthly_sold and len(monthly_sold) >= 2:
    current_sales = monthly_sold[-1]  # Most recent
    sales_6mo_ago = monthly_sold[-13] if len(monthly_sold) >= 14 else monthly_sold[1]
```

### Edge Cases
- **No historical data**: Score = 0, flag as "データ不足"
- **Negative sales values**: Filter out before calculation
- **Extreme growth (>1000%)**: Cap at 40 points, flag for manual review
- **Seasonal products**: Note potential seasonality in comments

---

## Pillar 2: Market Size Score (30 Points)
**Rationale**: Larger markets support more sellers and offer better revenue potential

### Calculation Method
```python
def calculate_market_size_score(current_monthly_sales):
    """
    Args:
        current_monthly_sales: Current month's sales volume

    Returns:
        Score (0-30) based on market size tiers
    """
    if current_monthly_sales >= 5000:
        return 30  # Very large market
    elif current_monthly_sales >= 3000:
        return 25  # Large market
    elif current_monthly_sales >= 1000:
        return 20  # Medium market
    elif current_monthly_sales >= 500:
        return 15  # Small market
    elif current_monthly_sales >= 100:
        return 10  # Very small market
    else:
        return 5   # Niche market
```

### Market Size Categories
| Monthly Sales | Category | Score | Entry Strategy |
|--------------|----------|-------|----------------|
| 5,000+ | Very Large | 30 | Competitive, needs differentiation |
| 3,000-4,999 | Large | 25 | Good demand, moderate competition |
| 1,000-2,999 | Medium | 20 | Balanced opportunity |
| 500-999 | Small | 15 | Lower competition, test market |
| 100-499 | Very Small | 10 | Niche play, validate demand first |
| <100 | Micro | 5 | High risk, avoid unless unique |

### Validation Rules
- **Sales = 0**: Verify data quality, may indicate new product
- **Sales > 50,000/month**: Flag as "mega market", high barrier to entry
- **BSR correlation**: Cross-check with Best Seller Rank for consistency

---

## Pillar 3: Improvement Potential Score (20 Points)
**Rationale**: Lower customer satisfaction = more room for differentiation

### Calculation Method
```python
def calculate_improvement_score(average_rating, review_count):
    """
    Args:
        average_rating: Product rating (1.0-5.0)
        review_count: Total number of reviews

    Returns:
        Score (0-20) based on improvement opportunity
    """
    # Require minimum review count for reliability
    if review_count < 10:
        return 0  # Insufficient data

    # Scoring based on rating gaps
    if average_rating < 3.5:
        return 20  # High improvement potential
    elif average_rating < 3.9:
        return 15  # Good improvement potential
    elif average_rating < 4.2:
        return 10  # Moderate improvement potential
    elif average_rating < 4.5:
        return 5   # Low improvement potential
    else:
        return 0   # Product already excellent
```

### Rating-Based Insights
| Rating Range | Score | Interpretation | Action |
|-------------|-------|----------------|--------|
| <3.5 | 20 | Major problems exist | Focus on core issues |
| 3.5-3.9 | 15 | Noticeable issues | Address top complaints |
| 4.0-4.2 | 10 | Minor issues | Incremental improvements |
| 4.3-4.5 | 5 | High quality | Differentiate on features |
| >4.5 | 0 | Excellent | Hard to compete on quality |

### Advanced Metrics
```python
# Enhanced scoring with review analysis
def enhanced_improvement_score(rating, review_count, low_rating_percentage):
    """
    Args:
        low_rating_percentage: % of 1-3 star reviews
    """
    base_score = calculate_improvement_score(rating, review_count)

    # Boost score if many low-rated reviews (actionable feedback)
    if low_rating_percentage > 30:
        base_score = min(base_score + 5, 20)

    return base_score
```

---

## Pillar 4: Entry Difficulty Score (10 Points)
**Rationale**: Fewer competitors = easier market entry

### Calculation Method
```python
def calculate_entry_difficulty_score(seller_count):
    """
    Args:
        seller_count: Number of active sellers (COUNT_NEW from Keepa)

    Returns:
        Score (0-10) based on competition level
    """
    if seller_count <= 3:
        return 10  # Blue ocean - very few sellers
    elif seller_count <= 10:
        return 7   # Low competition
    elif seller_count <= 30:
        return 5   # Moderate competition
    elif seller_count <= 100:
        return 3   # High competition
    else:
        return 0   # Red ocean - saturated market
```

### Competition Analysis Framework
| Seller Count | Category | Score | Strategy Recommendation |
|-------------|----------|-------|-------------------------|
| 1-3 | Blue Ocean | 10 | First-mover advantage possible |
| 4-10 | Low Competition | 7 | Good entry opportunity |
| 11-30 | Moderate | 5 | Need clear differentiation |
| 31-100 | High | 3 | Strong brand/quality required |
| 100+ | Red Ocean | 0 | Avoid unless niche angle exists |

### Additional Factors
```python
# Consider seller quality, not just quantity
def adjusted_entry_score(seller_count, top_seller_rating, top_seller_share):
    """
    Args:
        top_seller_rating: Rating of #1 seller
        top_seller_share: % of sales from #1 seller
    """
    base_score = calculate_entry_difficulty_score(seller_count)

    # Penalty if dominant seller exists (>50% market share)
    if top_seller_share > 50:
        base_score = max(base_score - 3, 0)

    # Bonus if top seller has low rating (vulnerable)
    if top_seller_rating < 4.0:
        base_score = min(base_score + 2, 10)

    return base_score
```

---

## Composite Evaluation

### Score Aggregation
```python
def calculate_total_score(sales_trend, market_size, improvement, entry_difficulty):
    """
    Combines all pillar scores into final product score
    """
    total = sales_trend + market_size + improvement + entry_difficulty

    # Validation: ensure each pillar contributes
    if sales_trend == 0 and market_size == 0:
        total = 0  # Insufficient data to evaluate

    return min(total, 100)  # Cap at 100
```

### Score Interpretation Matrix
```python
SCORE_BANDS = {
    (80, 100): {
        "label": "優良",
        "color": "green",
        "recommendation": "積極的に参入を検討",
        "next_steps": [
            "詳細なレビュー分析を実施",
            "サンプル発注と品質確認",
            "初期在庫計画(100-200個)を策定"
        ]
    },
    (60, 79): {
        "label": "良好",
        "color": "yellow",
        "recommendation": "条件付きで参入を検討",
        "next_steps": [
            "競合との差別化ポイントを明確化",
            "小ロット(50個)でテスト販売",
            "レビュー獲得戦略を準備"
        ]
    },
    (40, 59): {
        "label": "中程度",
        "color": "orange",
        "recommendation": "慎重に検討が必要",
        "next_steps": [
            "市場トレンドの継続監視(3ヶ月)",
            "ニッチセグメントの可能性調査",
            "他の候補商品と比較検討"
        ]
    },
    (0, 39): {
        "label": "低評価",
        "color": "red",
        "recommendation": "参入は推奨しない",
        "next_steps": [
            "他の商品カテゴリを探索",
            "市場調査の範囲を拡大"
        ]
    }
}
```

---

## Advanced Filtering Criteria

### Post-Search Filters (app.py lines 208-266)
Apply these filters AFTER initial scoring to refine results:

#### 1. Price Range Filter
```python
if price_filter_enabled:
    if not (price_min <= product["price"] <= price_max):
        continue  # Skip product
```

#### 2. BSR (Best Seller Rank) Filter
```python
if bsr_filter_enabled:
    if product["bsr"] == -1 or product["bsr"] > bsr_max:
        continue  # Skip unranked or low-ranked products
```

#### 3. Rating Filter
```python
if rating_filter_enabled:
    if product["rating"] > rating_max:
        continue  # Want lower ratings (more improvement potential)
```

#### 4. Growth Trend Filter
```python
if growth_filter_enabled:
    if product["sales_growth"] < growth_min:
        continue  # Skip declining/stagnant markets
```

### Filter Interaction Logic
```
Initial Results (10-20 products)
    ↓
Apply Price Filter → Remaining: ~8-15 products
    ↓
Apply BSR Filter → Remaining: ~5-10 products
    ↓
Apply Rating Filter → Remaining: ~3-8 products
    ↓
Apply Growth Filter → Final: ~2-5 products
    ↓
Display Filtered Results (sorted by product_score)
```

---

## Validation and Quality Checks

### Data Completeness Check
```python
def validate_product_data(product):
    """
    Ensures minimum data quality before scoring
    """
    required_fields = {
        "asin": str,
        "price": (int, float),
        "rating": (int, float),
        "review_count": int
    }

    for field, expected_type in required_fields.items():
        if field not in product:
            return False, f"Missing field: {field}"
        if not isinstance(product[field], expected_type):
            return False, f"Invalid type for {field}"

    # Value range checks
    if product["price"] <= 0:
        return False, "Invalid price (<=0)"
    if not (1.0 <= product["rating"] <= 5.0):
        return False, "Rating out of range"

    return True, "OK"
```

### Score Reasonableness Check
```python
def validate_score_distribution(results_df):
    """
    Flags unusual scoring patterns
    """
    warnings = []

    # Check 1: All scores too similar
    if results_df["product_score"].std() < 5:
        warnings.append("スコアの分散が小さすぎます(データ品質を確認)")

    # Check 2: All scores very high or very low
    avg_score = results_df["product_score"].mean()
    if avg_score > 85:
        warnings.append("平均スコアが高すぎます(フィルタ条件を見直し)")
    elif avg_score < 20:
        warnings.append("平均スコアが低すぎます(検索キーワードを変更)")

    # Check 3: Missing sales data for most products
    no_sales_pct = (results_df["current_sales"] == 0).sum() / len(results_df) * 100
    if no_sales_pct > 50:
        warnings.append(f"{no_sales_pct:.0f}%の商品に売上データがありません")

    return warnings
```

---

## Output Formats

### For UI Display (Streamlit)
```python
# modules/keepa_analyzer_simple.py (lines 384-401)
results = {
    "asin": asin,
    "title": title,
    "price": price,
    "rating": rating,
    "review_count": review_count,
    "bsr": bsr,
    "category": category,
    "seller_count": seller_count,
    "current_sales": current_sales,
    "sales_6mo_ago": sales_6mo_ago,
    "sales_growth": sales_growth,
    "product_score": total_score,
    # Score breakdown for transparency
    "score_breakdown": {
        "sales_trend": sales_trend_score,
        "market_size": market_size_score,
        "improvement": improvement_score,
        "entry_difficulty": entry_difficulty_score
    }
}
```

### For CSV Export
```csv
ASIN,Title,Price,Rating,Reviews,BSR,Category,Sellers,Current Sales,Sales 6mo Ago,Growth %,Total Score,Trend Score,Size Score,Improvement Score,Difficulty Score
B09XYZ123,商品タイトル,2403,3.2,1523,8234,Home,12,892,654,36.4,73,20,20,20,7
```

### For API Response
```json
{
  "evaluation_results": [
    {
      "asin": "B09XYZ123",
      "score": 73,
      "recommendation": "良好",
      "confidence": "high",
      "reasoning": {
        "strengths": ["売上成長率36%", "改善余地大(★3.2)"],
        "concerns": ["競合12社", "BSRランクやや低"],
        "verdict": "差別化ポイントを明確にすれば参入価値あり"
      }
    }
  ]
}
```

---

## Performance Benchmarks

### Scoring Speed
- Per product: <10ms (pure calculation)
- Batch (10 products): <100ms
- With filtering: <200ms total

### Memory Usage
- Results DataFrame: ~50KB per 100 products
- Session state: ~500KB for full analysis session

---

## Common Issues and Solutions

### Issue 1: All scores are low (<40)
**Possible Causes**:
- Poor keyword selection (irrelevant products)
- Insufficient Keepa data coverage
- All products in mature/declining markets

**Solutions**:
- Try different search keywords
- Expand to related categories
- Adjust scoring thresholds for specific niches

### Issue 2: Sales data missing for many products
**Cause**: Keepa doesn't track all products
**Solution**:
- Use BSR as proxy for sales trends
- Focus on products with complete data
- Document data limitations in report

### Issue 3: Inconsistent scores across similar products
**Cause**: Data quality variations
**Solution**:
- Implement confidence scoring
- Flag products with incomplete data
- Normalize scores within category

---

## Testing Checklist

- [ ] Test with high-score product (80+)
- [ ] Test with low-score product (<30)
- [ ] Test with missing sales data
- [ ] Test with extreme values (price=¥100,000, sales=50,000/mo)
- [ ] Verify filter combinations don't eliminate all results
- [ ] Validate score breakdown sums to total

---

## Integration Points

**Called by**: `app.py` after Keepa data retrieval (line 327)
**Calls**: `modules/keepa_analyzer_simple.py::calculate_sales_trend_score()`, etc.

**Session State Dependencies**:
- Reads: `st.session_state.search_results` (raw Keepa data)
- Writes: `st.session_state.search_results` (with scores), `st.session_state.score_warnings`
