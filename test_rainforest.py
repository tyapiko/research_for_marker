"""
RainforestAPI レビューエンドポイント テストスクリプト
"""
import requests
import json

# APIキー
API_KEY = "4C14A71DC96546EBB1F6F2921B5E61C0"

print("=" * 60)
print("RainforestAPI レビューエンドポイント テスト")
print("=" * 60)

# テスト1: レビューエンドポイント
print("\n[テスト1] レビューエンドポイント（amazon.co.jp）")
params1 = {
    'api_key': API_KEY,
    'type': 'reviews',
    'amazon_domain': 'amazon.co.jp',
    'asin': 'B01LP0VI3G',
    'page': 1
}

try:
    response1 = requests.get('https://api.rainforestapi.com/request', params=params1, timeout=10)
    print(f"ステータスコード: {response1.status_code}")
    print(f"レスポンス:\n{json.dumps(response1.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"エラー: {e}")

# テスト2: amazon.comでテスト（日本のAPIキーでも動くか確認）
print("\n" + "=" * 60)
print("[テスト2] レビューエンドポイント（amazon.com）")
params2 = {
    'api_key': API_KEY,
    'type': 'reviews',
    'amazon_domain': 'amazon.com',
    'asin': 'B07ZPKN6YR',  # 有名な商品のASIN
    'page': 1
}

try:
    response2 = requests.get('https://api.rainforestapi.com/request', params=params2, timeout=10)
    print(f"ステータスコード: {response2.status_code}")
    print(f"レスポンス:\n{json.dumps(response2.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"エラー: {e}")

# テスト3: product エンドポイントは動くか（レビュー以外）
print("\n" + "=" * 60)
print("[テスト3] 商品情報エンドポイント（amazon.co.jp）")
params3 = {
    'api_key': API_KEY,
    'type': 'product',
    'amazon_domain': 'amazon.co.jp',
    'asin': 'B01LP0VI3G'
}

try:
    response3 = requests.get('https://api.rainforestapi.com/request', params=params3, timeout=10)
    print(f"ステータスコード: {response3.status_code}")
    data3 = response3.json()

    # レビュー情報が含まれているか確認
    if 'product' in data3:
        product = data3['product']
        print(f"商品名: {product.get('title', 'N/A')}")
        print(f"評価: {product.get('rating', 'N/A')}")
        print(f"レビュー数: {product.get('ratings_total', 'N/A')}")

        # レビュー情報が含まれているか
        if 'top_reviews' in product:
            print(f"\ntop_reviews が存在します！")
            print(f"件数: {len(product['top_reviews'])}")
            if len(product['top_reviews']) > 0:
                print(f"\n最初のレビュー:")
                print(json.dumps(product['top_reviews'][0], indent=2, ensure_ascii=False))
        else:
            print("\ntop_reviews は存在しません")
    else:
        print(f"レスポンス:\n{json.dumps(data3, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"エラー: {e}")

print("\n" + "=" * 60)
print("テスト完了")
print("=" * 60)
