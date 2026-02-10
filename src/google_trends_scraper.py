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
            
            # トレンド行が表示されるまで待機
            try:
                page.wait_for_selector('tr.enOdEe-wZVHld-xMbwt', timeout=15000)
            except PlaywrightTimeoutError:
                print("  → トレンドが見つかりませんでした")
                browser.close()
                return []
            
            # トレンド行を取得
            trend_rows = page.query_selector_all('tr.enOdEe-wZVHld-xMbwt')
            
            trends = []
            
            for i, row in enumerate(trend_rows[:limit]):
                try:
                    # トレンド名を取得（2列目のdiv）
                    name_elem = row.query_selector('td:nth-child(2) div.mZ3RIc')
                    if not name_elem:
                        continue
                    
                    trend_name = name_elem.inner_text().strip()
                    
                    # 行をクリックしてサイドバーを開く
                    row.click()
                    
                    # サイドバーのニューストピックを待機
                    try:
                        page.wait_for_selector('div.jDtQ5', timeout=5000)
                        
                        # ニューストピックのタイトルを取得（理由として使用）
                        news_elem = page.query_selector('div.jDtQ5')
                        news_title = news_elem.inner_text().strip() if news_elem else ""
                        
                        trends.append({
                            'name': trend_name,
                            'traffic': '',
                            'articles': [{'title': news_title, 'url': ''}] if news_title else []
                        })
                        
                    except PlaywrightTimeoutError:
                        # ニューストピックがない場合
                        trends.append({
                            'name': trend_name,
                            'traffic': '',
                            'articles': []
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
        print(f"   Articles: {len(trend['articles'])}件")
        if trend['articles']:
            print(f"   Reason: {trend['articles'][0]['title'][:50]}...")
