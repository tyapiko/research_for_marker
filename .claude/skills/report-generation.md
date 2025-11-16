# Report Generation Skill

## Purpose
This skill standardizes the process of generating comprehensive analysis reports from collected data. Used by all agents to create consistent, actionable outputs for stakeholders.

## Prerequisites
- Completed product research (search_results DataFrame)
- Completed competitor analysis (review insights, SWOT)
- Product evaluation scores calculated
- Session state data available

## Report Types

### 1. Executive Summary Report
**Audience**: Decision makers who need quick insights
**Length**: 1-2 pages
**Delivery**: Markdown in Streamlit UI, exportable to PDF

#### Structure
```markdown
# Amazon商品参入分析レポート

## 📊 分析サマリー
- **検索キーワード**: [keyword]
- **分析日時**: 2025-01-16 14:30
- **分析商品数**: 10件
- **推奨商品数**: 3件(スコア60以上)

## 🎯 トップ3推奨商品

### 1位: [商品タイトル] (スコア: 85/100)
- **ASIN**: B09XYZ123
- **価格**: ¥2,403
- **月間売上**: 892個(成長率+36%)
- **評価**: ★3.2(改善余地大)
- **競合数**: 12社

**参入理由**:
1. 高い成長率(6ヶ月で+36%)
2. 低評価による改善機会(★3.2)
3. 適度な競合数(参入可能)

**改善ポイント**:
- 配送品質の向上(45件の指摘)
- スペック表記の正確化(32件の指摘)

**推奨戦略**:
- 目標価格: ¥2,500(競合より+4%)
- 目標評価: ★4.5以上
- 初期ロット: 100-150個

---

### 2位: [商品タイトル] (スコア: 73/100)
[同様の構造で2位の商品を記載]

---

### 3位: [商品タイトル] (スコア: 68/100)
[同様の構造で3位の商品を記載]

## ⚠️ 注意事項
- Keepa APIトークン制限により月間分析回数に制約あり
- レビューデータは取得時点のスナップショット(動的に変化)
- 参入判断には追加の市場調査を推奨

## 📈 次のステップ
1. トップ3商品のサンプル発注と品質確認
2. 詳細な収益シミュレーション
3. 初期在庫計画とキャッシュフロー試算
```

#### Implementation
```python
# app.py or modules/report_generator.py
def generate_executive_summary(search_results, keyword, top_n=3):
    """
    Args:
        search_results: DataFrame with scored products
        keyword: Search keyword used
        top_n: Number of top products to highlight

    Returns:
        Markdown-formatted executive summary
    """
    # Sort by score and get top N
    top_products = search_results.nlargest(top_n, "product_score")

    summary = f"""# Amazon商品参入分析レポート

## 📊 分析サマリー
- **検索キーワード**: {keyword}
- **分析日時**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
- **分析商品数**: {len(search_results)}件
- **推奨商品数**: {(search_results["product_score"] >= 60).sum()}件(スコア60以上)

## 🎯 トップ{top_n}推奨商品\n\n"""

    for idx, (_, product) in enumerate(top_products.iterrows(), 1):
        summary += generate_product_section(product, rank=idx)

    summary += generate_next_steps(top_products)

    return summary
```

---

### 2. Detailed Analysis Report
**Audience**: Analysts, product managers who need deep insights
**Length**: 5-10 pages
**Delivery**: Markdown + CSV exports + visualizations

#### Structure
```markdown
# 詳細分析レポート: [キーワード]

## 1. 市場概要

### 1.1 市場規模と成長性
- **総月間売上推定**: [sum of all products' sales]個
- **平均成長率**: [average growth rate]%
- **市場トレンド**: [growing/stable/declining]

### 1.2 価格分布
- **最安値**: ¥[min_price]
- **最高値**: ¥[max_price]
- **中央値**: ¥[median_price]
- **平均値**: ¥[mean_price]

[価格分布ヒストグラム画像]

### 1.3 品質分布
- **平均評価**: ★[mean_rating]
- **高評価商品(★4.5+)**: [count]件
- **低評価商品(★<3.5)**: [count]件

## 2. 商品別詳細分析

### 2.1 [商品1 タイトル]
#### 基本情報
- ASIN: [asin]
- 価格: ¥[price]
- 評価: ★[rating] ([review_count]件)
- BSR: [bsr] in [category]

#### スコア内訳
- **総合スコア**: [product_score]/100
  - 売上トレンド: [sales_trend_score]/40
  - 市場規模: [market_size_score]/30
  - 改善余地: [improvement_score]/20
  - 参入難易度: [entry_difficulty_score]/10

#### 売上推移
[6ヶ月間の売上グラフ]

#### 競合分析
- 競合数: [seller_count]社
- 市場シェア分布: [top seller share]
- 平均評価: ★[competitor_avg_rating]

#### レビュー分析(低評価★1-3)
**主要な問題点**:
1. 配送品質: 45件の指摘
   - 「箱が破損していた」「配送が遅い」
2. スペック不一致: 32件の指摘
   - 「サイズが説明と違う」「材質が期待外れ」

**改善提案**:
1. 堅牢な梱包材の使用(エアキャップ+二重箱)
2. 正確なサイズ表記と画像での寸法表示
3. 材質詳細の明記とサンプル写真の追加

#### 参入戦略
**推奨ポジショニング**:
- 価格: ¥2,500(競合平均+4%)
- 品質: ★4.5以上を目標
- 差別化: 「破損保証付き」「正確なサイズ保証」

**初期投資計画**:
- 初期ロット: 100個
- 仕入コスト: ¥1,200/個 × 100 = ¥120,000
- Amazon手数料: 15%(¥375/個)
- 目標利益率: 25%(¥625/個)

**リスク要因**:
- トップセラーが★4.3で強固な地位
- 季節性の可能性(要継続観察)

---

[商品2以降も同様の構造で記載]

## 3. 総合評価とアクションプラン

### 3.1 推奨順位
1. [商品1]: スコア85 - 即座に参入検討
2. [商品2]: スコア73 - 条件付きで参入検討
3. [商品3]: スコア68 - 小ロットテスト推奨

### 3.2 向こう3ヶ月のアクション
**Month 1**:
- [ ] トップ3商品のサンプル発注
- [ ] 品質確認と改善点リスト作成
- [ ] 詳細な収益シミュレーション

**Month 2**:
- [ ] 初期ロット発注(100個)
- [ ] 商品ページ作成(画像10枚、A+コンテンツ)
- [ ] レビュー獲得戦略の準備

**Month 3**:
- [ ] 販売開始
- [ ] 初期レビュー獲得(目標20件)
- [ ] 売上データ収集と分析

### 3.3 KPI設定
- **売上目標**: 月間50個(初月)→150個(3ヶ月後)
- **評価目標**: ★4.5以上(30件以上のレビュー)
- **利益率目標**: 25%以上
- **市場シェア目標**: Top 5セラー入り(6ヶ月後)

## 4. 付録

### 4.1 全商品一覧(CSV)
[search_results.csv へのリンク]

### 4.2 レビューサンプル
[collected_reviews.csv へのリンク]

### 4.3 データソース
- Keepa API: 価格・売上履歴
- RainforestAPI: 商品検索・レビュー
- Claude AI: レビュー分析
```

#### Implementation
```python
def generate_detailed_report(search_results, collected_reviews, analysis):
    """
    Generates comprehensive analysis report with all sections
    """
    report = []

    # Section 1: Market Overview
    report.append(generate_market_overview(search_results))

    # Section 2: Product-by-product analysis
    for _, product in search_results.iterrows():
        product_reviews = collected_reviews.get(product["asin"], [])
        product_analysis = analysis.get(product["asin"], {})
        report.append(generate_product_detail_section(
            product, product_reviews, product_analysis
        ))

    # Section 3: Action plan
    report.append(generate_action_plan(search_results))

    # Section 4: Appendix (CSV exports)
    report.append(generate_appendix(search_results, collected_reviews))

    return "\n\n".join(report)
```

---

### 3. Competitor Comparison Report
**Audience**: Product strategy team
**Length**: 2-3 pages per competitor pair
**Delivery**: Side-by-side comparison tables + charts

#### Structure
```markdown
# 競合比較レポート

## 対象商品
- **商品A**: [title A] (ASIN: [asin_a])
- **商品B**: [title B] (ASIN: [asin_b])

## スペック比較
| 項目 | 商品A | 商品B | 優位性 |
|------|-------|-------|--------|
| 価格 | ¥2,403 | ¥2,980 | A (¥577安) |
| 評価 | ★3.2 | ★4.1 | B |
| レビュー数 | 1,523 | 2,341 | B |
| 月間売上 | 892個 | 1,234個 | B |
| 成長率 | +36% | +12% | A |
| 競合数 | 12社 | 8社 | B(参入易) |

## 強み・弱み分析

### 商品A
**強み**:
- 高い成長率(市場拡大中)
- 価格競争力(¥577安)
- 改善余地大(★3.2)

**弱み**:
- 低評価(★3.2)
- レビュー数で劣る
- 競合やや多い(12社)

### 商品B
**強み**:
- 高評価(★4.1)
- 豊富なレビュー(2,341件)
- 安定した売上

**弱み**:
- 成長鈍化(+12%のみ)
- 価格が高め
- 改善余地少ない

## 参入難易度比較
| 要素 | 商品A | 商品B | 推奨 |
|------|-------|-------|------|
| 市場成長性 | 高 | 中 | A |
| 改善機会 | 多 | 少 | A |
| 既存品質 | 低 | 高 | A(追い越し易) |
| 参入障壁 | 中 | 低 | B |

**総合判定**: 商品Aを優先(成長市場+改善余地大)

## 推奨戦略
- **商品A**: 積極参入 - 品質改善で★4.5を狙う
- **商品B**: 様子見 - 市場成熟、差別化困難
```

#### Implementation
```python
def generate_competitor_comparison(product_a, product_b):
    """
    Creates side-by-side comparison of two products
    """
    comparison = {
        "specs": compare_specs(product_a, product_b),
        "strengths_weaknesses": analyze_swot(product_a, product_b),
        "entry_difficulty": compare_entry_barriers(product_a, product_b),
        "recommendation": generate_recommendation(product_a, product_b)
    }
    return format_comparison_report(comparison)
```

---

## Data Visualization

### Chart Types and Use Cases

#### 1. Price Distribution Histogram
**Use**: Show price range and clustering
```python
import matplotlib.pyplot as plt

def plot_price_distribution(search_results):
    plt.figure(figsize=(10, 6))
    plt.hist(search_results["price"], bins=20, edgecolor="black")
    plt.xlabel("Price (JPY)")
    plt.ylabel("Number of Products")
    plt.title("Price Distribution")
    plt.axvline(search_results["price"].median(), color="red", linestyle="--", label="Median")
    plt.legend()
    return plt
```

#### 2. Score Scatter Plot
**Use**: Visualize score vs. sales relationship
```python
def plot_score_vs_sales(search_results):
    plt.figure(figsize=(10, 6))
    plt.scatter(
        search_results["product_score"],
        search_results["current_sales"],
        s=search_results["review_count"] / 10,  # Size by review count
        alpha=0.6
    )
    plt.xlabel("Product Score")
    plt.ylabel("Monthly Sales")
    plt.title("Product Score vs. Sales Volume")
    return plt
```

#### 3. Sales Trend Line Chart
**Use**: Show historical sales trajectory
```python
def plot_sales_trend(monthly_sold_history):
    timestamps = monthly_sold_history[::2]  # Even indices
    sales = monthly_sold_history[1::2]      # Odd indices

    # Convert timestamps to dates
    dates = [datetime.fromtimestamp(ts * 60) for ts in timestamps]

    plt.figure(figsize=(12, 6))
    plt.plot(dates, sales, marker="o")
    plt.xlabel("Date")
    plt.ylabel("Monthly Sales")
    plt.title("Sales Trend (Last 6 Months)")
    plt.grid(True)
    return plt
```

#### 4. Radar Chart for Multi-Dimensional Comparison
**Use**: Compare products across all 4 scoring pillars
```python
import numpy as np
from matplotlib import pyplot as plt

def plot_product_radar(product):
    categories = ["Sales Trend", "Market Size", "Improvement", "Entry Ease"]
    values = [
        product["score_breakdown"]["sales_trend"] / 40 * 100,
        product["score_breakdown"]["market_size"] / 30 * 100,
        product["score_breakdown"]["improvement"] / 20 * 100,
        product["score_breakdown"]["entry_difficulty"] / 10 * 100
    ]

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]  # Close the circle
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    return fig
```

---

## Export Formats

### CSV Export
```python
def export_to_csv(search_results, filename="analysis_results.csv"):
    """
    Exports search results to CSV for Excel analysis
    """
    # Select columns for export
    export_columns = [
        "asin", "title", "price", "rating", "review_count",
        "bsr", "category", "seller_count",
        "current_sales", "sales_6mo_ago", "sales_growth",
        "product_score"
    ]

    search_results[export_columns].to_csv(
        filename,
        index=False,
        encoding="utf-8-sig"  # For Excel compatibility
    )
    return filename
```

### JSON Export (for API integration)
```python
def export_to_json(search_results, collected_reviews, analysis):
    """
    Structured JSON export for programmatic use
    """
    export_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "product_count": len(search_results),
            "keyword": st.session_state.get("last_keyword", "")
        },
        "products": []
    }

    for _, product in search_results.iterrows():
        export_data["products"].append({
            "asin": product["asin"],
            "title": product["title"],
            "score": product["product_score"],
            "metrics": {
                "price": product["price"],
                "rating": product["rating"],
                "monthly_sales": product["current_sales"]
            },
            "reviews": collected_reviews.get(product["asin"], []),
            "analysis": analysis.get(product["asin"], {})
        })

    return json.dumps(export_data, ensure_ascii=False, indent=2)
```

### PDF Export (future enhancement)
```python
# Using reportlab or weasyprint
def export_to_pdf(markdown_report, filename="report.pdf"):
    """
    Converts markdown report to PDF
    """
    # Implementation would use markdown → HTML → PDF pipeline
    # e.g., markdown → html (via markdown library)
    #       html → pdf (via weasyprint)
    pass  # To be implemented
```

---

## Streamlit UI Integration

### Display Implementation
```python
# app.py (lines 370-450 approximately)
def display_results(search_results, collected_reviews, analysis):
    """
    Renders interactive report in Streamlit UI
    """
    # Executive summary
    st.markdown("## 📊 分析サマリー")
    col1, col2, col3 = st.columns(3)
    col1.metric("分析商品数", len(search_results))
    col2.metric("推奨商品", (search_results["product_score"] >= 60).sum())
    col3.metric("平均スコア", f"{search_results['product_score'].mean():.1f}")

    # Top products
    st.markdown("## 🎯 推奨商品")
    for idx, (_, product) in enumerate(search_results.nlargest(5, "product_score").iterrows(), 1):
        with st.expander(f"{idx}位: {product['title']} (スコア: {product['product_score']})"):
            # Product details
            st.markdown(f"**ASIN**: {product['asin']}")
            st.markdown(f"**価格**: ¥{product['price']:,.0f}")
            st.markdown(f"**評価**: ★{product['rating']:.1f} ({product['review_count']}件)")

            # Score breakdown
            st.markdown("### スコア内訳")
            breakdown = product["score_breakdown"]
            st.progress(breakdown["sales_trend"] / 40, text=f"売上トレンド: {breakdown['sales_trend']}/40")
            st.progress(breakdown["market_size"] / 30, text=f"市場規模: {breakdown['market_size']}/30")
            st.progress(breakdown["improvement"] / 20, text=f"改善余地: {breakdown['improvement']}/20")
            st.progress(breakdown["entry_difficulty"] / 10, text=f"参入難易度: {breakdown['entry_difficulty']}/10")

            # Review insights (if available)
            if product["asin"] in analysis:
                st.markdown("### 主な改善ポイント")
                for category, data in analysis[product["asin"]]["categories"].items():
                    if data["count"] > 5:
                        st.markdown(f"- **{category}**: {data['count']}件の指摘")

    # Export buttons
    st.markdown("## 📥 エクスポート")
    col1, col2 = st.columns(2)
    with col1:
        csv_data = search_results.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="CSV形式でダウンロード",
            data=csv_data,
            file_name="analysis_results.csv",
            mime="text/csv"
        )
    with col2:
        json_data = export_to_json(search_results, collected_reviews, analysis)
        st.download_button(
            label="JSON形式でダウンロード",
            data=json_data,
            file_name="analysis_results.json",
            mime="application/json"
        )
```

---

## Error Handling

### Missing Data Gracefully
```python
def safe_report_generation(search_results):
    """
    Handles incomplete data scenarios
    """
    if search_results.empty:
        return "❌ データが不足しているためレポートを生成できません"

    # Check data quality
    complete_data_pct = (search_results["current_sales"] > 0).sum() / len(search_results) * 100

    warning = ""
    if complete_data_pct < 50:
        warning = f"""
        ⚠️ **データ品質警告**
        - {100-complete_data_pct:.0f}%の商品に不完全なデータ
        - レポートの信頼性が低下している可能性あり
        """

    return warning + generate_executive_summary(search_results)
```

---

## Performance Optimization

### Large Dataset Handling
```python
# For datasets >100 products
def paginated_report(search_results, page_size=20):
    """
    Generates report in chunks to avoid memory issues
    """
    total_pages = (len(search_results) + page_size - 1) // page_size

    for page in range(total_pages):
        start_idx = page * page_size
        end_idx = min((page + 1) * page_size, len(search_results))
        chunk = search_results.iloc[start_idx:end_idx]

        yield generate_report_section(chunk, page_num=page+1, total_pages=total_pages)
```

---

## Testing Checklist

- [ ] Generate report with 1 product
- [ ] Generate report with 10 products
- [ ] Generate report with 100+ products (performance test)
- [ ] Test with missing review data
- [ ] Test with missing sales data
- [ ] Test CSV export encoding (Japanese characters)
- [ ] Test JSON export structure validity
- [ ] Verify chart generation (matplotlib compatibility)

---

## Integration Points

**Called by**: All agents (Market Research, Data Analysis, Product Strategy)
**Calls**: Formatting utilities, export functions, visualization libraries

**Session State Dependencies**:
- Reads: `st.session_state.search_results`, `st.session_state.collected_reviews`, `st.session_state.analysis`
- Writes: Export files to disk, session state for report history
