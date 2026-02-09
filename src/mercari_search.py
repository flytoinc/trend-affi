"""
メルカリ商品検索
Google検索経由でメルカリ商品を取得（メルカリの動的レンダリング回避）
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import os


def find_related_products(news_item, limit=5):
    """
    ニュースから関連商品をメルカリで検索
    Google検索経由で商品を取得
    """
    keywords = news_item.get('keywords', [])
    
    if not keywords:
        keywords = extract_search_words(news_item['title'])
    
    print(f"検索キーワード: {keywords}")
    
    all_products = []
    
    for keyword in keywords[:2]:  # 上位2キーワード
        products = search_mercari_via_google(keyword)
        all_products.extend(products)
        time.sleep(0.5)
    
    # 重複除去
    seen_ids = set()
    unique_products = []
    for p in all_products:
        if p['item_id'] not in seen_ids:
            seen_ids.add(p['item_id'])
            unique_products.append(p)
    
    # 価格でソート（高単価優先）
    unique_products.sort(key=lambda x: x.get('price', 0), reverse=True)
    
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


def search_mercari_via_google(keyword, limit=10):
    """
    Google検索経由でメルカリ商品を取得
    """
    # site:jp.mercari.com で検索
    query = f"site:jp.mercari.com/item {keyword}"
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=20"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        
        # Google検索結果からメルカリURLを抽出
        for link in soup.select('a[href*="jp.mercari.com/item/"]'):
            href = link.get('href', '')
            
            # GoogleのリダイレクトURLから実際のURLを抽出
            if '/url?q=' in href:
                match = re.search(r'/url\?q=(https://jp\.mercari\.com/item/[^&]+)', href)
                if match:
                    href = match.group(1)
            
            # 商品IDを抽出
            item_id_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
            if not item_id_match:
                continue
            
            item_id = item_id_match.group(1)
            
            # タイトルを取得
            title_elem = link.select_one('h3') or link
            title = title_elem.get_text(strip=True)[:100] if title_elem else "メルカリ商品"
            
            # 価格抽出（タイトルから）
            price = 0
            price_match = re.search(r'[¥￥]?\s*(\d{1,3}(?:,\d{3})*|\d+)\s*円?', title)
            if price_match:
                price = int(price_match.group(1).replace(',', ''))
            
            affiliate_url = generate_affiliate_url(item_id)
            
            products.append({
                'title': title,
                'price': price,
                'likes': 0,  # Google検索からは取得不可
                'url': f"https://jp.mercari.com/item/{item_id}",
                'affiliate_url': affiliate_url,
                'item_id': item_id
            })
            
            if len(products) >= limit:
                break
        
        print(f"Google検索 [{keyword}]: {len(products)}件")
        return products
        
    except Exception as e:
        print(f"Google検索エラー [{keyword}]: {e}")
        return []


def generate_affiliate_url(item_id):
    """
    メルカリアンバサダーのアフィリエイトリンクを生成
    
    Note: 実際のメルカリアンバサダーURLフォーマットに変更してください
    """
    # メルカリアンバサダーの基本URL形式
    # 実際のアフィリエイトIDを設定してください
    ambassador_id = os.environ.get('MERCARI_AMBASSADOR_ID', '')
    
    if ambassador_id:
        # アンバサダーリンク形式（要確認）
        return f"https://jp.mercari.com/item/{item_id}?afid={ambassador_id}"
    else:
        # 通常のリンク
        return f"https://jp.mercari.com/item/{item_id}"


if __name__ == "__main__":
    # テスト
    test_news = {
        'title': '【速報】人気アイドルグループ「乃木坂46」新メンバー発表',
        'keywords': ['乃木坂46']
    }
    
    products = find_related_products(test_news)
    for p in products:
        print(f"\n{p['title']}")
        print(f"  ¥{p['price']}")
        print(f"  {p['affiliate_url']}")
