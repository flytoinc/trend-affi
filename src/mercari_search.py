"""
メルカリ商品検索
Playwrightを使用してJavaScriptレンダリング後の商品を取得
Gemini APIによる意味的な商品マッチング検証付き
"""
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
import time

try:
    import google.generativeai as genai
except ImportError:
    genai = None


MERCARI_AMBASSADOR_ID = "3578578619"  # アフィリエイトID


def find_related_products(news_item, limit=5, trend_data=None):
    """
    ニュースから関連商品をメルカリで検索
    Gemini APIで意味的な関連性を検証し、無関係な商品を除外
    
    Args:
        news_item: ニュース情報 {'title': str, 'keywords': list}
        limit: 取得する商品数
        trend_data: トレンド情報 {'name': str, 'reason': str} (意味マッチング用)
    
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
        products = search_mercari_with_playwright(keyword, limit=limit * 2)
        all_products.extend(products)
        
        if len(all_products) >= limit * 2:
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
    
    # Gemini APIで意味的な関連性を検証
    if trend_data and unique_products:
        validated = validate_products_relevance(trend_data, unique_products)
        if validated:
            print(f"意味マッチング後: {len(validated)}件")
            return validated[:limit]
        else:
            print("意味マッチングで関連商品なし、テキストマッチ結果を使用")
    
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
            
            # ページ遷移（タイムアウト延長、待機戦略変更）
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            
            # 商品リンクが表示されるまで待機
            try:
                page.wait_for_selector('a[href^="/item/m"]', timeout=15000)
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
                    title = link.inner_text().strip()
                    
                    # US$表記を削除
                    title = title.replace('US$', '').replace('$', '').strip()
                    # 連続する空白を1つに
                    title = re.sub(r'\s+', ' ', title)
                    # 最大100文字
                    title = title[:100]
                    
                    if not title:
                        title = "メルカリ商品"
                    
                    # 価格を取得（専用要素 → テキストからのフォールバック）
                    price = 0
                    price_elem = link.query_selector('[class*="price"], [class*="Price"], span[class*="number"]')
                    if price_elem:
                        price_text = price_elem.inner_text().strip()
                        price_match = re.search(r'[\d,]+', price_text)
                        if price_match:
                            price = int(price_match.group().replace(',', ''))
                    
                    if price == 0:
                        # テキスト全体から価格パターンを検索
                        price_match = re.search(r'[¥￥]\s*([\d,]+)', title)
                        if price_match:
                            price = int(price_match.group(1).replace(',', ''))
                    
                    # 商品画像URLを取得
                    image_url = ''
                    img_elem = link.query_selector('img')
                    if img_elem:
                        image_url = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or ''
                        # 小さいサムネイルを大きい画像に変換
                        if image_url and 'static.mercdn.net' in image_url:
                            image_url = re.sub(r'/w/\d+/', '/w/640/', image_url)
                    
                    # アフィリエイトリンク生成
                    affiliate_url = generate_affiliate_url(item_id)
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'likes': 0,
                        'url': f"https://jp.mercari.com/item/{item_id}",
                        'affiliate_url': affiliate_url,
                        'item_id': item_id,
                        'image_url': image_url
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


def validate_products_relevance(trend_data, products, threshold=6):
    """
    Gemini APIでトレンドと商品の意味的な関連性を検証
    
    Args:
        trend_data: トレンド情報 {'name': str, 'reason': str}
        products: 商品リスト
        threshold: 関連性スコアの閾値（1-10、この値以上で採用）
    
    Returns:
        list: 関連性の高い商品のみのリスト
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key or not genai:
        print("Gemini API未設定、意味マッチングスキップ")
        return products
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    trend_name = trend_data.get('name', '')
    trend_reason = trend_data.get('reason', '')
    
    # 商品リストをまとめて評価（API呼び出しを最小限にする）
    product_list_text = "\n".join([
        f"{i+1}. {p['title'][:80]} (¥{p.get('price', 0):,})"
        for i, p in enumerate(products[:10])
    ])
    
    prompt = f"""以下のトレンドと商品リストの関連性を評価してください。

【トレンド】
名前: {trend_name}
理由: {trend_reason}

【商品リスト】
{product_list_text}

各商品について、トレンドとの関連性を1-10のスコアで評価してください。
- 10: 直接的に関連（同じ人物/作品のグッズなど）
- 7-9: 強い関連（関連するジャンルやカテゴリ）
- 4-6: 弱い関連（間接的な関連）
- 1-3: ほぼ無関係

出力形式（各行に番号とスコアのみ）:
1:8
2:3
3:7
..."""
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # スコアをパース
        scores = {}
        for line in result_text.split('\n'):
            match = re.match(r'(\d+)\s*[:：]\s*(\d+)', line.strip())
            if match:
                idx = int(match.group(1)) - 1
                score = int(match.group(2))
                scores[idx] = score
        
        # 閾値以上の商品のみ返す
        validated = []
        for i, product in enumerate(products[:10]):
            score = scores.get(i, 0)
            if score >= threshold:
                product['relevance_score'] = score
                validated.append(product)
                print(f"  ✓ [{score}/10] {product['title'][:50]}")
            else:
                print(f"  ✗ [{score}/10] {product['title'][:50]}")
        
        # スコア順にソート
        validated.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return validated
        
    except Exception as e:
        print(f"意味マッチングエラー: {e}")
        return products


if __name__ == "__main__":
    # テスト
    test_news = {
        'title': '【BTS】人気グループの新グッズ発売',
        'keywords': ['BTS']
    }
    test_trend = {
        'name': 'BTS',
        'reason': '新アルバム発売で話題に'
    }
    
    products = find_related_products(test_news, trend_data=test_trend)
    for p in products:
        print(f"\n{p['title']}")
        print(f"  ¥{p['price']:,}")
        print(f"  {p['affiliate_url']}")
        if 'relevance_score' in p:
            print(f"  関連性: {p['relevance_score']}/10")
