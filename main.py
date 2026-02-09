"""
Trend-Affi: 自律型エンタメアフィリエイト・マーケター
オリコンニュース → メルカリ商品選定 → AI投稿生成 → X投稿
"""
import os
import sys
import traceback
from datetime import datetime

from src.oricon_scraper import get_latest_news
from src.mercari_search import find_related_products
from src.ai_generator import generate_post
from src.learning import get_top_posts_insights
from src.x_poster import post_to_x
from src.sheets_manager import SheetsManager


def main():
    """メイン実行関数"""
    print("=" * 60)
    print(f"Trend-Affi 実行開始: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # 環境変数チェック
    required_vars = [
        'GEMINI_API_KEY',
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
        print("\n[1/6] Google Sheets接続...")
        sheets = SheetsManager(
            os.environ['GOOGLE_CREDENTIALS_JSON'],
            os.environ['GOOGLE_SHEET_KEY']
        )
        
        # 2. オリコンニュース取得
        print("\n[2/6] オリコンニュース取得...")
        news_items = get_latest_news(limit=10)
        if not news_items:
            print("ニュースが取得できませんでした")
            return
        
        print(f"取得ニュース: {len(news_items)}件")
        for i, news in enumerate(news_items[:5], 1):
            print(f"  {i}. {news['title'][:50]}...")
        
        # 新規ニュースをtrendnewsシートに記録
        logged_urls = sheets.get_logged_urls()
        new_news_items = [n for n in news_items if n['url'] not in logged_urls]
        
        if new_news_items:
            print(f"\n新規ニュース {len(new_news_items)}件をtrendnewsに記録...")
            sheets.log_news_items(new_news_items)
        
        # 投稿済みニュースを除外
        posted_urls = sheets.get_posted_urls()
        unposted_items = [n for n in news_items if n['url'] not in posted_urls]
        
        if not unposted_items:
            print("新規ニュースがありません（全て投稿済み）")
            return
        
        print(f"\n未投稿ニュース: {len(unposted_items)}件")
        
        # 3. 各ニュースに対してメルカリ商品を検索
        print("\n[3/6] メルカリ商品検索...")
        
        selected_news = None
        selected_product = None
        
        for news in unposted_items[:5]:  # 上位5件まで試行
            print(f"\n検索中: {news['title'][:40]}...")
            products = find_related_products(news)
            
            if products:
                selected_news = news
                selected_product = products[0]
                sheets.update_news_status(news['url'], 'selected', selected_product['title'])
                break
            else:
                sheets.update_news_status(news['url'], 'skipped', '', '商品見つからず')
                print(f"  → 商品なし、スキップ")
        
        if not selected_product:
            print("全ニュースで関連商品が見つかりませんでした")
            return
        
        print(f"\n選択ニュース: {selected_news['title']}")
        print(f"選択商品: {selected_product['title'][:50]}...")
        print(f"価格: ¥{selected_product['price']}")
        
        # 4. 過去の高反応投稿から学習
        print("\n[4/6] 過去データから学習...")
        insights = get_top_posts_insights(sheets)
        print(f"学習インサイト: {insights[:100]}...")
        
        # 5. AI投稿生成
        print("\n[5/6] AI投稿生成...")
        post_text = generate_post(
            news=selected_news,
            product=selected_product,
            insights=insights
        )
        print(f"生成投稿:\n{post_text}")
        
        # 6. X投稿
        print("\n[6/6] X投稿...")
        result = post_to_x(post_text)
        
        if result['success']:
            print(f"投稿成功! Tweet ID: {result['tweet_id']}")
            
            # スプレッドシートに記録
            sheets.record_post(
                news_url=selected_news['url'],
                news_title=selected_news['title'],
                product_title=selected_product['title'],
                product_url=selected_product.get('affiliate_url', selected_product['url']),
                product_price=selected_product['price'],
                post_text=post_text,
                tweet_id=result['tweet_id']
            )
            print("スプレッドシートに記録完了")
        else:
            print(f"投稿失敗: {result['error']}")
            sheets.update_news_status(selected_news['url'], 'error', '', result['error'])
        
        print("\n" + "=" * 60)
        print(f"Trend-Affi 実行完了: {datetime.now().isoformat()}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nエラー発生: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
