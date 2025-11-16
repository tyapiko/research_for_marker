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
from modules.progress_tracker import ProgressTracker
from data.sample_data import get_sample_data

# 環境変数読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="Amazon競合分析ツール",
    page_icon="🏋️",
    layout="wide"
)

# APIキー取得ヘルパー関数(セキュリティ強化)
def get_api_key(key_name):
    """
    優先順位:
    1. Streamlit Secrets (本番環境推奨)
    2. 環境変数 (.env ファイル)
    3. 空文字列(ユーザー入力待ち)
    """
    try:
        # Streamlit Secretsから取得
        if hasattr(st, 'secrets') and 'api_keys' in st.secrets:
            return st.secrets['api_keys'].get(key_name, '')
    except:
        pass

    # 環境変数から取得
    return os.getenv(key_name, '')

# セッション状態初期化
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'collected_reviews' not in st.session_state:
    st.session_state.collected_reviews = {}
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'onboarding_completed' not in st.session_state:
    st.session_state.onboarding_completed = False
if 'show_onboarding' not in st.session_state:
    st.session_state.show_onboarding = True
if 'show_sample_mode' not in st.session_state:
    st.session_state.show_sample_mode = False
if 'sample_data_loaded' not in st.session_state:
    st.session_state.sample_data_loaded = False

# サイドバー：API設定
with st.sidebar:
    st.title("⚙️ 設定")

    st.info("💡 APIキーはStreamlit Secretsまたは.envファイルで管理することを推奨します。[セットアップガイド](SECURITY_SETUP.md)")

    # APIキーの取得(Streamlit Secrets → .env → ユーザー入力の優先順位)
    default_keepa = get_api_key('KEEPA_API_KEY')
    default_rainforest = get_api_key('RAINFOREST_API_KEY')
    default_claude = get_api_key('CLAUDE_API_KEY')

    keepa_key = st.text_input(
        "Keepa API Key" + (" ✓" if default_keepa else ""),
        value=default_keepa,
        type="password",
        help="Streamlit Secretsまたは.envで設定済みの場合、再入力不要"
    )
    rainforest_key = st.text_input(
        "RainforestAPI Key" + (" ✓" if default_rainforest else ""),
        value=default_rainforest,
        type="password",
        help="Streamlit Secretsまたは.envで設定済みの場合、再入力不要"
    )
    claude_key = st.text_input(
        "Claude API Key" + (" ✓" if default_claude else ""),
        value=default_claude,
        type="password",
        help="Streamlit Secretsまたは.envで設定済みの場合、再入力不要"
    )

    st.divider()
    st.markdown("### 📊 取得状況")
    total_reviews = sum(len(r) for r in st.session_state.collected_reviews.values())
    st.metric("取得済みレビュー", f"{total_reviews:,}件")
    st.metric("分析済み商品", f"{len(st.session_state.collected_reviews)}個")

# メインエリア
st.title("🎯 Amazon商品参入判定ツール")
st.caption("Keepa・RainforestAPI・Claude AIで競合の弱点を発見し、改良版商品を提案")

# オンボーディングフロー（初回訪問時）
if not st.session_state.onboarding_completed and st.session_state.show_onboarding:
    with st.expander("🎓 初めての方へ（5分で使い方をマスター）", expanded=True):
        tabs = st.tabs(["① 使い方", "② サンプル体験", "③ API設定"])

        with tabs[0]:
            st.markdown("""
            ### 🎯 このツールで何ができる？

            Amazon商品の**参入すべきか判断**を自動化します：

            - 🔍 **キーワード検索**: 入力するだけで参入候補商品を発見
            - 📊 **自動スコアリング**: 100点満点で客観的に評価
            - 💡 **AI分析**: 低評価レビューから改善点を抽出
            - 💰 **収益性計算**: 利益予測で参入判断を支援

            ---

            ### 📝 3ステップで完結

            **STEP 1**: キーワード入力 → 検索ボタン
            → 参入すべき商品を発見（売上・成長率・競合数から自動スコアリング）

            **STEP 2**: 上位商品の「レビュー収集」ボタン
            → 低評価レビューを優先的に取得

            **STEP 3**: 「AI分析」ボタン
            → Claude AIが問題点を6カテゴリに分類、改善提案を生成

            ---

            ### ⏱️ 所要時間

            - 検索: 30-60秒
            - レビュー収集: 15-30秒/商品
            - AI分析: 20-40秒

            **合計**: 1商品あたり約2-3分で完了！
            """)

        with tabs[1]:
            st.markdown("""
            ### 🎬 サンプルデータで体験

            APIキーがなくても、サンプルデータで実際のツールを体験できます。

            **「ヨガマット」の実際の分析結果**を表示します：
            - 10商品のスコアリング結果
            - レビュー分析
            - AI改善提案

            操作感を確かめてから、APIキーを設定してください。
            """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎯 サンプルデータを表示", type="primary", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.session_state.show_sample_mode = True
                    st.rerun()
            with col2:
                if st.button("スキップ", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.session_state.show_onboarding = False
                    st.rerun()

        with tabs[2]:
            st.markdown("""
            ### 🔑 APIキーの設定方法

            このツールは3つのAPIを使用します：

            #### 1. Keepa API（商品データ取得）
            - [Keepa公式サイト](https://keepa.com/#!api) で無料アカウント作成
            - 無料プラン: 1トークン/分（検索10商品=1トークン）
            - 推奨: Basic Plan（月$19, 100トークン/分）

            #### 2. RainforestAPI（ASIN検索・レビュー取得）
            - [RainforestAPI公式](https://www.rainforestapi.com/) で無料クレジット取得
            - 無料: $100クレジット（約200検索分）
            - 推奨: Starter Plan（月$29）

            #### 3. Claude API（AI分析）
            - [Anthropic Console](https://console.anthropic.com/) でキー発行
            - 無料: $5クレジット
            - 推奨: 従量課金（分析1回=約$0.1）

            ---

            #### ✅ 設定方法

            **方法1**: 左サイドバーに直接入力（簡単、非推奨）
            **方法2**: `.env` ファイルに保存（推奨）
            **方法3**: Streamlit Secrets（本番環境で推奨）

            詳細: [SECURITY_SETUP.md](SECURITY_SETUP.md)
            """)

            if st.button("理解しました", type="primary", use_container_width=True):
                st.session_state.onboarding_completed = True
                st.session_state.show_onboarding = False
                st.rerun()

# サンプルデータモード
if st.session_state.show_sample_mode and not st.session_state.sample_data_loaded:
    st.info("🎬 サンプルデータを読み込んでいます...")
    sample_data = get_sample_data()

    # サンプルデータをセッション状態に保存
    st.session_state.search_results = sample_data['products']
    st.session_state.collected_reviews = sample_data['reviews']
    st.session_state.analysis = sample_data['analysis']
    st.session_state.sample_data_loaded = True

    st.success("✅ サンプルデータ「ヨガマット」を読み込みました！実際のツールと同じように操作できます。")
    st.balloons()

# サンプルモードの表示
if st.session_state.show_sample_mode:
    st.warning("""
    🎬 **サンプルデータモード**

    これは「ヨガマット」の実際の分析結果です。
    APIキーを設定すると、他のキーワードでも分析できます。

    [サンプルモードを終了して実際に使う](#) ← サイドバーでAPIキーを設定してください
    """)

# シンプルなフロー図
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 30px; border-radius: 15px; margin: 20px 0;">
    <div style="display: flex; justify-content: space-around; align-items: center; color: white;">
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 48px; margin-bottom: 10px;">🔍</div>
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">STEP 1</div>
            <div style="font-size: 14px;">参入すべき商品を発見</div>
            <div style="font-size: 14px; opacity: 0.8; margin-top: 5px;">Keepa API</div>
        </div>
        <div style="font-size: 36px; opacity: 0.6;">→</div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 48px; margin-bottom: 10px;">📝</div>
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">STEP 2</div>
            <div style="font-size: 14px;">低評価レビューを収集</div>
            <div style="font-size: 14px; opacity: 0.8; margin-top: 5px;">RainforestAPI</div>
        </div>
        <div style="font-size: 36px; opacity: 0.6;">→</div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 48px; margin-bottom: 10px;">👾</div>
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">STEP 3</div>
            <div style="font-size: 14px;">改良案を提案</div>
            <div style="font-size: 14px; opacity: 0.8; margin-top: 5px;">Claude AI</div>
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

# 詳細検索フィルタ（折りたたみ式）
with st.expander("🔧 詳細検索（オプション）"):
    st.markdown("**商品条件を絞り込む**")

    # 現価格（スライダー）
    price_range = st.slider(
        "現価格（円）",
        min_value=0,
        max_value=100000,
        value=(0, 100000),
        step=1000,
        key="price_range",
        format="¥%d"
    )

    # 月間販売数（スライダー）
    monthly_range = st.slider(
        "月間販売数（個）",
        min_value=0,
        max_value=10000,
        value=(0, 10000),
        step=100,
        key="monthly_range"
    )

    # 成長トレンド（チェックボックス）
    st.markdown("##### 📈 成長トレンド")
    st.caption("チェックした場合、その期間より売上が伸びている商品のみ表示")
    growth_3m = st.checkbox("3ヶ月前より売れている", key="growth_3m")
    growth_6m = st.checkbox("6ヶ月前より売れている", key="growth_6m")
    growth_12m = st.checkbox("1年前より売れている", key="growth_12m")
    growth_24m = st.checkbox("2年前より売れている", key="growth_24m")

    # ランキング（BSR）（スライダー）
    bsr_range = st.slider(
        "ランキング（BSR）",
        min_value=0,
        max_value=100000,
        value=(0, 100000),
        step=1000,
        key="bsr_range",
        help="小さいほど売れている（1位が最高）"
    )

    # 商品評価（スライダー）
    rating_range = st.slider(
        "商品評価（★）",
        min_value=0.0,
        max_value=5.0,
        value=(0.0, 5.0),
        step=0.1,
        key="rating_range"
    )

    # レビュー数（スライダー）
    review_min = st.slider(
        "レビュー数（何件以上）",
        min_value=0,
        max_value=5000,
        value=0,
        step=50,
        key="review_min"
    )

    # 新規出品者数（スライダー）
    seller_max = st.slider(
        "新規出品者数（何社以下）",
        min_value=0,
        max_value=500,
        value=500,
        step=10,
        key="seller_max",
        help="競合が少ない商品を探す"
    )

# フィルタ条件を辞書に格納
filters = {
    'price': price_range,
    'monthly_current': monthly_range,
    'growth_3m': growth_3m,
    'growth_6m': growth_6m,
    'growth_12m': growth_12m,
    'growth_24m': growth_24m,
    'bsr': bsr_range,
    'rating': rating_range,
    'review_min': review_min,
    'seller_max': seller_max,
}

# 検索実行
if search_button and search_term:
    if not keepa_key:
        st.error("❌ Keepa APIキーを入力してください")
    else:
        # プログレストラッカー初期化
        tracker = ProgressTracker()
        progress_container = st.container()

        with progress_container:
            tracker.start(total_steps=4)

            try:
                # STEP 1: RainforestAPIでASIN検索
                tracker.update("RainforestAPIでキーワード検索中...")
                analyzer = KeepaAnalyzerSimple(keepa_key, rainforest_api_key=rainforest_key)

                # STEP 2: Keepa APIで商品データ取得
                tracker.update("Keepa APIで商品データ取得中...")
                results = analyzer.search_products(search_term)

                # STEP 3: スコア計算
                tracker.update("商品スコアを計算中...")

                # フィルタリング処理（ベクトル化で高速化）
                # 価格フィルタ
                price_mask = (results['price'] >= filters['price'][0]) & (results['price'] <= filters['price'][1])

                # 月間販売数フィルタ
                monthly_mask = (results['monthly_sold_current'] >= filters['monthly_current'][0]) & \
                              (results['monthly_sold_current'] <= filters['monthly_current'][1])

                # 成長トレンドフィルタ
                growth_mask = pd.Series([True] * len(results), index=results.index)

                if filters['growth_3m']:
                    growth_mask &= (results['monthly_sold_3m_ago'] > 0) & \
                                  (results['monthly_sold_current'] > results['monthly_sold_3m_ago'])

                if filters['growth_6m']:
                    growth_mask &= (results['monthly_sold_6m_ago'] > 0) & \
                                  (results['monthly_sold_current'] > results['monthly_sold_6m_ago'])

                if filters['growth_12m']:
                    growth_mask &= (results['monthly_sold_12m_ago'] > 0) & \
                                  (results['monthly_sold_current'] > results['monthly_sold_12m_ago'])

                if filters['growth_24m']:
                    growth_mask &= (results['monthly_sold_24m_ago'] > 0) & \
                                  (results['monthly_sold_current'] > results['monthly_sold_24m_ago'])

                # BSRフィルタ
                bsr_mask = ((results['current_rank'] >= filters['bsr'][0]) & \
                           (results['current_rank'] <= filters['bsr'][1])) | \
                          (results['current_rank'] == 0)

                # 評価フィルタ
                rating_mask = (results['rating'] >= filters['rating'][0]) & \
                             (results['rating'] <= filters['rating'][1])

                # レビュー数フィルタ
                review_mask = results['review_count'] >= filters['review_min']

                # 出品者数フィルタ
                seller_mask = results['seller_count'] <= filters['seller_max']

                # 全フィルタを結合
                final_mask = price_mask & monthly_mask & growth_mask & bsr_mask & rating_mask & review_mask & seller_mask

                # フィルタリング実行
                filtered_results = results[final_mask].copy()

                # STEP 4: 結果を整形
                tracker.update("検索結果を整形中...")

                if len(filtered_results) > 0:
                    # スコア順にソート
                    filtered_results = filtered_results.sort_values('product_score', ascending=False).reset_index(drop=True)
                    st.session_state.search_results = filtered_results

                    # 完了
                    tracker.complete(f"✅ 完了！{len(filtered_results)}件の商品を発見しました")
                    st.success(f"✅ {len(filtered_results)}件の参入候補商品を発見しました！（商品選定スコア順に表示）")
                    if len(results) > len(filtered_results):
                        st.info(f"💡 詳細検索フィルタにより、{len(results) - len(filtered_results)}件の商品が除外されました")
                else:
                    tracker.complete("⚠️ 条件に合う商品が見つかりませんでした")
                    st.warning("⚠️ 条件に合う商品が見つかりませんでした。キーワードやフィルタ条件を変えてみてください。")
                    if len(results) > 0:
                        st.info(f"💡 {len(results)}件の商品が見つかりましたが、詳細検索フィルタの条件を満たしませんでした")
            except Exception as e:
                tracker.error(f"エラーが発生しました: {str(e)}")
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

    # Next Actionガイド
    top_score = st.session_state.search_results.iloc[0]['product_score']
    top_asin = st.session_state.search_results.iloc[0]['asin']

    st.markdown("## 🎯 推奨アクション")

    if top_score >= 80:
        st.success("""
        ### 🔥 超推奨商品を発見！

        **トップ商品スコア**: {score}点 - これは非常に魅力的な参入機会です！

        **次のステップ**:
        1. 上位3商品のレビューを収集して問題点を特定
        2. AI分析で改善提案を取得
        3. 改良版の試作品を検討

        👇 今すぐレビュー収集を開始することをお勧めします
        """.format(score=int(top_score)))
    elif top_score >= 60:
        st.info("""
        ### ⭐ 参入価値あり

        **トップ商品スコア**: {score}点 - 慎重な調査で成功の可能性があります

        **次のステップ**:
        1. レビュー収集で市場の問題点を把握
        2. 競合の詳細調査
        3. 収益性シミュレーションで判断

        👇 まずはレビュー分析から始めてください
        """.format(score=int(top_score)))
    elif top_score >= 40:
        st.warning("""
        ### ✅ 慎重に検討すべき

        **トップ商品スコア**: {score}点 - リスクとリターンのバランスを精査が必要です

        **推奨アクション**:
        - 別のキーワードも試してみる
        - 詳細フィルタで条件を変更
        - レビューで具体的な問題点を確認

        👇 より高スコアの商品を探すことをお勧めします
        """.format(score=int(top_score)))
    else:
        st.error("""
        ### ⚠️ 参入非推奨

        **トップ商品スコア**: {score}点 - このカテゴリへの参入はリスクが高いです

        **推奨アクション**:
        - **別のキーワードで検索**: より良い機会を探す
        - **フィルタ条件を見直す**: 検索範囲を広げる

        現状では参入をお勧めしません。
        """.format(score=int(top_score)))

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
            '今月': f"{row.get('monthly_sold_current', 0):,}個",
            '3ヶ月前': f"{row.get('monthly_sold_3m_ago', 0):,}個" if row.get('monthly_sold_3m_ago', 0) > 0 else "-",
            '6ヶ月前': f"{row.get('monthly_sold_6m_ago', 0):,}個" if row.get('monthly_sold_6m_ago', 0) > 0 else "-",
            '1年前': f"{row.get('monthly_sold_12m_ago', 0):,}個" if row.get('monthly_sold_12m_ago', 0) > 0 else "-",
            '2年前': f"{row.get('monthly_sold_24m_ago', 0):,}個" if row.get('monthly_sold_24m_ago', 0) > 0 else "-"
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
                st.caption(f"今月: {row.get('monthly_sold_current', 0):,}個")
                if row.get('monthly_sold_3m_ago', 0) > 0:
                    st.caption(f"3ヶ月前: {row.get('monthly_sold_3m_ago', 0):,}個")
                if row.get('monthly_sold_6m_ago', 0) > 0:
                    st.caption(f"6ヶ月前: {row.get('monthly_sold_6m_ago', 0):,}個")
                if row.get('monthly_sold_12m_ago', 0) > 0:
                    st.caption(f"1年前: {row.get('monthly_sold_12m_ago', 0):,}個")
                if row.get('monthly_sold_24m_ago', 0) > 0:
                    st.caption(f"2年前: {row.get('monthly_sold_24m_ago', 0):,}個")

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
            st.caption("⭐★1〜3の低評価レビューを最大50件取得（改善点分析用）")

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
