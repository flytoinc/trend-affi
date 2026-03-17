"""
Xエンゲージメント検索
トレンドワードに関連する高インプレッション投稿をPlaywrightで検索
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
import time


def find_popular_tweet(keyword, min_likes=50):
    """
    トレンドワードで人気の投稿を検索し、最もエンゲージメントの高い投稿を返す
    
    Args:
        keyword: 検索キーワード（トレンドワード）
        min_likes: 最低いいね数フィルタ
    
    Returns:
        dict or None: {'tweet_id': str, 'author': str, 'text': str, 'likes': int, 'url': str}
    """
    import urllib.parse
    
    # X検索URL（人気順）
    search_url = (
        f"https://x.com/search?"
        f"q={urllib.parse.quote(keyword)}"
        f"&src=typed_query&f=top"
    )
    
    print(f"X検索: {keyword} (人気順)")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            
            # ツイートが表示されるまで待機
            try:
                page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)
            except PlaywrightTimeoutError:
                print("  → ツイートが見つかりませんでした")
                browser.close()
                return None
            
            # 少し待ってからスクロールして追加ツイートを読み込む
            time.sleep(2)
            page.mouse.wheel(0, 500)
            time.sleep(1)
            
            # ツイートを取得
            tweets = page.query_selector_all('article[data-testid="tweet"]')
            
            best_tweet = None
            best_likes = 0
            
            for tweet in tweets[:10]:  # 上位10件を調査
                try:
                    tweet_data = _parse_tweet(tweet, page)
                    
                    if not tweet_data or not tweet_data.get('tweet_id'):
                        continue
                    
                    likes = tweet_data.get('likes', 0)
                    
                    # 最低いいね数フィルタ
                    if likes < min_likes:
                        continue
                    
                    # 自分のアカウントの投稿は除外（引用RT対象外）
                    # （アカウント名チェックは環境変数から取得できないためスキップ）
                    
                    # 最もいいね数が多い投稿を選択
                    if likes > best_likes:
                        best_likes = likes
                        best_tweet = tweet_data
                        
                except Exception as e:
                    print(f"  ツイートパースエラー: {e}")
                    continue
            
            browser.close()
            
            if best_tweet:
                print(f"  → 人気投稿発見: {best_tweet['likes']}いいね")
                print(f"    @{best_tweet['author']}: {best_tweet['text'][:60]}...")
            else:
                print(f"  → 条件を満たす投稿なし (min_likes={min_likes})")
            
            return best_tweet
            
    except Exception as e:
        print(f"X検索エラー: {e}")
        return None


def _parse_tweet(tweet_elem, page):
    """
    ツイート要素からデータを抽出
    
    Args:
        tweet_elem: Playwright要素
        page: Playwrightページ
    
    Returns:
        dict: {'tweet_id': str, 'author': str, 'text': str, 'likes': int, 'url': str}
    """
    try:
        # ツイートリンクからIDを取得
        tweet_links = tweet_elem.query_selector_all('a[href*="/status/"]')
        tweet_id = None
        tweet_url = None
        
        for link in tweet_links:
            href = link.get_attribute('href') or ''
            match = re.search(r'/status/(\d+)', href)
            if match:
                tweet_id = match.group(1)
                tweet_url = f"https://x.com{href}" if not href.startswith('http') else href
                break
        
        if not tweet_id:
            return None
        
        # ユーザー名を取得
        author = ''
        user_link = tweet_elem.query_selector('a[href^="/"][role="link"] span')
        if user_link:
            author_text = user_link.inner_text().strip()
            author = author_text.lstrip('@')
        
        # ツイートテキストを取得
        text = ''
        text_elem = tweet_elem.query_selector('div[data-testid="tweetText"]')
        if text_elem:
            text = text_elem.inner_text().strip()
        
        # いいね数を取得
        likes = _parse_engagement_count(tweet_elem, 'like')
        
        return {
            'tweet_id': tweet_id,
            'author': author,
            'text': text[:200],
            'likes': likes,
            'url': tweet_url
        }
        
    except Exception as e:
        return None


def _parse_engagement_count(tweet_elem, metric_type):
    """
    エンゲージメント数をパース（いいね、RT等）
    
    Args:
        tweet_elem: ツイート要素
        metric_type: 'like', 'retweet', 'reply'
    
    Returns:
        int: カウント
    """
    try:
        # data-testid で特定
        button = tweet_elem.query_selector(f'button[data-testid="{metric_type}"]')
        if not button:
            return 0
        
        aria_label = button.get_attribute('aria-label') or ''
        
        # "123 Likes" や "1,234 いいね" のような形式からパース
        match = re.search(r'([\d,]+)', aria_label)
        if match:
            return int(match.group(1).replace(',', ''))
        
        # ボタン内のテキストからもトライ
        text = button.inner_text().strip()
        if text:
            # K/M表記を処理
            text = text.replace(',', '')
            if 'K' in text.upper():
                return int(float(text.upper().replace('K', '')) * 1000)
            elif 'M' in text.upper():
                return int(float(text.upper().replace('M', '')) * 1000000)
            elif text.isdigit():
                return int(text)
        
        return 0
        
    except Exception:
        return 0


if __name__ == "__main__":
    # テスト
    result = find_popular_tweet("仲間由紀恵", min_likes=10)
    if result:
        print(f"\n=== 最も人気の投稿 ===")
        print(f"ID: {result['tweet_id']}")
        print(f"@{result['author']}")
        print(f"テキスト: {result['text']}")
        print(f"いいね: {result['likes']}")
        print(f"URL: {result['url']}")
    else:
        print("人気投稿が見つかりませんでした")
