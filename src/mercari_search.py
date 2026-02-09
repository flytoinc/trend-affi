"""
メルカリ商品検索
Playwrightを使用してJavaScriptレンダリング後の商品を取得
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
import time


MERCARI_AMBASSADOR_ID = "3578578619"  # アフィリエイトID


def find_related_products(news_item, limit=5):
    """
    ニュースから関連商品をメルカリで検索
    
    Args:
        news_item: ニュース情報 {'title': str, 'keywords': list}
        limit: 取得する商品数
    
    Returns:
        list: 商品リスト
    """
    keywords = news_item.get('keywords', [])
    
    if not keywords:
        keywords = extract_search_words(news_item['title'])
    
    print(f"検索キーワード: {keywords}")
    
    all_products = []
    
    # 上位2キーワードで検索
    for keyword in keywords[:2]:
        products = search_mercari_with_playwright(keyword, limit=limit)
        all_products.extend(products)
        
        if len(all_products) >= limit:
            break
        
        time.sleep(1)
    
    # 重複除去
    seen_ids = set()
    unique_products = []
    for p in all_products:
        if p['item_id'] not in seen_ids:
            seen_ids.add(p['item_id'])
            unique_products.append(p)
    
    print(f"メルカリ商品: {len(unique_products)}件取得")
    return unique_products[:limit]


def extract_search_words(title):
    """タイトルから検索ワードを抽出"""
    # カッコ内を優先
    matches = re.findall(r'[「『【](.+?)[」』】]', title)
    if matches:
        return matches[:2]
    
    # 固有名詞を抽出
    names = re.findall(r'[ァ-ヶー々\u3400-\u9FFF]{2,8}', title)
    stopwords = {'ニュース', '発表', '出演', '放送', '公開', '話題', '注目', 
                 '最新', '速報', '映画', 'ドラマ', '番組', 'テレビ'}
    
    return [n for n in names if n not in stopwords][:2]


def search_mercari_with_playwright(keyword, limit=5):
    """
    Playwrightを使用してメルカリで商品を検索
    
    検索条件:
    - 最低価格: 10,000円以上
    - ソート: いいね数が多い順
    - 個人の出品のみ
    
    Args:
        keyword: 検索キーワード
        limit: 取得する商品数
    
    Returns:
        list: 商品リスト
    """
    import urllib.parse
    
    # メルカリ検索URL構築
    search_url = (
        f"https://jp.mercari.com/search?"
        f"keyword={urllib.parse.quote(keyword)}"
        f"&sort=num_likes"
        f"&order=desc"
        f"&item_types=mercari"
        f"&price_min=10000"
    )
    
    print(f"メルカリ検索: {keyword}")
    
    try:
        with sync_playwright() as p:
            # ヘッドレスブラウザ起動
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # ページ遷移
            page.goto(search_url, wait_until='networkidle', timeout=30000)
            
            # 商品リンクが表示されるまで待機
            try:
                page.wait_for_selector('a[href^="/item/m"]', timeout=10000)
            except PlaywrightTimeoutError:
                print(f"  → 商品が見つかりませんでした")
                browser.close()
                return []
            
            # 商品リンクを取得
            links = page.query_selector_all('a[href^="/item/m"]')
            
            products = []
            
            for link in links[:limit]:
                try:
                    # hrefからitem IDを取得
                    href = link.get_attribute('href')
                    item_id_match = re.search(r'/item/(m\d+)', href)
                    
                    if not item_id_match:
                        continue
                    
                    item_id = item_id_match.group(1)
                    
                    # タイトルを取得
                    title = link.inner_text().strip()[:100]
                    
                    if not title:
                        title = "メルカリ商品"
                    
                    # 価格を取得（テキストから抽出）
                    price = 0
                    price_match = re.search(r'[¥￥]?\s*(\d{1,3}(?:,\d{3})*|\d+)', title)
                    if price_match:
                        price = int(price_match.group(1).replace(',', ''))
                    
                    # アフィリエイトリンク生成
                    affiliate_url = generate_affiliate_url(item_id)
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'likes': 0,  # いいね数は取得困難
                        'url': f"https://jp.mercari.com/item/{item_id}",
                        'affiliate_url': affiliate_url,
                        'item_id': item_id
                    })
                    
                except Exception as e:
                    print(f"  商品パースエラー: {e}")
                    continue
            
            browser.close()
            
            print(f"  → {len(products)}件取得")
            return products
            
    except Exception as e:
        print(f"メルカリ検索エラー [{keyword}]: {e}")
        return []


def generate_affiliate_url(item_id):
    """
    メルカリアンバサダーのアフィリエイトリンクを生成
    
    Args:
        item_id: メルカリ商品ID (例: m43941834421)
    
    Returns:
        str: アフィリエイトURL
    """
    return f"https://jp.mercari.com/item/{item_id}?afid={MERCARI_AMBASSADOR_ID}"


if __name__ == "__main__":
    # テスト
    test_news = {
        'title': '【BTS】人気グループの新グッズ発売',
        'keywords': ['BTS']
    }
    
    products = find_related_products(test_news)
    for p in products:
        print(f"\n{p['title']}")
        print(f"  ¥{p['price']:,}")
        print(f"  {p['affiliate_url']}")
