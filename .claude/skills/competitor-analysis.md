# Competitor Analysis Skill

## Purpose
This skill provides standardized methods for analyzing competitor products through review analysis, price comparison, and strengths/weaknesses evaluation. Primarily used by the Data Analysis Agent.

## Prerequisites
- Completed Amazon Product Research (ASINs identified)
- RainforestAPI credentials for review collection
- Claude API credentials for AI-powered review analysis
- Product data from Keepa API

## Workflow Steps

### Step 1: Review Collection
**Objective**: Gather low-rated reviews (★1-3) to identify competitor weaknesses

**Implementation Strategy**:
```python
# modules/review_collector.py (lines 12-91)
# Two-tier fallback approach:

# PRIMARY: RainforestAPI reviews endpoint
params = {
    "api_key": RAINFOREST_API_KEY,
    "type": "reviews",
    "amazon_domain": "amazon.co.jp",
    "asin": target_asin,
    "review_stars": "one_star,two_star,three_star",  # Filter low ratings
    "page": str(page_num)
}

# FALLBACK: Product endpoint's top_reviews
params = {
    "type": "product",
    "asin": target_asin
}
# Then sort top_reviews by rating ascending
```

**Expected Review Format**:
```python
{
    "reviews": [
        {
            "id": "R3XYZ123456",
            "title": "レビュータイトル",
            "body": "レビュー本文...",
            "rating": 2,
            "date": {"raw": "2025年1月10日"},
            "verified_purchase": True,
            "helpful_votes": 15
        },
        # ... more reviews
    ]
}
```

**Data Filtering Rules**:
1. **Priority Ratings**: ★1 > ★2 > ★3 (lower = higher priority)
2. **Verified Purchases Only**: Filter `verified_purchase == True`
3. **Minimum Body Length**: Exclude reviews with <20 characters
4. **Pagination**: Collect up to 5 pages (max ~100 reviews per ASIN)
5. **Deduplication**: Remove duplicate review IDs

**Error Handling**:
- **503 Reviews Endpoint Error**: Auto-fallback to product endpoint
- **Empty Results**: Log warning, proceed with available reviews
- **Rate Limit (429)**: Wait 60s and retry up to 3 times
- **Invalid JSON**: Skip malformed reviews, log for debugging

**Data Validation**:
```python
def validate_review(review):
    required_fields = ["id", "body", "rating"]
    if not all(field in review for field in required_fields):
        return False
    if review["rating"] > 3:  # Only low ratings
        return False
    if len(review.get("body", "")) < 20:  # Minimum content
        return False
    return True
```

---

### Step 2: AI-Powered Review Analysis
**Objective**: Extract structured insights from reviews using Claude AI

**Implementation**:
```python
# modules/claude_analyzer.py (lines 12-89)
def analyze_reviews_with_claude(reviews, product_title):
    # Sample if too many reviews (token limit protection)
    if len(reviews) > 300:
        reviews = random.sample(reviews, 300)

    # Prepare prompt with review data
    prompt = f"""
    以下は「{product_title}」の低評価レビュー(★1-3)です。

    # レビューデータ
    {format_reviews_for_analysis(reviews)}

    # タスク
    1. 問題をカテゴリ別に分類
    2. 各問題の頻度と深刻度を評価
    3. 改善提案を生成
    """

    response = anthropic.Anthropic(api_key=CLAUDE_API_KEY).messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        temperature=0.3,  # Lower temp for analytical consistency
        messages=[{"role": "user", "content": prompt}]
    )
```

**Analysis Output Schema**:
```python
{
    "categories": {
        "delivery": {
            "count": 45,
            "severity": "high",  # high/medium/low
            "examples": ["配送が遅い", "箱が破損していた"],
            "improvement_priority": 1  # 1=highest
        },
        "specs": {
            "count": 32,
            "severity": "medium",
            "examples": ["サイズが説明と違う", "材質が期待外れ"],
            "improvement_priority": 2
        },
        "design": {...},
        "quality": {...},
        "service": {...},
        "price": {...}
    },
    "key_insights": [
        "配送品質が最大の課題(45件の指摘)",
        "製品スペックと実物の乖離が顕著",
        "価格に対する品質の不満が散見"
    ],
    "competitor_weaknesses": [
        {
            "weakness": "配送時の梱包が不十分",
            "opportunity": "堅牢な梱包材を使用することで差別化可能",
            "estimated_impact": "high"
        },
        # ... more weaknesses
    ]
}
```

**Token Management**:
- Review sampling: Max 300 reviews per analysis
- Character limit per review: 500 chars (truncate if longer)
- Total input tokens: ~15,000 (leaves room for response)
- Response max_tokens: 4,096

**Error Handling**:
- **Token Limit Exceeded**: Reduce sample size to 200, retry
- **API Timeout**: Increase timeout to 120s
- **Invalid Response**: Return partial analysis with warning
- **No Reviews Available**: Return empty analysis structure

---

### Step 3: Price and Sales Comparison
**Objective**: Benchmark target product against competitors

**Data Sources**:
```python
# From Keepa API data (already collected in Step 1)
competitor_data = {
    "price_range": {
        "min": 1980,
        "max": 4980,
        "avg": 2980,
        "median": 2850,
        "target_product": 2403
    },
    "sales_comparison": {
        "top_seller_monthly": 5234,
        "avg_monthly": 1523,
        "target_product": 892,
        "percentile_rank": 45  # Target is better than 45% of competitors
    },
    "rating_comparison": {
        "top_rated": 4.5,
        "avg_rating": 3.8,
        "target_product": 3.2,
        "percentile_rank": 25
    }
}
```

**Calculation Methods**:
```python
def calculate_competitive_position(target, competitors):
    """
    Args:
        target: Dict with price, sales, rating for target product
        competitors: List of dicts for competing products

    Returns:
        Dict with percentile ranks and competitive gaps
    """
    metrics = {}

    # Price competitiveness (lower is better)
    all_prices = [c["price"] for c in competitors] + [target["price"]]
    price_percentile = sum(1 for p in all_prices if p > target["price"]) / len(all_prices) * 100
    metrics["price_competitiveness"] = {
        "percentile": price_percentile,
        "vs_avg": target["price"] - np.mean([c["price"] for c in competitors]),
        "recommendation": "価格を下げる余地あり" if price_percentile > 70 else "価格は競争力あり"
    }

    # Sales performance (higher is better)
    all_sales = [c["monthly_sales"] for c in competitors] + [target["monthly_sales"]]
    sales_percentile = sum(1 for s in all_sales if s < target["monthly_sales"]) / len(all_sales) * 100

    # Quality perception (rating, higher is better)
    all_ratings = [c["rating"] for c in competitors] + [target["rating"]]
    rating_percentile = sum(1 for r in all_ratings if r < target["rating"]) / len(all_ratings) * 100

    return metrics
```

**Visualization Data Prep**:
```python
# Prepare data for Streamlit charts
comparison_df = pd.DataFrame({
    "Product": ["Target"] + [f"Competitor {i+1}" for i in range(len(competitors))],
    "Price": [target["price"]] + [c["price"] for c in competitors],
    "Monthly Sales": [target["sales"]] + [c["sales"] for c in competitors],
    "Rating": [target["rating"]] + [c["rating"] for c in competitors],
    "Score": [target["score"]] + [c["score"] for c in competitors]
})
```

---

### Step 4: Strengths and Weaknesses Matrix
**Objective**: Generate SWOT-style analysis for entry decision

**Analysis Framework**:
```python
def generate_swot_analysis(target_asin, competitor_reviews, price_comparison):
    swot = {
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": []
    }

    # STRENGTHS: What competitors do well (to match or exceed)
    if competitor_reviews["avg_rating"] > 4.0:
        swot["strengths"].append({
            "factor": "高い顧客満足度",
            "evidence": f"平均評価{competitor_reviews['avg_rating']}",
            "our_target": "★4.5以上を目指す"
        })

    # WEAKNESSES: Common competitor problems (our opportunities)
    for category, data in competitor_reviews["categories"].items():
        if data["count"] > 10 and data["severity"] in ["high", "medium"]:
            swot["weaknesses"].append({
                "factor": category,
                "frequency": data["count"],
                "our_improvement": data["improvement_suggestion"]
            })

    # OPPORTUNITIES: Market gaps
    if price_comparison["avg_price"] > 3000 and competitor_reviews["price_complaints"] > 20:
        swot["opportunities"].append({
            "gap": "高価格帯での品質不満",
            "strategy": "¥2,500-2,800で高品質品を投入",
            "estimated_share": "15-20%"
        })

    # THREATS: Entry barriers
    if competitor_reviews["top_seller_sales"] > 10000:
        swot["threats"].append({
            "risk": "支配的なトップセラーの存在",
            "mitigation": "ニッチセグメント(例:女性向け)に特化"
        })

    return swot
```

**Output Format for Reporting**:
```markdown
## 競合分析サマリー

### 主要な弱点(参入機会)
1. **配送品質**: 45件の低評価レビュー → 梱包改善で差別化
2. **スペック不一致**: 32件の指摘 → 正確な商品説明で信頼構築
3. **価格対品質**: 平均価格¥2,980で★3.8 → ¥2,500で★4.5+を狙う

### 競合の強み(マッチすべき要素)
- 豊富なバリエーション(5色展開)
- 迅速な発送(Prime対応)
- 詳細な商品画像(10枚以上)

### 推奨戦略
1. **差別化ポイント**: 堅牢な梱包 + 正確なサイズ表記
2. **価格設定**: ¥2,403(競合平均より20%安)
3. **初期投資**: レビュー獲得キャンペーン(50件目標)
```

---

## Performance Considerations

### Review Collection Limits
- **Free RainforestAPI**: ~100 requests/hour
  - 1 ASIN × 5 pages = 5 requests
  - Max ~20 ASINs per hour
- **Optimization**: Prioritize top-scoring products only

### Claude API Costs
- **Per Analysis**: ~$0.10-0.20 (15K input + 4K output tokens)
- **Budget Management**: Limit to top 5 ASINs per session
- **Caching**: Store analyses for 7 days, reuse when possible

---

## Common Issues and Solutions

### Issue 1: "Reviews endpoint returns 503"
**Cause**: RainforestAPI reviews endpoint instability (Nov 2025)
**Solution**:
- Automatically fallback to `product` endpoint `top_reviews`
- Accept limited review count (10-20 vs 100+)
- Prioritize quality over quantity in analysis

### Issue 2: Insufficient low-rated reviews
**Cause**: Highly rated products have few ★1-3 reviews
**Solution**:
- Expand to ★4 reviews for these products
- Focus on "critical" reviews (helpful_votes > 10)
- Analyze review trends over time

### Issue 3: Claude analysis lacks specificity
**Cause**: Generic prompt or insufficient review samples
**Solution**:
- Include product category context in prompt
- Provide at least 30 reviews per analysis
- Use temperature=0.3 for consistency

---

## Testing Checklist

- [ ] Test with ASIN having 100+ low-rated reviews
- [ ] Test with ASIN having <10 low-rated reviews
- [ ] Test fallback from reviews to product endpoint
- [ ] Verify Claude analysis quality (3 sample products)
- [ ] Check price comparison calculations (edge cases: 1 competitor, 50 competitors)
- [ ] Validate SWOT generation completeness

---

## Output Deliverables

**For Data Analysis Agent**:
1. Review analysis JSON with categorized problems
2. Price/sales comparison metrics
3. SWOT matrix for top 3-5 products

**For Product Strategy Agent**:
- Prioritized list of improvement opportunities
- Competitive positioning recommendations
- Entry barrier assessment

**For Report Generation**:
- Formatted markdown summaries
- Visualization-ready DataFrames
- Key insights and action items

---

## Integration Points

**Called by**: `app.py` review collection section (lines 319-365)
**Calls**:
- `modules/review_collector.py::collect_reviews()`
- `modules/claude_analyzer.py::analyze_reviews_with_claude()`

**Session State Dependencies**:
- Reads: `st.session_state.search_results`, `st.session_state.rainforest_api_key`, `st.session_state.claude_api_key`
- Writes: `st.session_state.collected_reviews`, `st.session_state.analysis`
