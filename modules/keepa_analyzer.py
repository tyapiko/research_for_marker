"""
Keepa APIを使用してAmazon市場のトレンド分析を行うモジュール
"""
import keepa
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

class KeepaAnalyzer:
    """Keepa API分析クラス"""

    def __init__(self, api_key, rainforest_api_key=None):
        """
        初期化

        Args:
            api_key (str): Keepa APIキー
            rainforest_api_key (str): RainforestAPI キー（キーワード検索用）
        """
        self.api = keepa.Keepa(api_key)
        self.rainforest_api_key = rainforest_api_key

    def _search_asins_with_rainforest(self, keyword, max_results=50):
        """
        RainforestAPIでキーワード検索してASINを取得

        Args:
            keyword (str): 検索キーワード
            max_results (int): 最大取得件数

        Returns:
            list: ASINのリスト
        """
        if not self.rainforest_api_key:
            raise Exception("RainforestAPI キーが設定されていません")

        params = {
            'api_key': self.rainforest_api_key,
            'type': 'search',
            'amazon_domain': 'amazon.co.jp',
            'search_term': keyword,
            'page': '1'
        }

        response = requests.get('https://api.rainforestapi.com/request', params=params)
        response.raise_for_status()
        data = response.json()

        asins = []
        if 'search_results' in data:
            for result in data['search_results'][:max_results]:
                if 'asin' in result:
                    asins.append(result['asin'])

        return asins

    def search_trending_products(self, keyword, min_reviews=10, min_growth=-1.0, max_results=20, test_mode=False):
        """
        キーワードで売れ筋商品を検索

        Args:
            keyword (str): 検索キーワード（例: "ヨガマット"）
            min_reviews (int): 最小レビュー数フィルタ
            min_growth (float): 最小成長率フィルタ（0.2 = 20%）
            max_results (int): 最大結果数
            test_mode (bool): テストモード（キーワードベースASIN検索）

        Returns:
            pd.DataFrame: 急成長商品のデータフレーム
        """
        try:
            # キーワードから既知の人気ASINをマッピング（Keepa APIテスト用）
            keyword_to_asins = {
                'ヨガマット': ['B07YNNH8K6', 'B08L649B9N', 'B01LP0VI3G'],
                'ダンベル': ['B07WTQ2YPX', 'B07B3GGFQM', 'B07BJJN6JV'],
                'フィットネスバンド': ['B07ZR5WN8F', 'B07Z8KBMD9', 'B07YLGVJCQ'],
                'プロテイン': ['B00M1YRZZG', 'B00M1YRQIC', 'B07G5QCJ8P'],
                'トレーニングマット': ['B07YNNH8K6', 'B08L649B9N', 'B07YNNJ3C8'],
            }

            # テストモード：キーワードに基づいてASINを選択
            if test_mode:
                import sys
                print(f"テストモード：キーワード「{keyword}」で既知のASINを検索します", file=sys.stderr)

                # キーワードの部分一致で検索
                asins = None
                for key, value in keyword_to_asins.items():
                    if key in keyword or keyword in key:
                        asins = value
                        print(f"キーワード「{keyword}」→「{key}」にマッチ、ASIN: {asins}", file=sys.stderr)
                        break

                # マッチしない場合はデフォルト
                if asins is None:
                    asins = ['B07YNNH8K6', 'B08L649B9N', 'B01LP0VI3G']
                    print(f"キーワード「{keyword}」はマッチせず、デフォルトASINを使用: {asins}", file=sys.stderr)
            else:
                # Step1: RainforestAPIでキーワード検索してASINを取得
                # Keepaトークン制限のため、少数に絞る（テスト用）
                asins = self._search_asins_with_rainforest(keyword, max_results=3)

            if not asins or len(asins) == 0:
                return pd.DataFrame()

            # Step2: Keepa APIでASINの詳細情報を取得
            products = self.api.query(
                asins,
                stats=180,  # 過去180日のデータ
                domain='JP'  # amazon.co.jp (日本)
            )

            results = []

            # デバッグ: 最初の商品データを確認
            import sys
            if len(products) > 0:
                first_product = products[0]
                print(f"デバッグ: 最初の商品ASIN: {first_product.get('asin')}", file=sys.stderr)
                print(f"デバッグ: レビュー数: {first_product.get('reviewCount')}", file=sys.stderr)
                print(f"デバッグ: data keys: {list(first_product['data'].keys())}", file=sys.stderr)
                print(f"デバッグ: SALES exists: {'SALES' in first_product['data']}", file=sys.stderr)
                if 'SALES' in first_product['data']:
                    sales_data = first_product['data']['SALES']
                    # numpy配列対応
                    if sales_data is None:
                        sales_len = 0
                    elif isinstance(sales_data, (list, np.ndarray)):
                        sales_len = len(sales_data)
                    else:
                        sales_len = 0
                    print(f"デバッグ: SALES length: {sales_len}", file=sys.stderr)
                    print(f"デバッグ: SALES type: {type(sales_data)}", file=sys.stderr)

            for product in products:
                # レビュー数フィルタ（テストモードでは無効化）
                review_count = product.get('reviewCount', 0)
                # Noneの場合は0に変換
                if review_count is None:
                    review_count = 0

                import sys
                print(f"デバッグ: 商品 {product.get('asin')} - レビュー数: {review_count}, min_reviews: {min_reviews}, test_mode: {test_mode}", file=sys.stderr)

                # テストモードではフィルタをスキップ
                if not test_mode and review_count < min_reviews:
                    print(f"デバッグ: 商品 {product.get('asin')} はレビュー数不足で除外", file=sys.stderr)
                    continue

                # BSR（ベストセラーランキング）推移を取得
                bsr_history = product['data'].get('SALES', [])

                import sys
                print(f"デバッグ: 商品 {product.get('asin')} - BSR history type: {type(bsr_history)}", file=sys.stderr)

                # BSRデータがない、またはほとんどない場合はスキップ
                if bsr_history is None:
                    print(f"デバッグ: 商品 {product.get('asin')} はBSR履歴がNoneで除外", file=sys.stderr)
                    continue

                # numpy配列かリストの場合の処理
                if isinstance(bsr_history, (list, np.ndarray)):
                    print(f"デバッグ: 商品 {product.get('asin')} - BSR history length: {len(bsr_history)}", file=sys.stderr)
                    if len(bsr_history) == 0:
                        print(f"デバッグ: 商品 {product.get('asin')} はBSR履歴が空で除外", file=sys.stderr)
                        continue
                else:
                    print(f"デバッグ: 商品 {product.get('asin')} はBSR履歴が配列でないため除外", file=sys.stderr)
                    continue

                # 成長率計算（ランキングが下がる = 売上上昇）
                growth_rate = 0.0

                if len(bsr_history) >= 10:
                    # データの前半と後半で比較
                    half_point = len(bsr_history) // 2
                    past_avg = float(np.mean(bsr_history[:half_point]))
                    recent_avg = float(np.mean(bsr_history[half_point:]))

                    if past_avg > 0 and recent_avg > 0:
                        growth_rate = (past_avg - recent_avg) / past_avg

                # 成長率フィルタを適用（テストモードでは無効化）
                import sys
                print(f"デバッグ: 商品 {product.get('asin')} - 成長率: {growth_rate}, min_growth: {min_growth}", file=sys.stderr)
                if not test_mode and growth_rate < min_growth:
                    print(f"デバッグ: 商品 {product.get('asin')} は成長率不足で除外", file=sys.stderr)
                    continue

                print(f"デバッグ: 商品 {product.get('asin')} は全フィルタを通過！", file=sys.stderr)

                # 日付配列を生成（KeepaTime形式からdatetimeに変換）
                csv_data = product.get('csv', [])
                dates = []
                if len(csv_data) > 0:
                    # CSVデータから日付を取得
                    for i in range(0, len(csv_data), 2):
                        if i + 1 < len(csv_data):
                            keepa_time = csv_data[i]
                            dates.append(datetime(2011, 1, 1) + timedelta(minutes=int(keepa_time)))

                # 価格取得（複数の価格タイプをチェック）
                price = 0
                try:
                    if 'NEW' in product['data']:
                        new_prices = product['data']['NEW']
                        if isinstance(new_prices, (list, np.ndarray)) and len(new_prices) > 0:
                            # numpy配列の場合はリストに変換
                            if isinstance(new_prices, np.ndarray):
                                new_prices = new_prices.tolist()
                            # -1は欠損値を示すので除外
                            valid_prices = [float(p) for p in new_prices if isinstance(p, (int, float, np.integer, np.floating)) and p > 0]
                            if valid_prices:
                                price = valid_prices[-1] / 100

                    if price == 0 and 'AMAZON' in product['data']:
                        amazon_prices = product['data']['AMAZON']
                        if isinstance(amazon_prices, (list, np.ndarray)) and len(amazon_prices) > 0:
                            # numpy配列の場合はリストに変換
                            if isinstance(amazon_prices, np.ndarray):
                                amazon_prices = amazon_prices.tolist()
                            valid_prices = [float(p) for p in amazon_prices if isinstance(p, (int, float, np.integer, np.floating)) and p > 0]
                            if valid_prices:
                                price = valid_prices[-1] / 100
                except Exception as e:
                    import sys
                    print(f"価格取得エラー: {e}", file=sys.stderr)
                    price = 0

                results.append({
                    'asin': product['asin'],
                    'title': product.get('title', 'N/A'),
                    'growth_rate': growth_rate,
                    'review_count': review_count,
                    'rating': product.get('rating', 0) / 10,  # Keepaは10倍スケール
                    'price': price,
                    'current_rank': bsr_history[-1] if len(bsr_history) > 0 else 0,
                    'bsr_history': bsr_history,
                    'bsr_history_dates': dates if len(dates) > 0 else list(range(len(bsr_history)))
                })

            df = pd.DataFrame(results)
            import sys
            print(f"デバッグ: フィルタ後の結果数: {len(df)}", file=sys.stderr)
            if len(df) == 0:
                print("デバッグ: 結果が0件のため空のDataFrameを返します", file=sys.stderr)
                return pd.DataFrame()

            return df.sort_values('growth_rate', ascending=False).head(max_results)

        except Exception as e:
            import traceback
            import sys
            print(f"エラー詳細トレースバック:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            raise Exception(f"Keepa検索エラー: {str(e)}")
