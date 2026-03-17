"""
Xトレンドスクレイパー
trends24.in/japan からXの日本トレンドを取得
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re


def get_x_trending_topics(limit=10):
    """
    X (Twitter) の日本トレンドを取得
    
    Args:
        limit: 取得するトレンド数
    
    Returns:
        list: [{'name': str, 'traffic': str, 'articles': []}, ...]
    """
    url = "https://trends24.in/japan/"
    
    print("Xトレンド取得中...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # トレンドリストが表示されるまで待機
            try:
                page.wait_for_selector('ol.trend-card__list', timeout=15000)
            except PlaywrightTimeoutError:
                print("  → トレンドリストが見つかりませんでした")
                browser.close()
                return []
            
            # 最新のトレンドカード（最初のol）からトレンドを取得
            trend_items = page.query_selector_all('ol.trend-card__list:first-of-type li a')
            
            trends = []
            seen_names = set()
            
            for item in trend_items:
                if len(trends) >= limit:
                    break
                
                try:
                    trend_name = item.inner_text().strip()
                    
                    # ハッシュタグの # を除去して正規化
                    clean_name = trend_name.lstrip('#').strip()
                    
                    if not clean_name or len(clean_name) < 2:
                        continue
                    
                    # 重複チェック
                    if clean_name.lower() in seen_names:
                        continue
                    seen_names.add(clean_name.lower())
                    
                    trends.append({
                        'name': clean_name,
                        'traffic': '',
                        'articles': [],
                        'source': 'x_trends'
                    })
                    
                except Exception as e:
                    print(f"  トレンドパースエラー: {e}")
                    continue
            
            browser.close()
            
            print(f"  → {len(trends)}件取得")
            return trends
            
    except Exception as e:
        print(f"Xトレンド取得エラー: {e}")
        return []


if __name__ == "__main__":
    # テスト
    trends = get_x_trending_topics(10)
    for i, trend in enumerate(trends, 1):
        print(f"{i}. {trend['name']}")
