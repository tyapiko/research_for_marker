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
from modules.keepa_analyzer_simple import KeepaAnalyzerSimple
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
st.title("🎯 Amazon商品参入判定ツール")
st.caption("Keepa・RainforestAPI・Claude AIで競合の弱点を発見し、改良版商品を提案")

# シンプルなフロー図
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; margin: 20px 0;">
    <div style="display: flex; justify-content: space-around; align-items: center; color: white;">
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 48px; margin-bottom: 10px;">🔍</div>
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">STEP 1</div>
            <div style="font-size: 14px;">参入すべき商品を発見</div>
            <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">Keepa API</div>
        </div>
        <div style="font-size: 36px; opacity: 0.6;">→</div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 48px; margin-bottom: 10px;">📝</div>
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">STEP 2</div>
            <div style="font-size: 14px;">低評価レビューを収集</div>
            <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">RainforestAPI</div>
        </div>
        <div style="font-size: 36px; opacity: 0.6;">→</div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 48px; margin-bottom: 10px;">🤖</div>
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">STEP 3</div>
            <div style="font-size: 14px;">改良案を提案</div>
            <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">Claude AI</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 検索セクション
st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input(
        "🔍 商品カテゴリを検索",
        placeholder="例: ヨガマット, ダンベル, プロテインシェーカー",
        help="参入候補を探したい商品カテゴリを入力してください"
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
        # RainforestAPI + Keepa APIで動的検索
        with st.spinner("Amazon商品を検索中..."):
            try:
                analyzer = KeepaAnalyzerSimple(keepa_key, rainforest_api_key=rainforest_key)
                results = analyzer.search_products(search_term)

                if len(results) > 0:
                    st.session_state.search_results = results
                    st.success(f"✅ {len(results)}件の参入候補商品を発見しました！（商品選定スコア順に表示）")
                else:
                    st.warning("⚠️ 条件に合う商品が見つかりませんでした。キーワードを変えてみてください。")
            except Exception as e:
                error_msg = str(e)

                # Keepa APIのタイムアウトエラー
                if "Read timed out" in error_msg or "timeout" in error_msg.lower():
                    st.error("❌ **Keepa APIへの接続がタイムアウトしました**")
                    st.info("""
                    **考えられる原因：**
                    - Keepa APIのサーバーが混雑している
                    - ネットワーク接続が不安定

                    **対処方法：**
                    - 数分待ってから再度検索してください
                    - それでも解決しない場合は、Keepa APIの状態を確認してください
                    """)

                # Keepa APIのトークン制限エラー
                elif "token" in error_msg.lower() or "waiting" in error_msg.lower():
                    st.error("❌ **Keepa APIのトークン制限に達しました**")
                    st.warning("""
                    **Keepa API無料プランの制限：**
                    - 1トークン/分の制限があります
                    - 連続して検索すると、次のトークンが回復するまで待機が必要です

                    **対処方法：**
                    - 約30分後に再度検索してください
                    - または、Keepa APIの有料プランへのアップグレードをご検討ください
                    """)

                # その他のエラー
                else:
                    st.error(f"❌ エラーが発生しました: {error_msg}")
                    st.info("""
                    **トラブルシューティング：**
                    - APIキーが正しく設定されているか確認してください
                    - インターネット接続を確認してください
                    - 数分待ってから再試行してください
                    """)

# 結果表示
if st.session_state.search_results is not None and len(st.session_state.search_results) > 0:
    st.divider()
    st.subheader("🎯 参入候補商品 TOP5（選定スコア順）")
    st.caption("💡 スコアが高いほど「この商品カテゴリに参入すべき」と判断できます")

    # 上位5件のみ取得
    top5_results = st.session_state.search_results.head(5)

    # テーブル形式でサマリー表示
    st.markdown("### 📊 商品比較テーブル")

    # データフレーム用に整形
    table_data = []
    for idx, (_, row) in enumerate(top5_results.iterrows(), 1):
        # 推奨度の判定
        score = row.get('product_score', 0)
        if score >= 80:
            recommendation = "🔥超推奨"
        elif score >= 60:
            recommendation = "⭐推奨"
        elif score >= 40:
            recommendation = "✅検討"
        else:
            recommendation = "⚠️要注意"

        table_data.append({
            '順位': f"{idx}位 {recommendation}",
            '商品名': row['title'][:40] + "..." if len(row['title']) > 40 else row['title'],
            'スコア': f"{score}点",
            '現単価': f"¥{row['price']:,.0f}" if row['price'] > 0 else "-",
            '最安': f"¥{row.get('lowest_price', 0):,.0f}" if row.get('lowest_price', 0) > 0 else "-",
            '新規数': f"{row.get('seller_count', 0)}社",
            'レビュー': f"{row.get('review_count', 0):,}件",
            '評価': f"⭐{row['rating']:.1f}",
            'BSR': f"{row.get('current_rank', 0):,}" if row.get('current_rank', 0) > 0 else "-",
            '今月販売': f"{row.get('monthly_sold_current', 0):,}個",
            '6ヶ月前': f"{row.get('monthly_sold_6m_ago', 0):,}個" if row.get('monthly_sold_6m_ago', 0) > 0 else "-",
            '1年前': f"{row.get('monthly_sold_12m_ago', 0):,}個" if row.get('monthly_sold_12m_ago', 0) > 0 else "-"
        })

    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True, height=250)

    st.divider()

    # 各商品の詳細を展開可能に
    st.markdown("### 📋 商品詳細（総合評価の内訳）")

    for idx, (_, row) in enumerate(top5_results.iterrows(), 1):
        title = row['title'] if row['title'] else "商品名取得中..."
        score = row.get('product_score', 0)

        # 推奨度の判定
        if score >= 80:
            recommendation = "🔥 超推奨"
        elif score >= 60:
            recommendation = "⭐ 推奨"
        elif score >= 40:
            recommendation = "✅ 検討価値あり"
        else:
            recommendation = "⚠️ 要慎重検討"

        with st.expander(f"🏆 {idx}位: {title[:50]}... | スコア: {score}点", expanded=(idx == 1)):
            # Amazon商品ページリンク
            amazon_url = f"https://www.amazon.co.jp/dp/{row['asin']}"
            st.markdown(f"🔗 [Amazonで商品を見る]({amazon_url}) | ASIN: `{row['asin']}` | {recommendation}")

            st.divider()

            # 総合評価の内訳
            st.markdown("##### 📊 総合評価の内訳")
            score_col1, score_col2, score_col3, score_col4 = st.columns(4)

            with score_col1:
                trend_score = row.get('trend_score', 0)
                st.metric("📈 販売トレンド", f"{trend_score}/40点")
                st.caption("成長率が高いほど高得点")
                growth = row.get('sales_growth_rate', 0)
                st.caption(f"成長率: {growth:+.1f}%")

            with score_col2:
                market_score = row.get('market_score', 0)
                st.metric("💰 市場規模", f"{market_score}/30点")
                st.caption("販売数が多いほど高得点")
                st.caption(f"月間: {row.get('monthly_sold_current', 0):,}個")

            with score_col3:
                improvement_score = row.get('improvement_score', 0)
                st.metric("🔧 改善余地", f"{improvement_score}/20点")
                st.caption("評価が低いほど高得点")
                st.caption(f"評価: ⭐{row['rating']:.1f}")

            with score_col4:
                entry_score = row.get('entry_score', 0)
                st.metric("🚪 参入難易度", f"{entry_score}/10点")
                st.caption("競合が少ないほど高得点")
                st.caption(f"新規: {row.get('seller_count', 0)}社")

            st.divider()

            # レビュー収集セクション
            st.markdown("##### 📝 レビュー収集")
            st.caption("⭐最新50件のレビューを取得（低評価優先ソート）")

            if rainforest_key:
                # 既に収集済みかチェック
                if row['asin'] in st.session_state.collected_reviews:
                    reviews = st.session_state.collected_reviews[row['asin']]

                    col_review1, col_review2 = st.columns([2, 1])
                    with col_review1:
                        st.success(f"✅ レビュー収集済み: {len(reviews)}件")

                    with col_review2:
                        # CSVダウンロードボタン
                        df_reviews = pd.DataFrame(reviews)
                        csv = df_reviews.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            "💾 CSV",
                            csv,
                            f"reviews_{row['asin']}.csv",
                            "text/csv",
                            key=f"download_{row['asin']}",
                            use_container_width=True
                        )

                    # レビュープレビュー（最新3件）
                    with st.expander("📋 レビュープレビュー（最新3件）"):
                        preview_reviews = reviews[:3]

                        for i, review in enumerate(preview_reviews, 1):
                            col_star, col_date = st.columns([1, 2])
                            with col_star:
                                st.caption(f"⭐ {review['rating']}")
                            with col_date:
                                st.caption(f"📅 {review.get('date', 'N/A')}")

                            if review.get('title'):
                                st.markdown(f"**{review['title']}**")

                            body = review.get('body', '')
                            if len(body) > 200:
                                st.caption(body[:200] + "...")
                            else:
                                st.caption(body)

                            if i < len(preview_reviews):
                                st.markdown("---")

                else:
                    if st.button("📝 レビューを収集（最新50件）", key=f"review_{row['asin']}", use_container_width=True, type="secondary"):
                        with st.spinner("収集中...（reviewsエンドポイント使用）"):
                            try:
                                from modules.review_collector import ReviewCollector
                                collector = ReviewCollector(rainforest_key)
                                reviews = collector.collect_reviews(row['asin'], target_count=50)
                                st.session_state.collected_reviews[row['asin']] = reviews

                                # 収集件数に応じてメッセージを変更
                                if len(reviews) >= 40:
                                    st.success(f"✅ {len(reviews)}件収集完了！（reviewsエンドポイント）")
                                elif len(reviews) >= 10:
                                    st.success(f"✅ {len(reviews)}件収集完了！")
                                    st.info("💡 RainforestAPIの無料プランでは約10-20件のレビューが取得できます。より多くのレビューが必要な場合は有料プランをご検討ください。")
                                else:
                                    st.warning(f"⚠️ {len(reviews)}件のレビューを収集しましたが、予想より少ない可能性があります。")

                                st.rerun()
                            except Exception as e:
                                error_msg = str(e)
                                st.error(f"❌ レビュー収集エラー: {error_msg}")

                                # RainforestAPIのエラーメッセージを分かりやすく表示
                                if "両方失敗" in error_msg:
                                    st.warning("""
                                    **レビュー取得に失敗しました**

                                    **考えられる原因：**
                                    - RainforestAPIのクレジットが不足している
                                    - この商品にレビューが存在しない
                                    - API接続の問題

                                    **対処方法：**
                                    - RainforestAPIの残クレジットを確認してください
                                    - 別の商品で試してみてください
                                    - 数分待ってから再試行してください
                                    """)
                                else:
                                    st.info("数分待ってから再試行してください。")
            else:
                st.warning("⚠️ RainforestAPIキーを設定してください")

# 分析セクション
if st.session_state.collected_reviews and claude_key:
    st.divider()
    st.subheader("🤖 AI分析（低評価レビュー★3以下）")
    st.caption("Claude Sonnet 4.5が低評価レビューから問題点を抽出し、改善提案を生成します")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 一括分析開始", type="primary", use_container_width=True):
            with st.spinner("Claude Sonnet 4.5で低評価レビューを分析中... 数十秒かかります"):
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
