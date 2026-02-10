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
                    
                    # サイドバーのニューストピックを待機（タイムアウトを10秒に延長）
                    try:
                        page.wait_for_selector('div.jDtQ5', timeout=10000)
                        
                        # 複数のニューストピックのタイトルを取得
                        news_elems = page.query_selector_all('div.jDtQ5')
                        article_titles = []
                        
                        for news_elem in news_elems[:5]:  # 最大5件取得
                            full_text = news_elem.inner_text().strip()
                            # 最初の行のみを取得（メタ情報を除外）
                            first_line = full_text.split('\n')[0].strip()
                            if first_line:
                                article_titles.append(first_line)
                        
                        # 記事タイトルがある場合
                        if article_titles:
                            # 最も長いタイトルを選択（50文字以上を優先）
                            long_titles = [t for t in article_titles if len(t) >= 50]
                            if long_titles:
                                best_title = max(long_titles, key=len)
                            else:
                                best_title = max(article_titles, key=len)
                            
                            trends.append({
                                'name': trend_name,
                                'traffic': '',
                                'articles': [{'title': best_title, 'url': ''}]
                            })
                        else:
                            # タイトルが取得できない場合
                            trends.append({
                                'name': trend_name,
                                'traffic': '',
                                'articles': []
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
            title = trend['articles'][0]['title']
            print(f"   Reason ({len(title)}文字): {title[:80]}...")
