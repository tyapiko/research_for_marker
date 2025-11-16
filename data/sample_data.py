"""
サンプルデータ: ヨガマットの分析結果
オンボーディング・デモ用
"""
import pandas as pd
from datetime import datetime

# サンプル商品データ (10商品)
SAMPLE_PRODUCTS = pd.DataFrame([
    {
        'asin': 'B08SAMPLE1',
        'title': 'ヨガマット 10mm 高密度 TPE素材 滑り止め付き トレーニングマット',
        'price': 2980,
        'rating': 3.8,
        'review_count': 1247,
        'current_rank': 152,
        'monthly_sold_current': 1200,
        'monthly_sold_6m_ago': 750,
        'monthly_sold_12m_ago': 520,
        'monthly_sold_24m_ago': 380,
        'seller_count': 8,
        'product_score': 85,
        'sales_trend_score': 38,
        'market_size_score': 25,
        'improvement_potential_score': 18,
        'entry_difficulty_score': 9
    },
    {
        'asin': 'B09SAMPLE2',
        'title': 'ヨガマット 6mm エクササイズマット NBR素材 収納バッグ付き',
        'price': 1980,
        'rating': 4.1,
        'review_count': 856,
        'current_rank': 248,
        'monthly_sold_current': 850,
        'monthly_sold_6m_ago': 680,
        'monthly_sold_12m_ago': 590,
        'monthly_sold_24m_ago': 510,
        'seller_count': 15,
        'product_score': 72,
        'sales_trend_score': 28,
        'market_size_score': 20,
        'improvement_potential_score': 12,
        'entry_difficulty_score': 7
    },
    {
        'asin': 'B07SAMPLE3',
        'title': 'ヨガマット 8mm 軽量 折りたたみ式 持ち運び便利 滑り止め',
        'price': 3480,
        'rating': 3.6,
        'review_count': 632,
        'current_rank': 385,
        'monthly_sold_current': 600,
        'monthly_sold_6m_ago': 620,
        'monthly_sold_12m_ago': 580,
        'monthly_sold_24m_ago': 550,
        'seller_count': 22,
        'product_score': 68,
        'sales_trend_score': 18,
        'market_size_score': 15,
        'improvement_potential_score': 20,
        'entry_difficulty_score': 5
    },
    {
        'asin': 'B10SAMPLE4',
        'title': 'プロ仕様 ヨガマット 12mm 超厚手 関節保護 エクササイズマット',
        'price': 4980,
        'rating': 4.3,
        'review_count': 1534,
        'current_rank': 189,
        'monthly_sold_current': 980,
        'monthly_sold_6m_ago': 850,
        'monthly_sold_12m_ago': 720,
        'monthly_sold_24m_ago': 610,
        'seller_count': 6,
        'product_score': 78,
        'sales_trend_score': 32,
        'market_size_score': 25,
        'improvement_potential_score': 8,
        'entry_difficulty_score': 10
    },
    {
        'asin': 'B11SAMPLE5',
        'title': 'ヨガマット 滑らない 初心者向け 厚さ4mm ピラティスマット',
        'price': 1580,
        'rating': 3.9,
        'review_count': 423,
        'current_rank': 542,
        'monthly_sold_current': 420,
        'monthly_sold_6m_ago': 380,
        'monthly_sold_12m_ago': 350,
        'monthly_sold_24m_ago': 320,
        'seller_count': 18,
        'product_score': 65,
        'sales_trend_score': 22,
        'market_size_score': 10,
        'improvement_potential_score': 15,
        'entry_difficulty_score': 7
    },
    {
        'asin': 'B12SAMPLE6',
        'title': '環境配慮 天然ゴム ヨガマット 5mm グリップ力抜群 ストラップ付',
        'price': 5980,
        'rating': 4.5,
        'review_count': 2134,
        'current_rank': 95,
        'monthly_sold_current': 1450,
        'monthly_sold_6m_ago': 1280,
        'monthly_sold_12m_ago': 1100,
        'monthly_sold_24m_ago': 890,
        'seller_count': 4,
        'product_score': 82,
        'sales_trend_score': 35,
        'market_size_score': 30,
        'improvement_potential_score': 5,
        'entry_difficulty_score': 10
    },
    {
        'asin': 'B13SAMPLE7',
        'title': 'ヨガマット ケース付き 6mm TPE 軽量 水洗い可能 滑り止め',
        'price': 2480,
        'rating': 4.0,
        'review_count': 745,
        'current_rank': 312,
        'monthly_sold_current': 680,
        'monthly_sold_6m_ago': 720,
        'monthly_sold_12m_ago': 690,
        'monthly_sold_24m_ago': 650,
        'seller_count': 12,
        'product_score': 70,
        'sales_trend_score': 20,
        'market_size_score': 20,
        'improvement_potential_score': 10,
        'entry_difficulty_score': 7
    },
    {
        'asin': 'B14SAMPLE8',
        'title': 'ヨガマット 大判 200cm×80cm 厚さ10mm トレーニング ストレッチ',
        'price': 3980,
        'rating': 3.7,
        'review_count': 512,
        'current_rank': 425,
        'monthly_sold_current': 520,
        'monthly_sold_6m_ago': 480,
        'monthly_sold_12m_ago': 450,
        'monthly_sold_24m_ago': 420,
        'seller_count': 9,
        'product_score': 66,
        'sales_trend_score': 25,
        'market_size_score': 15,
        'improvement_potential_score': 18,
        'entry_difficulty_score': 9
    },
    {
        'asin': 'B15SAMPLE9',
        'title': 'ヨガマット 折りたたみ 4mm コンパクト 収納便利 自宅トレーニング',
        'price': 2280,
        'rating': 3.5,
        'review_count': 398,
        'current_rank': 638,
        'monthly_sold_current': 350,
        'monthly_sold_6m_ago': 420,
        'monthly_sold_12m_ago': 380,
        'monthly_sold_24m_ago': 360,
        'seller_count': 25,
        'product_score': 62,
        'sales_trend_score': 15,
        'market_size_score': 10,
        'improvement_potential_score': 20,
        'entry_difficulty_score': 5
    },
    {
        'asin': 'B16SAMPLE0',
        'title': 'ヨガマット 高級 厚さ15mm クッション性抜群 ホットヨガ対応',
        'price': 6980,
        'rating': 4.2,
        'review_count': 923,
        'current_rank': 275,
        'monthly_sold_current': 780,
        'monthly_sold_6m_ago': 690,
        'monthly_sold_12m_ago': 620,
        'monthly_sold_24m_ago': 540,
        'seller_count': 7,
        'product_score': 75,
        'sales_trend_score': 30,
        'market_size_score': 20,
        'improvement_potential_score': 12,
        'entry_difficulty_score': 9
    }
])

# サンプルレビューデータ (上位3商品分)
SAMPLE_REVIEWS = {
    'B08SAMPLE1': [
        {
            'rating': 2,
            'title': '1ヶ月で劣化',
            'body': '使い始めて1ヶ月で表面がボロボロになってきました。滑り止めのグリップ力も落ちてきており、ヨガ中に滑って危険です。'
        },
        {
            'rating': 1,
            'title': 'においがきつい',
            'body': '届いてすぐゴム臭がひどく、1週間以上干しても匂いが取れません。部屋中が臭くなり使えません。'
        },
        {
            'rating': 3,
            'title': '厚みはいいが重い',
            'body': '10mmの厚さで膝への負担は減りましたが、重さが1.5kgあり持ち運びには不便。ジムに持っていくには向かないです。'
        },
        {
            'rating': 2,
            'title': '滑り止めがすぐ剥がれた',
            'body': '滑り止め加工が2週間で剥がれてきました。価格の割に品質が悪いと感じます。'
        },
        {
            'rating': 1,
            'title': '配送時に折れ跡',
            'body': '配送時の梱包が悪く、マットに深い折れ跡がついていました。広げても跡が消えず、使いづらいです。'
        }
    ],
    'B09SAMPLE2': [
        {
            'rating': 3,
            'title': '薄すぎる',
            'body': '6mmですが実際は5mm程度しかないように感じます。固い床だと膝が痛くなります。'
        },
        {
            'rating': 2,
            'title': '収納バッグがすぐ破れた',
            'body': '付属の収納バッグの縫い目が弱く、3回使っただけで破れました。バッグだけ別売りしてほしい。'
        },
        {
            'rating': 1,
            'title': '汗で滑る',
            'body': 'ホットヨガで使用したところ、汗で非常に滑りやすく危険でした。グリップ力が全くありません。'
        }
    ],
    'B07SAMPLE3': [
        {
            'rating': 2,
            'title': '折りたたみ部分がすぐダメに',
            'body': '折りたたみ式なのは便利ですが、折り目部分がすぐに割れてボロボロになりました。'
        },
        {
            'rating': 3,
            'title': '軽量だが安定感なし',
            'body': '軽いのはいいですが、薄くて床との密着性が悪く、ポーズ中にずれてしまいます。'
        },
        {
            'rating': 1,
            'title': '色落ちがひどい',
            'body': '使用後に手に色がつき、洗っても色落ちが止まりません。衣類にも色移りしてしまいました。'
        }
    ]
}

# サンプルAI分析結果
SAMPLE_ANALYSIS = {
    'カテゴリ別問題': {
        '品質・耐久性': [
            {'問題': '1-2ヶ月で表面が劣化・ボロボロになる', '頻度': '高', '深刻度': '高'},
            {'問題': '滑り止め加工が短期間で剥がれる', '頻度': '高', '深刻度': '高'},
            {'問題': '折りたたみ部分が割れやすい', '頻度': '中', '深刻度': '中'}
        ],
        '使用感・機能': [
            {'問題': '汗をかくと滑りやすく危険', '頻度': '高', '深刻度': '高'},
            {'問題': '重量が重く持ち運びに不便（1.5kg）', '頻度': '中', '深刻度': '中'},
            {'問題': '床との密着性が悪くずれる', '頻度': '中', '深刻度': '中'}
        ],
        '製品仕様': [
            {'問題': '表記厚みより薄い（6mm→実質5mm）', '頻度': '中', '深刻度': '中'},
            {'問題': '厚みが薄く膝・関節が痛くなる', '頻度': '高', '深刻度': '高'}
        ],
        '配送・梱包': [
            {'問題': '配送時の折れ跡が消えない', '頻度': '中', '深刻度': '中'},
            {'問題': '梱包が雑で商品が破損', '頻度': '低', '深刻度': '中'}
        ],
        '付属品': [
            {'問題': '収納バッグの縫製が弱く破れやすい', '頻度': '高', '深刻度': '中'}
        ],
        'におい・素材': [
            {'問題': 'ゴム臭がきつく、長期間消えない', '頻度': '高', '深刻度': '高'},
            {'問題': '色落ちがひどく衣類に色移り', '頻度': '中', '深刻度': '高'}
        ]
    },
    '改善提案': [
        {
            '提案': '高耐久TPE素材 + 強化滑り止め加工',
            '詳細': '耐久性の高いTPE素材を使用し、滑り止め加工を2層構造に強化。汗をかいても滑らない特殊グリップ加工を施す',
            '実現可能性': '高',
            '期待効果': '品質問題の70%を解決、返品率を50%削減'
        },
        {
            '提案': '軽量化設計（1.0kg以下）+ 改良収納バッグ',
            '詳細': '厚み10mmを維持しつつ軽量素材で1.0kg以下を実現。収納バッグは二重縫製+ナイロン素材で耐久性向上',
            '実現可能性': '中',
            '期待効果': '持ち運び問題を解決、ジム利用者の満足度向上'
        },
        {
            '提案': '無臭加工 + 環境配慮素材',
            '詳細': '特殊脱臭処理を施し、開封直後からにおいゼロを実現。環境に優しいTPE素材でサステナブル訴求',
            '実現可能性': '高',
            '期待効果': 'におい問題を完全解決、エコ意識の高い顧客層を獲得'
        },
        {
            '提案': '厚み保証 + 3年品質保証',
            '詳細': '表記厚み±0.5mm以内を保証。3年間の品質保証で返品・交換対応',
            '実現可能性': '高',
            '期待効果': '信頼性向上、リピート率30%増加'
        }
    ],
    '新商品コンセプト': [
        {
            'コンセプト': 'プロ仕様 超耐久ヨガマット "ZEN PRO"',
            '特徴': [
                '10mm厚 + 軽量1.0kg（業界最軽量）',
                '2層構造滑り止め（汗でも滑らない特殊グリップ）',
                '無臭TPE素材 + 3年品質保証',
                '改良収納バッグ（二重縫製ナイロン）',
                '厚み保証±0.5mm'
            ],
            '想定価格': '¥4,980',
            '差別化ポイント': '競合の問題点を全て解決した「完璧なヨガマット」'
        }
    ]
}

def get_sample_data():
    """サンプルデータを取得"""
    return {
        'products': SAMPLE_PRODUCTS,
        'reviews': SAMPLE_REVIEWS,
        'analysis': SAMPLE_ANALYSIS
    }
