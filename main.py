"""
Trend-Affi: 自律型エンタメアフィリエイト・マーケター
Google Trends → メルカリ商品選定 → 投稿生成 → X投稿（2件）
"""
import os
import sys
import traceback
from datetime import datetime

from src.google_trends_scraper import get_trending_topics
from src.trend_researcher import research_trend_reason
from src.mercari_search import find_related_products
from src.ai_generator import generate_post
from src.x_poster import post_to_x
from src.sheets_manager import SheetsManager


def main():
    """メイン実行関数"""
    print("=" * 60)
    print(f"Trend-Affi 実行開始: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # 環境変数チェック
    required_vars = [
        'X_API_KEY', 'X_API_SECRET', 
        'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET',
        'GOOGLE_CREDENTIALS_JSON', 'GOOGLE_SHEET_KEY'
    ]
    
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        print(f"Error: Missing environment variables: {missing}")
        sys.exit(1)
    
    try:
        # 1. Google Sheets接続
        print("\n[1/5] Google Sheets接続...")
        sheets = SheetsManager(
            os.environ['GOOGLE_CREDENTIALS_JSON'],
            os.environ['GOOGLE_SHEET_KEY']
        )
        
        # 2. Google Trendsから話題のトレンドを取得
        print("\n[2/5] Google Trendsからトレンド取得...")
        trends = get_trending_topics(limit=10)
        if not trends:
            print("トレンドが取得できませんでした")
            return
        
        print(f"取得トレンド: {len(trends)}件")
        for i, trend in enumerate(trends[:5], 1):
            print(f"  {i}. {trend['name']}")
        
        # 過去48時間のトレンドを取得（重複防止）
        recent_trends = sheets.get_recent_trends(hours=48)
        print(f"\n過去48時間の投稿済みトレンド: {len(recent_trends)}件")
        
        # 未投稿のトレンドをフィルタリング
        new_trends = [t for t in trends if t['name'] not in recent_trends]
        
        if not new_trends:
            print("新規トレンドがありません（全て48時間以内に投稿済み）")
            return
        
        print(f"未投稿トレンド: {len(new_trends)}件")
        
        # 上位2件のトレンドを処理
        posts_count = 0
        target_count = 2
        
        for trend in new_trends[:5]:  # 最大5件まで試行
            if posts_count >= target_count:
                break
            
            print(f"\n{'='*60}")
            print(f"処理中 ({posts_count + 1}/{target_count}): {trend['name']}")
            print(f"{'='*60}")
            
            # 3. トレンドの理由を調査
            print("\n[3/5] トレンド理由調査...")
            trend_reason = research_trend_reason(trend)
            print(f"理由: {trend_reason}")
            
            # 4. メルカリで関連商品を検索
            print("\n[4/5] メルカリ商品検索...")
            
            # トレンド名をキーワードとして使用
            news_item = {
                'title': trend['name'],
                'keywords': [trend['name']],
                'url': ''
            }
            
            products = find_related_products(news_item, limit=5)
            
            if not products:
                print(f"  → 商品なし、スキップ")
                continue
            
            selected_product = products[0]
            print(f"選択商品: {selected_product['title'][:50]}...")
            print(f"価格: ¥{selected_product['price']:,}")
            
            # 5. 投稿生成
            print("\n[5/5] 投稿生成...")
            
            trend_data = {
                'name': trend['name'],
                'reason': trend_reason,
                'keywords': [trend['name']]
            }
            
            post_text = generate_post(trend_data, selected_product)
            print(f"生成投稿:\n{post_text}")
            
            # 6. X投稿
            print("\n[6/6] X投稿...")
            result = post_to_x(post_text)
            
            if result['success']:
                print(f"投稿成功! Tweet ID: {result['tweet_id']}")
                
                # スプレッドシートに記録
                trend_record = {
                    'trend_name': trend['name'],
                    'trend_reason': trend_reason,
                    'title': trend['name'],
                    'url': '',
                    'keywords': [trend['name']]
                }
                
                sheets.log_news_items([trend_record])
                
                sheets.record_post(
                    news_url='',
                    news_title=trend['name'],
                    product_title=selected_product['title'],
                    product_url=selected_product.get('affiliate_url', selected_product['url']),
                    product_price=selected_product['price'],
                    post_text=post_text,
                    tweet_id=result['tweet_id']
                )
                print("スプレッドシートに記録完了")
                
                posts_count += 1
            else:
                print(f"投稿失敗: {result['error']}")
                continue
        
        print(f"\n{'='*60}")
        print(f"投稿完了: {posts_count}件")
        print(f"Trend-Affi 実行完了: {datetime.now().isoformat()}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nエラー発生: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
