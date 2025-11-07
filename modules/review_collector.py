"""
RainforestAPIを使用してAmazonレビューを取得するモジュール

[注意] RainforestAPIのreviewsエンドポイントは現在利用不可のため、
productエンドポイントのtop_reviewsフィールドを使用しています。
取得できるレビュー数は約10-20件に制限されます。
"""
import requests
import time
from typing import List, Dict, Callable, Optional

class ReviewCollector:
    """RainforestAPI レビュー取得クラス（productエンドポイント経由）"""

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
        指定ASINのレビューを取得（productエンドポイント経由）

        Args:
            asin (str): Amazon商品ID (ASIN)
            target_count (int): 取得目標件数（実際は10-20件程度しか取得できません）
            progress_callback (callable): プログレスバー更新用コールバック関数

        Returns:
            List[Dict]: レビューデータのリスト
        """
        print(f"[INFO] レビュー収集開始（productエンドポイント経由）: ASIN={asin}")
        reviews = []

        # プログレスバー初期化
        if progress_callback:
            progress_bar = progress_callback(0)

        try:
            # productエンドポイントからtop_reviewsを取得
            params = {
                'api_key': self.api_key,
                'type': 'product',
                'amazon_domain': 'amazon.co.jp',
                'asin': asin
            }

            print(f"[INFO] 商品情報を取得中...")
            response = requests.get(self.base_url, params=params, timeout=30)
            print(f"[INFO] RainforestAPI レスポンス status={response.status_code}")

            if response.status_code != 200:
                print(f"[ERROR] 取得失敗 (Status: {response.status_code})")
                data = response.json()
                error_msg = data.get('request_info', {}).get('message', 'Unknown error')
                raise Exception(f"API Error: {error_msg}")

            data = response.json()
            print(f"[DEBUG] レスポンスキー: {list(data.keys())}")

            # productデータからtop_reviewsを取得
            product = data.get('product', {})
            top_reviews = product.get('top_reviews', [])

            print(f"[INFO] top_reviewsで{len(top_reviews)}件のレビューを発見")

            if len(top_reviews) == 0:
                print(f"[WARNING] レビューが見つかりませんでした")
                return []

            # レビューデータを抽出
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

                # プログレス更新
                if progress_callback:
                    progress = min(len(reviews) / target_count, 1.0)
                    progress_bar.progress(progress)

            # 低評価レビュー優先でソート（rating昇順、次にhelpful_votes降順）
            # Claude分析では★3以下のレビューから問題点を抽出するため
            reviews.sort(key=lambda x: (x['rating'], -x.get('helpful_votes', 0)))

            print(f"[SUCCESS] レビュー収集完了: 合計{len(reviews)}件")
            print(f"[INFO] 低評価レビュー優先でソート済み（AI分析用）")
            print(f"[INFO] [注意] productエンドポイントの制限により、取得できるのは約10-20件です")
            return reviews

        except Exception as e:
            print(f"[ERROR] エラー詳細: {str(e)}")
            raise Exception(f"レビュー取得エラー: {str(e)}")
