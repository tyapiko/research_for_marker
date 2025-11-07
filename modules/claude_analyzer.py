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
