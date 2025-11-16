"""
Keepa APIを使用したシンプルな商品検索モジュール（テスト用）
"""
import keepa
import pandas as pd
import numpy as np
import requests
from .cache_manager import get_cache_manager


class KeepaAnalyzerSimple:
    """Keepa API分析クラス（超シンプル版）"""

    def __init__(self, api_key, rainforest_api_key=None):
        """
        初期化

        Args:
            api_key (str): Keepa APIキー
            rainforest_api_key (str): RainforestAPI キー（動的検索用）
        """
        self.api = keepa.Keepa(api_key, timeout=60)  # タイムアウトを60秒に延長
        self.rainforest_api_key = rainforest_api_key
        self.cache = get_cache_manager()  # キャッシュマネージャー

    def _search_asins_with_rainforest(self, keyword, max_results=10):
        """
        RainforestAPIでキーワード検索してASINを取得（キャッシュ対応）

        Args:
            keyword (str): 検索キーワード
            max_results (int): 最大取得件数（デフォルト10件）

        Returns:
            list: ASINのリスト
        """
        if not self.rainforest_api_key:
            print("[INFO] RainforestAPIキーが未設定のため、固定ASINリストを使用します")
            return None

        # キャッシュチェック
        cached = self.cache.get('rainforest_search', ttl_hours=1, keyword=keyword, max_results=max_results)
        if cached:
            print(f"[CACHE HIT] キャッシュから{len(cached)}件のASINを取得")
            return cached

        try:
            print(f"[INFO] RainforestAPIで「{keyword}」を検索中...")
            params = {
                'api_key': self.rainforest_api_key,
                'type': 'search',
                'amazon_domain': 'amazon.co.jp',
                'search_term': keyword,
                'page': '1'
            }

            response = requests.get('https://api.rainforestapi.com/request', params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            asins = []
            if 'search_results' in data:
                for result in data['search_results'][:max_results]:
                    if 'asin' in result:
                        asins.append(result['asin'])

            print(f"[SUCCESS] RainforestAPIから{len(asins)}件のASINを取得しました")

            # キャッシュに保存(TTL: 1時間)
            if len(asins) > 0:
                self.cache.set(asins, 'rainforest_search', ttl_hours=1, keyword=keyword, max_results=max_results)

            return asins if len(asins) > 0 else None

        except Exception as e:
            print(f"[ERROR] RainforestAPI検索エラー: {e}")
            return None

    def search_products(self, keyword):
        """
        キーワードで商品を検索（超シンプル版）

        Args:
            keyword (str): 検索キーワード

        Returns:
            pd.DataFrame: 商品データフレーム
        """
        try:
            # Step 1: RainforestAPIで動的にASINを検索（上位10件のみ）
            asins = self._search_asins_with_rainforest(keyword, max_results=10)

            # RainforestAPIが使えない場合は固定リストにフォールバック（3件のみ）
            if asins is None:
                keyword_to_asins = {
                    'ヨガマット': ['B01LP0VI3G', 'B01N7EQ8CK', 'B078WZ13GP'],
                    'ダンベル': ['B07WTQ2YPX', 'B0BH7KQWMY', 'B0C8RJHXKP'],
                    'フィットネスバンド': ['B0BVKX7QWM', 'B0C4NMHQXZ', 'B0BYFK3MNQ'],
                }

                for key, value in keyword_to_asins.items():
                    if key in keyword or keyword in key:
                        asins = value
                        break

                if asins is None:
                    asins = ['B01LP0VI3G', 'B01N7EQ8CK', 'B078WZ13GP']

            print(f"検索ASIN: {asins[:10]}... (合計{len(asins)}件)")

            # Keepa APIでデータ取得
            products = self.api.query(
                asins,
                domain='JP',
                stats=90,      # 過去90日の統計情報
                rating=True,   # レビュー情報を含める
                offers=20      # オファー情報を含める
            )

            # デバッグ: 取得した商品数とデータ構造をファイルに書き出し
            with open('keepa_debug.txt', 'w', encoding='utf-8') as f:
                f.write(f"取得した商品数: {len(products)}\n\n")
                for idx, product in enumerate(products):
                    f.write(f"\n{'='*50}\n")
                    f.write(f"商品 {idx+1}: {product.get('asin', 'N/A')}\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"利用可能なキー: {list(product.keys())}\n\n")

                    # 主要なフィールドの値を確認
                    f.write(f"title: {product.get('title')}\n")
                    f.write(f"reviewCount: {product.get('reviewCount')}\n")
                    f.write(f"rating: {product.get('rating')}\n")

                    if 'data' in product:
                        f.write(f"\ndata内のキー: {list(product['data'].keys())}\n")

                        # NEW価格データ
                        if 'NEW' in product['data']:
                            new_data = product['data']['NEW']
                            f.write(f"\nNEW価格データの型: {type(new_data)}\n")
                            if isinstance(new_data, (list, np.ndarray)):
                                f.write(f"NEW価格データの長さ: {len(new_data)}\n")
                                f.write(f"NEW価格データの最初の10要素: {list(new_data[:10]) if len(new_data) > 0 else []}\n")
                                # 最後の10要素も確認
                                f.write(f"NEW価格データの最後の10要素: {list(new_data[-10:]) if len(new_data) >= 10 else list(new_data)}\n")

                        # RATINGデータ
                        if 'RATING' in product['data']:
                            rating_data = product['data']['RATING']
                            f.write(f"\nRATING評価データの型: {type(rating_data)}\n")
                            if isinstance(rating_data, (list, np.ndarray)):
                                f.write(f"RATING評価データの長さ: {len(rating_data)}\n")
                                f.write(f"RATING評価データの最後の10要素: {list(rating_data[-10:]) if len(rating_data) >= 10 else list(rating_data)}\n")

                        # COUNT_REVIEWSデータ
                        if 'COUNT_REVIEWS' in product['data']:
                            review_data = product['data']['COUNT_REVIEWS']
                            f.write(f"\nCOUNT_REVIEWSデータの型: {type(review_data)}\n")
                            if isinstance(review_data, (list, np.ndarray)):
                                f.write(f"COUNT_REVIEWSデータの長さ: {len(review_data)}\n")
                                f.write(f"COUNT_REVIEWSデータの最後の10要素: {list(review_data[-10:]) if len(review_data) >= 10 else list(review_data)}\n")

            results = []

            for product in products:
                try:
                    # 基本情報のみ取得
                    asin = product.get('asin', 'N/A')
                    title = product.get('title', 'N/A')

                    # データが存在しない商品をスキップ
                    if not title or title == 'N/A' or title is None:
                        print(f"[SKIP] {asin}: タイトルなし（Keepaにデータが存在しない可能性）")
                        continue

                    # dataフィールドが空の商品もスキップ
                    if 'data' not in product or not product['data']:
                        print(f"[SKIP] {asin}: dataフィールドが空")
                        continue

                    # 価格取得（シンプル版）
                    price = 0
                    lowest_price = 0
                    try:
                        if 'NEW' in product.get('data', {}):
                            new_prices = product['data']['NEW']
                            if isinstance(new_prices, np.ndarray):
                                new_prices = new_prices.tolist()

                            valid_prices = []
                            # 最後の有効な価格を取得（nanをスキップ）
                            # Keepa APIは価格を100で割った値で返すため、100倍して円に変換
                            for p in reversed(new_prices):
                                if isinstance(p, (int, float)) and not np.isnan(p) and p > 0:
                                    price = int(p * 100)  # 円に変換（例: 24.03 → 2403円）
                                    break

                            # 過去最安単価を取得（全価格データから最小値）
                            for p in new_prices:
                                if isinstance(p, (int, float)) and not np.isnan(p) and p > 0:
                                    valid_prices.append(int(p * 100))

                            if len(valid_prices) > 0:
                                lowest_price = min(valid_prices)
                    except:
                        price = 0
                        lowest_price = 0

                    # レビュー数（dataから取得）
                    review_count = 0
                    try:
                        if 'COUNT_REVIEWS' in product.get('data', {}):
                            review_data = product['data']['COUNT_REVIEWS']
                            if isinstance(review_data, np.ndarray) and len(review_data) > 0:
                                # 最後の有効な値を取得
                                for r in reversed(review_data.tolist()):
                                    if isinstance(r, (int, float)) and not np.isnan(r) and r > 0:
                                        review_count = int(r)
                                        break
                    except:
                        review_count = 0

                    # 評価（dataから取得）
                    rating = 0
                    try:
                        if 'RATING' in product.get('data', {}):
                            rating_data = product['data']['RATING']
                            if isinstance(rating_data, np.ndarray) and len(rating_data) > 0:
                                # 最後の有効な値を取得
                                # stats=90を使用すると既に正しいスケール（4.2など）で返される
                                for r in reversed(rating_data.tolist()):
                                    if isinstance(r, (int, float)) and not np.isnan(r) and r > 0:
                                        rating = r  # そのまま使用
                                        break
                    except:
                        rating = 0

                    # BSRランキング（最新のみ）
                    current_rank = 0
                    try:
                        if 'SALES' in product.get('data', {}):
                            sales = product['data']['SALES']
                            if isinstance(sales, np.ndarray) and len(sales) > 0:
                                sales_list = sales.tolist()
                                # 最後の有効なランキング
                                for s in reversed(sales_list):
                                    if isinstance(s, (int, float)) and s > 0:
                                        current_rank = int(s)
                                        break
                    except:
                        current_rank = 0

                    # 新品出品者数（競合分析用）
                    seller_count = 0
                    try:
                        if 'COUNT_NEW' in product.get('data', {}):
                            count_new_data = product['data']['COUNT_NEW']
                            if isinstance(count_new_data, np.ndarray) and len(count_new_data) > 0:
                                # 最後の有効な値を取得（-1はデータなしを意味する）
                                for c in reversed(count_new_data.tolist()):
                                    if isinstance(c, (int, float)) and c > 0:
                                        seller_count = int(c)
                                        break
                    except:
                        seller_count = 0

                    # 月間販売数トレンド計算
                    monthly_sold_current = 0
                    monthly_sold_3m_ago = 0
                    monthly_sold_6m_ago = 0
                    monthly_sold_12m_ago = 0
                    monthly_sold_24m_ago = 0
                    sales_growth_rate = 0

                    try:
                        # 現在の月間販売数
                        monthly_sold_current = product.get('monthlySold', 0)

                        # 履歴データから過去の販売数を取得
                        if 'monthlySoldHistory' in product and product['monthlySoldHistory']:
                            history = product['monthlySoldHistory']

                            # 偶数インデックス：タイムスタンプ、奇数インデックス：販売数
                            # 最新から遡って3ヶ月前、6ヶ月前、12ヶ月前、2年前のデータを探す
                            if len(history) >= 2:
                                # 現在のタイムスタンプ（最新）
                                current_time = history[-2] if len(history) >= 2 else 0

                                # 3ヶ月 = 約90日 = 90 * 24 * 60 = 129600分
                                # 6ヶ月 = 約180日 = 180 * 24 * 60 = 259200分
                                # 12ヶ月 = 約365日 = 365 * 24 * 60 = 525600分
                                # 24ヶ月 = 約730日 = 730 * 24 * 60 = 1051200分
                                target_3m = current_time - 129600
                                target_6m = current_time - 259200
                                target_12m = current_time - 525600
                                target_24m = current_time - 1051200

                                # 3ヶ月前の販売数を探す
                                for i in range(len(history) - 2, 0, -2):
                                    timestamp = history[i]
                                    sales = history[i + 1]
                                    if timestamp <= target_3m:
                                        monthly_sold_3m_ago = sales
                                        break

                                # 6ヶ月前の販売数を探す
                                for i in range(len(history) - 2, 0, -2):
                                    timestamp = history[i]
                                    sales = history[i + 1]
                                    if timestamp <= target_6m:
                                        monthly_sold_6m_ago = sales
                                        break

                                # 12ヶ月前の販売数を探す
                                for i in range(len(history) - 2, 0, -2):
                                    timestamp = history[i]
                                    sales = history[i + 1]
                                    if timestamp <= target_12m:
                                        monthly_sold_12m_ago = sales
                                        break

                                # 24ヶ月前（2年前）の販売数を探す
                                for i in range(len(history) - 2, 0, -2):
                                    timestamp = history[i]
                                    sales = history[i + 1]
                                    if timestamp <= target_24m:
                                        monthly_sold_24m_ago = sales
                                        break

                        # 販売数成長率を計算（6ヶ月前→現在）
                        if monthly_sold_6m_ago > 0 and monthly_sold_current > 0:
                            sales_growth_rate = ((monthly_sold_current - monthly_sold_6m_ago) / monthly_sold_6m_ago) * 100
                        elif monthly_sold_12m_ago > 0 and monthly_sold_current > 0:
                            # 6ヶ月前のデータがない場合は12ヶ月前で計算
                            sales_growth_rate = ((monthly_sold_current - monthly_sold_12m_ago) / monthly_sold_12m_ago) * 100
                    except Exception as e:
                        print(f"[WARNING] 月間販売数の計算エラー: {e}")
                        sales_growth_rate = 0

                    # 商品選定スコア計算（100点満点）
                    product_score = 0

                    # 1. 販売トレンドスコア（40点）
                    if sales_growth_rate > 100:
                        trend_score = 40
                    elif sales_growth_rate > 50:
                        trend_score = 30
                    elif sales_growth_rate > 20:
                        trend_score = 20
                    elif sales_growth_rate > 0:
                        trend_score = 10
                    else:
                        trend_score = 0

                    # 2. 市場規模スコア（30点）- 月間販売数
                    if monthly_sold_current >= 5000:
                        market_score = 30
                    elif monthly_sold_current >= 3000:
                        market_score = 25
                    elif monthly_sold_current >= 1000:
                        market_score = 20
                    elif monthly_sold_current >= 500:
                        market_score = 15
                    elif monthly_sold_current >= 100:
                        market_score = 10
                    else:
                        market_score = 5

                    # 3. 改善余地スコア（20点）- 評価が低いほど改善余地あり
                    if 0 < rating < 3.5:
                        improvement_score = 20
                    elif 3.5 <= rating < 4.0:
                        improvement_score = 15
                    elif 4.0 <= rating < 4.3:
                        improvement_score = 10
                    elif 4.3 <= rating < 4.5:
                        improvement_score = 5
                    else:
                        improvement_score = 0

                    # 4. 参入難易度スコア（10点）- 新品出品者数（競合の少なさ）
                    if 0 < seller_count <= 3:  # 1-3社: ブルーオーシャン
                        entry_score = 10
                    elif 4 <= seller_count <= 10:  # 4-10社: 競合少なめ
                        entry_score = 7
                    elif 11 <= seller_count <= 30:  # 11-30社: 普通
                        entry_score = 5
                    elif 31 <= seller_count <= 50:  # 31-50社: 競合多め
                        entry_score = 3
                    elif seller_count > 50:  # 51社以上: レッドオーシャン
                        entry_score = 1
                    else:  # データなし
                        entry_score = 5  # 中間値

                    product_score = trend_score + market_score + improvement_score + entry_score

                    results.append({
                        'asin': asin,
                        'title': title,
                        'price': price,
                        'lowest_price': lowest_price,
                        'review_count': review_count,
                        'rating': rating,
                        'current_rank': current_rank,
                        'seller_count': seller_count,
                        'monthly_sold_current': monthly_sold_current,
                        'monthly_sold_3m_ago': monthly_sold_3m_ago,
                        'monthly_sold_6m_ago': monthly_sold_6m_ago,
                        'monthly_sold_12m_ago': monthly_sold_12m_ago,
                        'monthly_sold_24m_ago': monthly_sold_24m_ago,
                        'sales_growth_rate': sales_growth_rate,
                        'product_score': product_score,
                        'trend_score': trend_score,
                        'market_score': market_score,
                        'improvement_score': improvement_score,
                        'entry_score': entry_score,
                    })

                    print(f"[OK] {asin}: {title[:30]}... 価格: {price}円")

                except Exception as e:
                    print(f"[ERROR] 商品処理エラー: {e}")
                    continue

            df = pd.DataFrame(results)

            # 商品選定スコアでソート（降順）
            if len(df) > 0 and 'product_score' in df.columns:
                df = df.sort_values('product_score', ascending=False).reset_index(drop=True)
                print(f"\n取得完了: {len(df)}件（商品選定スコア順にソート済み）")
            else:
                print(f"\n取得完了: {len(df)}件")

            return df

        except Exception as e:
            print(f"Keepa検索エラー: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Keepa検索エラー: {str(e)}")
