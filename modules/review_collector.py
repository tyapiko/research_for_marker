"""
RainforestAPIを使用してAmazonレビューを取得するモジュール

[改善版] reviewsエンドポイントを使用してレビュー全文を取得
- ページネーション対応（最大5ページ=約50件）
- 低評価優先ソート対応
- レビュー全文取得対応
"""
import requests
import time
from typing import List, Dict, Callable, Optional


class ReviewCollector:
    """RainforestAPI レビュー取得クラス（reviewsエンドポイント）"""

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
        target_count: int = 50,
        progress_callback: Optional[Callable] = None,
        sort_by: str = 'recent'
    ) -> List[Dict]:
        """
        指定ASINのレビューを取得（reviewsエンドポイント）

        Args:
            asin (str): Amazon商品ID (ASIN)
            target_count (int): 取得目標件数（デフォルト50件、最大50件）
            progress_callback (callable): プログレスバー更新用コールバック関数
            sort_by (str): ソート順（'recent': 最新順、'helpful': 役立つ順）

        Returns:
            List[Dict]: レビューデータのリスト
        """
        print(f"[INFO] レビュー収集開始（reviewsエンドポイント）: ASIN={asin}")
        reviews = []

        # プログレスバー初期化
        if progress_callback:
            progress_bar = progress_callback(0)

        try:
            # ページネーションで複数ページ取得
            # 各ページ約10件 → 5ページで最大50件
            max_page = min(5, (target_count + 9) // 10)  # 10件/ページで計算

            params = {
                'api_key': self.api_key,
                'type': 'reviews',
                'amazon_domain': 'amazon.co.jp',
                'asin': asin,
                'page': 1,
                'max_page': max_page,
                'sort_by': sort_by,  # 'recent' or 'helpful'
                'star_rating': 'critical'  # ★1〜3のみ取得
            }

            print(f"[INFO] レビューを取得中... (最大{max_page}ページ)")
            response = requests.get(self.base_url, params=params, timeout=60)
            print(f"[INFO] RainforestAPI レスポンス status={response.status_code}")

            if response.status_code != 200:
                print(f"[ERROR] 取得失敗 (Status: {response.status_code})")
                data = response.json()
                error_msg = data.get('request_info', {}).get('message', 'Unknown error')
                raise Exception(f"API Error: {error_msg}")

            data = response.json()
            print(f"[DEBUG] レスポンスキー: {list(data.keys())}")

            # reviewsデータを取得
            reviews_data = data.get('reviews', [])

            print(f"[INFO] {len(reviews_data)}件のレビューを取得しました")

            if len(reviews_data) == 0:
                print(f"[WARNING] レビューが見つかりませんでした")
                return []

            # レビューデータを抽出
            for review in reviews_data:
                reviews.append({
                    'asin': asin,
                    'review_id': review.get('id', ''),
                    'rating': review.get('rating', 0),
                    'title': review.get('title', ''),
                    'body': review.get('body', ''),  # 全文が取得できる
                    'verified_purchase': review.get('verified_purchase', False),
                    'date': review.get('date', {}).get('raw', '') if isinstance(review.get('date'), dict) else '',
                    'helpful_votes': review.get('helpful_votes', 0),
                    'images': len(review.get('images', [])),
                    'page': review.get('page', 1),  # ページネーション情報
                    'position': review.get('position', 0)
                })

                # プログレス更新
                if progress_callback:
                    progress = min(len(reviews) / target_count, 1.0)
                    progress_bar.progress(progress)

            # 低評価レビュー優先でソート（rating昇順、次にhelpful_votes降順）
            # Claude分析では★3以下のレビューから問題点を抽出するため
            reviews.sort(key=lambda x: (x['rating'], -x.get('helpful_votes', 0)))

            print(f"[SUCCESS] レビュー収集完了: 合計{len(reviews)}件")
            print(f"[INFO] 低評価レビュー優先でソート済み（AI分析用）")
            return reviews

        except Exception as e:
            print(f"[ERROR] エラー詳細: {str(e)}")
            # フォールバック: productエンドポイントを試す
            print(f"[INFO] フォールバック: productエンドポイントを試します...")
            return self._fallback_collect_from_product(asin, progress_callback)

    def _fallback_collect_from_product(
        self,
        asin: str,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        フォールバック: productエンドポイントからtop_reviewsを取得

        Args:
            asin (str): Amazon商品ID (ASIN)
            progress_callback (callable): プログレスバー更新用コールバック関数

        Returns:
            List[Dict]: レビューデータのリスト
        """
        try:
            params = {
                'api_key': self.api_key,
                'type': 'product',
                'amazon_domain': 'amazon.co.jp',
                'asin': asin
            }

            print(f"[INFO] 商品情報を取得中（フォールバック）...")
            response = requests.get(self.base_url, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"フォールバックも失敗 (Status: {response.status_code})")

            data = response.json()
            product = data.get('product', {})
            top_reviews = product.get('top_reviews', [])

            print(f"[INFO] top_reviewsから{len(top_reviews)}件のレビューを取得")

            reviews = []
            for review in top_reviews:
                reviews.append({
                    'asin': asin,
                    'review_id': review.get('id', ''),
                    'rating': review.get('rating', 0),
                    'title': review.get('title', ''),
                    'body': review.get('body', ''),
                    'verified_purchase': review.get('verified_purchase', False),
                    'date': review.get('date', {}).get('raw', '') if isinstance(review.get('date'), dict) else '',
                    'helpful_votes': review.get('helpful_votes', 0),
                    'images': len(review.get('images', []))
                })

                if progress_callback:
                    progress = min(len(reviews) / 20, 1.0)
                    progress_callback(0).progress(progress)

            # 低評価優先ソート
            reviews.sort(key=lambda x: (x['rating'], -x.get('helpful_votes', 0)))

            print(f"[SUCCESS] フォールバック成功: {len(reviews)}件")
            return reviews

        except Exception as e:
            print(f"[ERROR] フォールバックも失敗: {str(e)}")
            raise Exception(f"レビュー取得エラー（両方失敗）: {str(e)}")
