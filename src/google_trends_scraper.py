"""
Google Trendsスクレイパー
Playwrightを使用してGoogle Trendsから話題のトレンドを取得
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re


def get_trending_topics(limit=10):
    """
    Google Trendsから話題のトレンドを取得
    
    Args:
        limit: 取得するトレンド数
    
    Returns:
        list: [{'name': str, 'traffic': str, 'articles': []}, ...]
    """
    url = "https://trends.google.co.jp/trending?geo=JP"
    
    print(f"Google Trendsからトレンド取得中...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # ページ遷移
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # トレンド要素が表示されるまで待機
            try:
                page.wait_for_selector('.feed-item', timeout=15000)
            except PlaywrightTimeoutError:
                print("  → トレンドが見つかりませんでした")
                browser.close()
                return []
            
            # トレンド要素を取得
            trend_elements = page.query_selector_all('.feed-item')
            
            trends = []
            
            for elem in trend_elements[:limit]:
                try:
                    # トレンド名を取得
                    title_elem = elem.query_selector('.title a')
                    if not title_elem:
                        continue
                    
                    trend_name = title_elem.inner_text().strip()
                    
                    # トラフィック情報を取得
                    traffic_elem = elem.query_selector('.summary-text')
                    traffic = traffic_elem.inner_text().strip() if traffic_elem else ""
                    
                    # 関連記事リンクを取得（理由調査用）
                    article_links = []
                    article_elems = elem.query_selector_all('.article-title a')
                    for article in article_elems[:3]:
                        article_links.append({
                            'title': article.inner_text().strip(),
                            'url': article.get_attribute('href')
                        })
                    
                    trends.append({
                        'name': trend_name,
                        'traffic': traffic,
                        'articles': article_links
                    })
                    
                except Exception as e:
                    print(f"  トレンドパースエラー: {e}")
                    continue
            
            browser.close()
            
            print(f"  → {len(trends)}件取得")
            return trends
            
    except Exception as e:
        print(f"Google Trends取得エラー: {e}")
        return []


if __name__ == "__main__":
    # テスト
    trends = get_trending_topics(5)
    for i, trend in enumerate(trends, 1):
        print(f"\n{i}. {trend['name']}")
        print(f"   Traffic: {trend['traffic']}")
        print(f"   Articles: {len(trend['articles'])}件")
