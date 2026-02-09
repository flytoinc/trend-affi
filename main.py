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
        news_items = get_latest_news(limit=5)
        if not news_items:
            print("ニュースが取得できませんでした")
            return
        
        print(f"取得ニュース: {len(news_items)}件")
        for i, news in enumerate(news_items[:3], 1):
            print(f"  {i}. {news['title'][:50]}...")
        
        # 投稿済みニュースを除外
        posted_urls = sheets.get_posted_urls()
        new_items = [n for n in news_items if n['url'] not in posted_urls]
        
        if not new_items:
            print("新規ニュースがありません")
            return
        
        # 最新ニュースを選択
        selected_news = new_items[0]
        print(f"\n選択ニュース: {selected_news['title']}")
        
        # 3. メルカリ商品検索
        print("\n[3/6] メルカリ商品検索...")
        products = find_related_products(selected_news)
        
        if not products:
            print("関連商品が見つかりませんでした")
            return
        
        selected_product = products[0]
        print(f"選択商品: {selected_product['title'][:50]}...")
        print(f"価格: ¥{selected_product['price']}")
        print(f"いいね数: {selected_product.get('likes', 0)}")
        
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
        print(f"生成投稿: {post_text[:100]}...")
        
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
                product_url=selected_product['url'],
                product_price=selected_product['price'],
                post_text=post_text,
                tweet_id=result['tweet_id']
            )
            print("スプレッドシートに記録完了")
        else:
            print(f"投稿失敗: {result['error']}")
        
        print("\n" + "=" * 60)
        print(f"Trend-Affi 実行完了: {datetime.now().isoformat()}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nエラー発生: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
