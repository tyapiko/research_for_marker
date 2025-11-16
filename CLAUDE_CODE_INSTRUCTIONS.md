# 🏋️ Amazon競合分析ツール for フィットネス機器

## 📋 プロジェクト概要

健康フィットネス機器を販売する企業向けの、Amazon市場分析＆商品企画支援ツール。
競合商品の売れ行きトレンドとレビューをAIで分析し、差別化された新商品開発を支援する。

### 🎯 主な機能

1. **市場トレンド検索**: キーワードで急成長中のフィットネス商品をランキング表示
2. **レビュー一括取得**: 競合商品の直近レビューを指定件数で収集
3. **AI分析**: Claude Sonnet 4.5でプロセス別（配送・仕様・デザイン等）に問題点を分析
4. **レポート出力**: CSV/Excel形式でデータ出力、改善提案を可視化

---

## 🛠️ 技術スタック

- **フロントエンド**: Streamlit (Pythonベースの対話型Webアプリ)
- **データ分析**: pandas, numpy, plotly
- **外部API**:
  - Keepa API: Amazon市場データ（ランキング推移・価格・レビュー数）
  - RainforestAPI: Amazonレビュー全文取得
  - Claude API (Anthropic): AI分析・提案生成

---

## 📁 プロジェクト構成

```
market/
├── app.py                      # メインアプリケーション
├── requirements.txt            # 依存パッケージ
├── .env                        # API鍵設定（gitignoreに追加）
├── .gitignore
├── modules/
│   ├── __init__.py
│   ├── keepa_analyzer.py      # Keepa市場分析モジュール
│   ├── review_collector.py    # Rainforestレビュー取得モジュール
│   └── claude_analyzer.py     # Claude AI分析モジュール
└── README.md                   # プロジェクト説明
```

---

## 📝 実装手順

### Step 1: 初期セットアップ

#### 1.1 依存パッケージのインストール

**requirements.txt** を作成:

```txt
streamlit==1.35.0
pandas==2.2.0
numpy==1.26.0
plotly==5.18.0
python-keepa==1.3.6
anthropic==0.25.0
requests==2.31.0
python-dotenv==1.0.0
openpyxl==3.1.2
```

インストールコマンド:
```bash
pip install -r requirements.txt
```

#### 1.2 環境変数設定

**.env** ファイルを作成（API鍵は後で設定）:

```env
KEEPA_API_KEY=your_keepa_key_here
RAINFOREST_API_KEY=your_rainforest_key_here
CLAUDE_API_KEY=your_claude_key_here
```

**.gitignore** を作成:

```
.env
__pycache__/
*.pyc
.streamlit/
```

---

### Step 2: モジュール実装

#### 2.1 modules/__init__.py

```python
# 空ファイルでOK（Pythonパッケージとして認識させる）
```

#### 2.2 modules/keepa_analyzer.py

```python
"""
Keepa APIを使用してAmazon市場のトレンド分析を行うモジュール
"""
import keepa
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class KeepaAnalyzer:
    """Keepa API分析クラス"""
    
    def __init__(self, api_key):
        """
        初期化
        
        Args:
            api_key (str): Keepa APIキー
        """
        self.api = keepa.Keepa(api_key)
    
    def search_trending_products(self, keyword, min_reviews=100, min_growth=0.2, max_results=20):
        """
        キーワードで売れ筋商品を検索
        
        Args:
            keyword (str): 検索キーワード（例: "ヨガマット"）
            min_reviews (int): 最小レビュー数フィルタ
            min_growth (float): 最小成長率フィルタ（0.2 = 20%）
            max_results (int): 最大結果数
            
        Returns:
            pd.DataFrame: 急成長商品のデータフレーム
        """
        try:
            # Keepaで商品検索
            products = self.api.query(
                keyword,
                stats=180,  # 過去180日のデータ
                domain='com'  # amazon.com
            )
            
            results = []
            for product in products:
                # レビュー数フィルタ
                if product.get('reviewCount', 0) < min_reviews:
                    continue
                
                # BSR（ベストセラーランキング）推移を取得
                bsr_history = product['data'].get('SALES_rank', [])
                if len(bsr_history) < 60:  # 最低60日分のデータが必要
                    continue
                
                # 成長率計算（ランキングが下がる = 売上上昇）
                recent_avg = np.mean(bsr_history[-30:]) if len(bsr_history) >= 30 else None
                past_avg = np.mean(bsr_history[-90:-60]) if len(bsr_history) >= 90 else None
                
                if recent_avg and past_avg and past_avg > 0:
                    growth_rate = (past_avg - recent_avg) / past_avg
                    
                    if growth_rate >= min_growth:
                        # 日付配列を生成（KeepaTime形式からdatetimeに変換）
                        keepa_time_minutes = product['data'].get('SALES_time', [])
                        dates = [
                            datetime(2011, 1, 1) + timedelta(minutes=int(t))
                            for t in keepa_time_minutes
                        ]
                        
                        results.append({
                            'asin': product['asin'],
                            'title': product.get('title', 'N/A'),
                            'growth_rate': growth_rate,
                            'review_count': product.get('reviewCount', 0),
                            'rating': product.get('rating', 0) / 10,  # Keepaは10倍スケール
                            'price': product['data']['NEW'][-1] / 100 if 'NEW' in product['data'] else 0,
                            'current_rank': bsr_history[-1] if bsr_history else 0,
                            'bsr_history': bsr_history,
                            'bsr_history_dates': dates
                        })
            
            df = pd.DataFrame(results)
            if len(df) == 0:
                return pd.DataFrame()
            
            return df.sort_values('growth_rate', ascending=False).head(max_results)
        
        except Exception as e:
            raise Exception(f"Keepa検索エラー: {str(e)}")
```

#### 2.3 modules/review_collector.py

```python
"""
RainforestAPIを使用してAmazonレビューを取得するモジュール
"""
import requests
import time
from typing import List, Dict, Callable, Optional

class ReviewCollector:
    """RainforestAPI レビュー取得クラス"""
    
    def __init__(self, api_key):
        """
        初期化
        
        Args:
            api_key (str): RainforestAPI APIキー
        """
        self.api_key = api_key
        self.base_url = 'https://api.rainforestapi.com/request'
    
    def collect_reviews(
        self, 
        asin: str, 
        target_count: int, 
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        指定ASINの直近レビューを取得
        
        Args:
            asin (str): Amazon商品ID (ASIN)
            target_count (int): 取得目標件数
            progress_callback (callable): プログレスバー更新用コールバック関数
            
        Returns:
            List[Dict]: レビューデータのリスト
        """
        reviews = []
        page = 1
        
        # プログレスバー初期化
        if progress_callback:
            progress_bar = progress_callback(0)
        
        try:
            while len(reviews) < target_count:
                params = {
                    'api_key': self.api_key,
                    'type': 'reviews',
                    'amazon_domain': 'amazon.com',
                    'asin': asin,
                    'page': page,
                    'sort_by': 'recent'  # 直近順にソート
                }
                
                response = requests.get(self.base_url, params=params, timeout=30)
                
                if response.status_code != 200:
                    print(f"警告: ページ{page}の取得失敗 (Status: {response.status_code})")
                    break
                
                data = response.json()
                
                # レビューデータを抽出
                for review in data.get('reviews', []):
                    if len(reviews) >= target_count:
                        break
                    
                    reviews.append({
                        'asin': asin,
                        'review_id': review.get('id', ''),
                        'rating': review.get('rating', 0),
                        'title': review.get('title', ''),
                        'body': review.get('body', ''),
                        'verified_purchase': review.get('verified_purchase', False),
                        'date': review.get('date', {}).get('raw', ''),
                        'helpful_votes': review.get('helpful_votes', 0),
                        'images': len(review.get('images', []))
                    })
                    
                    # プログレス更新
                    if progress_callback:
                        progress_bar.progress(len(reviews) / target_count)
                
                # 次ページがない場合は終了
                if not data.get('pagination', {}).get('next_page_link'):
                    break
                
                page += 1
                time.sleep(0.5)  # レート制限対策
            
            return reviews
        
        except Exception as e:
            raise Exception(f"レビュー取得エラー: {str(e)}")
```

#### 2.4 modules/claude_analyzer.py

```python
"""
Claude APIを使用してレビューを分析するモジュール
"""
import anthropic
import json
import pandas as pd
from typing import Dict

class ClaudeAnalyzer:
    """Claude AI分析クラス"""
    
    def __init__(self, api_key):
        """
        初期化
        
        Args:
            api_key (str): Anthropic Claude APIキー
        """
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def analyze_reviews(self, reviews_df: pd.DataFrame) -> Dict:
        """
        レビューをプロセス別に分析
        
        Args:
            reviews_df (pd.DataFrame): レビューデータフレーム
            
        Returns:
            Dict: 分析結果（カテゴリ別問題、改善提案、新商品コンセプト）
        """
        # 低評価レビューを抽出（★3以下）
        negative_reviews = reviews_df[reviews_df['rating'] <= 3]
        
        if len(negative_reviews) == 0:
            return {
                "カテゴリ別問題": {},
                "改善提案": [],
                "新商品コンセプト": {}
            }
        
        # サンプリング（最大300件、トークン制限対策）
        sampled = negative_reviews.sample(
            n=min(300, len(negative_reviews))
        )
        
        # レビューテキストを整形
        review_text = "\n\n---\n\n".join([
            f"★{row['rating']} | {row['date']}\n"
            f"タイトル: {row['title']}\n"
            f"本文: {row['body']}"
            for _, row in sampled.iterrows()
        ])
        
        prompt = f"""
あなたはフィットネス機器メーカーの商品企画コンサルタントです。
競合商品の低評価レビューを分析し、**プロセス別**に問題点を整理してください。

## 分析対象レビュー（{len(sampled)}件）
{review_text}

## 分析指示
以下のカテゴリに分類して問題点を抽出してください：

1. **配送・梱包**: 配送遅延、破損、梱包不良など
2. **商品仕様**: サイズ、重量、素材、機能不足など
3. **デザイン**: 見た目、色、使いやすさなど
4. **品質・耐久性**: 故障、劣化、不良品など
5. **サービス**: 返品対応、カスタマーサポートなど
6. **価格・コスパ**: 価格に見合わない、高すぎるなど

## 出力JSON形式
```json
{{
  "カテゴリ別問題": {{
    "配送・梱包": [
      {{"問題": "具体的な問題内容", "頻度": "高", "具体例": "レビューからの引用"}}
    ],
    "商品仕様": [...],
    "デザイン": [...],
    "品質・耐久性": [...],
    "サービス": [...],
    "価格・コスパ": [...]
  }},
  "改善提案": [
    {{
      "提案": "具体的な改善案",
      "解決する問題": "対応するカテゴリと問題",
      "実現可能性": "高",
      "差別化ポイント": "競合との違い",
      "想定コスト影響": "コスト増減の見込み"
    }}
  ],
  "新商品コンセプト": {{
    "商品名案": "魅力的な商品名",
    "ターゲット顧客": "具体的なペルソナ",
    "USP": "他社にない独自の価値",
    "想定価格帯": "$XX - $XX",
    "マーケティングメッセージ": "顧客に刺さるメッセージ"
  }}
}}
```

**重要**: 必ずJSON形式のみを出力してください。説明文は不要です。
"""
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # JSON抽出（マークダウン記法を除去）
            response_text = message.content[0].text
            json_text = response_text.replace('```json', '').replace('```', '').strip()
            
            analysis = json.loads(json_text)
            return analysis
        
        except Exception as e:
            raise Exception(f"Claude分析エラー: {str(e)}")
```

---

### Step 3: メインアプリケーション実装

#### 3.1 app.py

```python
"""
Amazon競合分析ツール for フィットネス機器
メインアプリケーション
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

# カスタムモジュール
from modules.keepa_analyzer import KeepaAnalyzer
from modules.review_collector import ReviewCollector
from modules.claude_analyzer import ClaudeAnalyzer

# 環境変数読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="Amazon競合分析ツール",
    page_icon="🏋️",
    layout="wide"
)

# セッション状態初期化
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'collected_reviews' not in st.session_state:
    st.session_state.collected_reviews = {}
if 'analysis' not in st.session_state:
    st.session_state.analysis = None

# サイドバー：API設定
with st.sidebar:
    st.title("⚙️ 設定")
    
    # 環境変数から読み込み or ユーザー入力
    keepa_key = st.text_input(
        "Keepa API Key", 
        value=os.getenv('KEEPA_API_KEY', ''),
        type="password"
    )
    rainforest_key = st.text_input(
        "RainforestAPI Key",
        value=os.getenv('RAINFOREST_API_KEY', ''),
        type="password"
    )
    claude_key = st.text_input(
        "Claude API Key",
        value=os.getenv('CLAUDE_API_KEY', ''),
        type="password"
    )
    
    st.divider()
    st.markdown("### 📊 取得状況")
    total_reviews = sum(len(r) for r in st.session_state.collected_reviews.values())
    st.metric("取得済みレビュー", f"{total_reviews:,}件")
    st.metric("分析済み商品", f"{len(st.session_state.collected_reviews)}個")

# メインエリア
st.title("🏋️ Amazon競合分析ツール for フィットネス")
st.markdown("競合商品の売れ行きトレンドとレビューをAI分析し、差別化された新商品開発を支援します。")

# 検索セクション
st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input(
        "商品カテゴリを検索",
        placeholder="例: ヨガマット, ダンベル, フィットネスバンド",
        help="Amazonで検索したいフィットネス機器のキーワードを入力"
    )
with col2:
    st.write("")  # スペース調整
    st.write("")
    search_button = st.button("🔍 検索", type="primary", use_container_width=True)

# 検索実行
if search_button and search_term:
    if not keepa_key:
        st.error("❌ Keepa APIキーを入力してください")
    else:
        with st.spinner("市場分析中... Keepa APIでトレンド商品を検索しています"):
            try:
                analyzer = KeepaAnalyzer(keepa_key)
                results = analyzer.search_trending_products(search_term)
                
                if len(results) > 0:
                    st.session_state.search_results = results
                    st.success(f"✅ {len(results)}件の急成長商品を発見しました！")
                else:
                    st.warning("⚠️ 条件に合う商品が見つかりませんでした。キーワードを変えてみてください。")
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")

# 結果表示
if st.session_state.search_results is not None and len(st.session_state.search_results) > 0:
    st.divider()
    st.subheader("📊 売れ筋トレンド（成長率順）")
    
    for idx, (_, row) in enumerate(st.session_state.search_results.iterrows(), 1):
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.markdown(f"### {idx}. {row['title'][:60]}...")
                st.caption(f"ASIN: {row['asin']}")
                
                # メトリクス表示
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                with metric_col1:
                    st.metric("評価", f"⭐ {row['rating']:.1f}")
                with metric_col2:
                    st.metric("レビュー数", f"{row['review_count']:,}件")
                with metric_col3:
                    st.metric("価格", f"${row['price']:.2f}")
                
                # 成長率バッジ
                growth = row['growth_rate'] * 100
                st.markdown(
                    f"<div style='background-color: #00ff00; padding: 8px; border-radius: 5px; "
                    f"text-align: center; font-weight: bold;'>"
                    f"📈 成長率: {growth:.1f}%</div>",
                    unsafe_allow_html=True
                )
            
            with col2:
                # ランキング推移グラフ
                if 'bsr_history' in row and len(row['bsr_history']) > 0:
                    fig = px.line(
                        x=row['bsr_history_dates'][-90:],  # 直近90日
                        y=row['bsr_history'][-90:],
                        title="売上ランキング推移（低いほど売れている）"
                    )
                    fig.update_layout(
                        height=200, 
                        showlegend=False,
                        xaxis_title="",
                        yaxis_title="ランキング"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                st.markdown("**レビュー取得**")
                review_count = st.number_input(
                    "取得件数",
                    min_value=100,
                    max_value=1000,
                    value=500,
                    step=100,
                    key=f"count_{row['asin']}",
                    help="取得するレビュー数（直近から）"
                )
                
                # 取得ボタン
                if st.button(
                    f"📥 レビュー取得", 
                    key=f"btn_{row['asin']}", 
                    use_container_width=True,
                    disabled=not rainforest_key
                ):
                    if not rainforest_key:
                        st.error("RainforestAPI Keyが必要です")
                    else:
                        with st.spinner(f"レビュー取得中... (0/{review_count})"):
                            try:
                                collector = ReviewCollector(rainforest_key)
                                reviews = collector.collect_reviews(
                                    row['asin'],
                                    review_count,
                                    progress_callback=st.progress
                                )
                                st.session_state.collected_reviews[row['asin']] = reviews
                                st.success(f"✅ {len(reviews)}件取得完了！")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ エラー: {str(e)}")
                
                # 既に取得済みなら表示
                if row['asin'] in st.session_state.collected_reviews:
                    count = len(st.session_state.collected_reviews[row['asin']])
                    st.success(f"✅ {count}件取得済み")
            
            st.divider()

# 分析セクション
if st.session_state.collected_reviews and claude_key:
    st.divider()
    st.subheader("🤖 AI分析")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 一括分析開始", type="primary", use_container_width=True):
            with st.spinner("Claude Sonnet 4.5で分析中... 数十秒かかります"):
                try:
                    # 全レビューを統合
                    all_reviews = []
                    for asin, reviews in st.session_state.collected_reviews.items():
                        all_reviews.extend(reviews)
                    
                    df_reviews = pd.DataFrame(all_reviews)
                    
                    # Claude分析
                    analyzer = ClaudeAnalyzer(claude_key)
                    analysis = analyzer.analyze_reviews(df_reviews)
                    
                    st.session_state.analysis = analysis
                    st.success("✅ 分析完了！下にスクロールして結果を確認してください")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 分析エラー: {str(e)}")
    
    with col2:
        if st.button("📄 CSV出力", use_container_width=True):
            # CSV生成
            all_reviews_df = pd.DataFrame([
                r for reviews in st.session_state.collected_reviews.values() 
                for r in reviews
            ])
            
            csv = all_reviews_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "💾 CSVダウンロード",
                csv,
                "amazon_reviews.csv",
                "text/csv",
                use_container_width=True
            )
    
    with col3:
        if st.button("🔄 データクリア", use_container_width=True):
            st.session_state.collected_reviews = {}
            st.session_state.analysis = None
            st.success("✅ データをクリアしました")
            st.rerun()

# 分析結果表示
if st.session_state.analysis:
    st.divider()
    st.header("📈 AI分析結果")
    
    analysis = st.session_state.analysis
    
    # タブで表示
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 カテゴリ別問題点",
        "💡 改善提案",
        "🎯 新商品コンセプト",
        "📈 詳細データ"
    ])
    
    with tab1:
        st.subheader("プロセス別問題点分析")
        
        categories = analysis.get('カテゴリ別問題', {})
        
        for category, issues in categories.items():
            if len(issues) > 0:
                with st.expander(f"**{category}** ({len(issues)}件)", expanded=True):
                    for issue in issues:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{issue['問題']}**")
                            st.caption(f"具体例: {issue['具体例'][:150]}...")
                        with col2:
                            freq_color = {
                                '高': '🔴',
                                '中': '🟡',
                                '低': '🟢'
                            }
                            freq = issue.get('頻度', '中')
                            st.markdown(f"{freq_color.get(freq, '⚪')} 頻度: {freq}")
    
    with tab2:
        st.subheader("💡 改善提案")
        
        proposals = analysis.get('改善提案', [])
        
        for idx, proposal in enumerate(proposals, 1):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {idx}. {proposal['提案']}")
                    st.markdown(f"**解決する問題:** {proposal['解決する問題']}")
                    st.markdown(f"**差別化ポイント:** {proposal['差別化ポイント']}")
                with col2:
                    st.metric("実現可能性", proposal['実現可能性'])
                    st.caption(f"コスト影響: {proposal['想定コスト影響']}")
                st.divider()
    
    with tab3:
        st.subheader("🎯 新商品コンセプト")
        concept = analysis.get('新商品コンセプト', {})
        
        if concept:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("商品名案", concept.get('商品名案', 'N/A'))
                st.metric("想定価格帯", concept.get('想定価格帯', 'N/A'))
            with col2:
                st.metric("ターゲット顧客", concept.get('ターゲット顧客', 'N/A'))
            
            st.markdown("### 🎖️ USP (独自の強み)")
            st.info(concept.get('USP', 'N/A'))
            
            st.markdown("### 📢 マーケティングメッセージ")
            st.success(concept.get('マーケティングメッセージ', 'N/A'))
    
    with tab4:
        # 詳細データ表示
        st.subheader("📈 詳細レビューデータ")
        
        all_reviews_df = pd.DataFrame([
            r for reviews in st.session_state.collected_reviews.values() 
            for r in reviews
        ])
        
        # 評価分布
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                all_reviews_df,
                x='rating',
                title="評価分布",
                labels={'rating': '評価', 'count': '件数'},
                nbins=5
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 評価統計
            st.markdown("### 📊 統計情報")
            st.metric("平均評価", f"{all_reviews_df['rating'].mean():.2f}")
            st.metric("総レビュー数", f"{len(all_reviews_df):,}件")
            st.metric("低評価(★3以下)", f"{len(all_reviews_df[all_reviews_df['rating'] <= 3]):,}件")
        
        # データテーブル
        st.markdown("### 📋 レビュー一覧")
        st.dataframe(
            all_reviews_df[['asin', 'rating', 'title', 'date', 'verified_purchase']],
            use_container_width=True,
            height=400
        )

# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
<p>Powered by Keepa API | RainforestAPI | Claude Sonnet 4.5</p>
<p>© 2025 Amazon競合分析ツール for フィットネス</p>
</div>
""", unsafe_allow_html=True)
```

---

### Step 4: README作成

#### README.md

```markdown
# 🏋️ Amazon競合分析ツール for フィットネス機器

競合商品の売れ行きトレンドとレビューをAI分析し、差別化された新商品開発を支援するツール。

## 🚀 クイックスタート

### 1. 依存パッケージのインストール

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. API鍵の設定

`.env`ファイルを作成し、以下を記入：

\`\`\`env
KEEPA_API_KEY=your_keepa_api_key_here
RAINFOREST_API_KEY=your_rainforest_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
\`\`\`

**API取得方法：**
- **Keepa**: https://keepa.com/ (€19/月)
- **RainforestAPI**: https://www.rainforestapi.com/ ($47/月〜)
- **Claude**: https://console.anthropic.com/ (従量課金)

### 3. アプリ起動

\`\`\`bash
streamlit run app.py
\`\`\`

ブラウザで `http://localhost:8501` が自動で開きます。

## 📋 使い方

1. **検索**: キーワード（例: "ヨガマット"）で急成長商品を検索
2. **レビュー取得**: 各商品の「レビュー取得」ボタンで直近レビューを収集
3. **AI分析**: 「一括分析開始」で問題点・改善提案を生成
4. **レポート出力**: CSV/Excel形式でダウンロード

## 💰 コスト試算

| 項目 | 料金 |
|------|------|
| Keepa API | €19/月 |
| RainforestAPI | $47/月（10,000リクエスト） |
| Claude API | $0.18/分析 |

**例**: 5商品×500レビュー分析 = 約$80/月

## 🛠️ トラブルシューティング

### エラー: "Keepa検索エラー"
→ APIキーが正しいか確認。Keepaアカウントの有効期限をチェック。

### エラー: "レビュー取得エラー"
→ RainforestAPIの月間リクエスト上限を確認。

### 分析が途中で止まる
→ Claude APIのトークン制限の可能性。レビュー件数を減らして再試行。

## 📄 ライセンス

MIT License
```

---

## ✅ 実装完了後の確認事項

### 1. ローカルテスト
```bash
# 仮想環境作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# アプリ起動
streamlit run app.py
```

### 2. API鍵のテスト
- Keepa: 検索機能が動作するか
- RainforestAPI: レビュー取得が動作するか
- Claude: 分析が正常に動作するか

### 3. エラーハンドリング確認
- API鍵未入力時のエラー表示
- ネットワークエラー時の動作
- 異常なレスポンス時の処理

---

## 🎓 PBL教材化のポイント

### Week 1: セットアップ
- Python環境構築
- Streamlit基礎
- API登録・認証

### Week 2: データ収集
- Keepa APIの理解
- RainforestAPIの統合
- エラーハンドリング

### Week 3: AI分析
- Claude APIプロンプトエンジニアリング
- JSON構造化出力
- 結果の可視化

### Week 4: 実務適用
- 実際の商品で分析
- ビジネス提案書作成
- ROI計算

---

## 📞 サポート

質問・バグ報告はGitHub Issuesまで。