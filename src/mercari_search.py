"""
メルカリ商品検索
ニュースキーワードから関連商品を検索し、アフィリエイトリンクを生成
"""
import requests
from bs4 import BeautifulSoup
import re
import time


def find_related_products(news_item, limit=5):
    """
    ニュースから関連商品をメルカリで検索
    
    Args:
        news_item: ニュース情報 {title, keywords, ...}
        limit: 取得件数
    
    Returns:
        list: 商品情報リスト（いいね数・価格でソート済み）
    """
    keywords = news_item.get('keywords', [])
    
    if not keywords:
        # キーワードがない場合はタイトルから抽出
        keywords = extract_search_words(news_item['title'])
    
    all_products = []
    
    for keyword in keywords[:3]:  # 上位3キーワードで検索
        # 検索ワードの拡張
        search_terms = expand_search_terms(keyword)
        
        for term in search_terms[:2]:
            products = search_mercari(term)
            all_products.extend(products)
            time.sleep(0.5)  # レート制限対策
    
    # 重複除去
    seen_urls = set()
    unique_products = []
    for p in all_products:
        if p['url'] not in seen_urls:
            seen_urls.add(p['url'])
            unique_products.append(p)
    
    # ソート: いいね数×価格の高い順（売れそう&高単価）
    unique_products.sort(
        key=lambda x: (x.get('likes', 0) * 10 + x.get('price', 0) / 100),
        reverse=True
    )
    
    return unique_products[:limit]


def expand_search_terms(keyword):
    """
    キーワードを検索用に拡張
    例: 「山田太郎」→「山田太郎 グッズ」「山田太郎 写真集」等
    """
    suffixes = ['グッズ', '写真集', 'CD', 'DVD', 'ポスター', 'クリアファイル', 'アクスタ']
    
    terms = [keyword]  # 元のキーワードも含む
    
    for suffix in suffixes[:3]:
        terms.append(f"{keyword} {suffix}")
    
    return terms


def extract_search_words(title):
    """タイトルから検索ワードを抽出"""
    # カッコ内を優先
    matches = re.findall(r'[「『【](.+?)[」』】]', title)
    if matches:
        return matches[:2]
    
    # 固有名詞を抽出
    names = re.findall(r'[ァ-ヶー々\u3400-\u9FFF]{2,6}', title)
    stopwords = {'ニュース', '発表', '出演', '放送', '公開'}
    
    return [n for n in names if n not in stopwords][:2]


def search_mercari(keyword, limit=10):
    """
    メルカリで商品を検索
    
    Args:
        keyword: 検索キーワード
        limit: 取得件数
    
    Returns:
        list: 商品情報リスト [{title, price, likes, url, affiliate_url}]
    """
    # メルカリ検索URL
    search_url = f"https://jp.mercari.com/search?keyword={requests.utils.quote(keyword)}&status=on_sale"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        products = []
        
        # 商品リスト取得（セレクタは変更される可能性あり）
        items = soup.select('[data-testid="item-cell"], li[data-testid], div.items-box')
        
        if not items:
            items = soup.select('a[href*="/item/"]')
        
        for item in items[:limit]:
            try:
                # URL
                if item.name == 'a':
                    link = item
                else:
                    link = item.select_one('a[href*="/item/"]')
                
                if not link:
                    continue
                
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = f"https://jp.mercari.com{href}"
                
                # 商品ID抽出
                item_id_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
                if not item_id_match:
                    continue
                
                item_id = item_id_match.group(1)
                
                # タイトル
                title_elem = item.select_one('span, p, .item-name')
                title = title_elem.get_text(strip=True) if title_elem else "商品"
                
                # 価格
                price_elem = item.select_one('[class*="price"], .items-box-price')
                price_text = price_elem.get_text(strip=True) if price_elem else "0"
                price = int(re.sub(r'[^\d]', '', price_text) or 0)
                
                # いいね数（取得できない場合は0）
                likes = 0
                likes_elem = item.select_one('[class*="like"], .items-box-like')
                if likes_elem:
                    likes_text = likes_elem.get_text(strip=True)
                    likes_match = re.search(r'\d+', likes_text)
                    likes = int(likes_match.group()) if likes_match else 0
                
                # アフィリエイトリンク生成
                affiliate_url = generate_affiliate_url(item_id)
                
                products.append({
                    'title': title[:100],
                    'price': price,
                    'likes': likes,
                    'url': href,
                    'affiliate_url': affiliate_url,
                    'item_id': item_id
                })
                
            except Exception as e:
                continue
        
        print(f"メルカリ検索 [{keyword}]: {len(products)}件")
        return products
        
    except Exception as e:
        print(f"メルカリ検索エラー [{keyword}]: {e}")
        return []


def generate_affiliate_url(item_id):
    """
    メルカリアンバサダーのアフィリエイトリンクを生成
    
    Note: 実際のアンバサダーURLフォーマットに合わせて調整が必要
    """
    # 基本的なアフィリエイトURL形式
    # 実際のメルカリアンバサダーのリンク形式に変更してください
    base_url = "https://jp.mercari.com/item/"
    
    # アンバサダーパラメータ（例）
    # 実際のアフィリエイトIDに変更してください
    affiliate_param = "?afid=trend_affi"
    
    return f"{base_url}{item_id}{affiliate_param}"


if __name__ == "__main__":
    # テスト
    test_news = {
        'title': '【速報】人気アイドルグループ「乃木坂46」新メンバー発表',
        'keywords': ['乃木坂46']
    }
    
    products = find_related_products(test_news)
    for p in products:
        print(f"\n{p['title']}")
        print(f"  ¥{p['price']} / {p['likes']}いいね")
        print(f"  {p['affiliate_url']}")
