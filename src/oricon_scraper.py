"""
オリコンニューススクレイパー
エンタメニュースの最新記事を取得
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


def get_latest_news(limit=10):
    """
    オリコンニュースからエンタメ最新記事を取得
    
    Returns:
        list: ニュース記事のリスト [{title, url, summary, keywords}]
    """
    url = "https://www.oricon.co.jp/news/entertainment/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # エンコーディングを自動検出（apparent_encoding を使用）
        if response.encoding.lower() == 'iso-8859-1':
            response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        
        news_items = []
        
        # オリコンの構造に合わせたセレクタ
        articles = soup.select('article.news-list-item, div.news-card, li.news-item')
        
        if not articles:
            # より汎用的なセレクタ
            articles = soup.select('a[href*="/news/"][href*=".html"]')
        
        if not articles:
            articles = soup.select('a[href*="/news/"]')
        
        print(f"取得要素数: {len(articles)}")
        
        for article in articles[:limit * 3]:
            try:
                # URLとタイトル取得
                if article.name == 'a':
                    link = article
                    # タイトルはリンク内のテキストまたはimg alt
                    title = link.get_text(strip=True)
                    if not title:
                        img = link.select_one('img')
                        title = img.get('alt', '') if img else ''
                else:
                    link = article.select_one('a[href*="/news/"]')
                    title_elem = article.select_one('h2, h3, p.title, .headline, span')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not link:
                    continue
                
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = f"https://www.oricon.co.jp{href}"
                
                if not title:
                    title = link.get_text(strip=True)
                
                # バリデーション
                if not title or len(title) < 5 or '/news/' not in href:
                    continue
                
                # 重複チェック
                if any(n['url'] == href for n in news_items):
                    continue
                
                # キーワード抽出
                keywords = extract_keywords(title)
                
                print(f"  取得: {title[:40]}... keywords={keywords}")
                
                news_items.append({
                    'title': title,
                    'url': href,
                    'summary': title,
                    'keywords': keywords,
                    'scraped_at': datetime.now().isoformat()
                })
                
                if len(news_items) >= limit:
                    break
                
            except Exception as e:
                print(f"記事パースエラー: {e}")
                continue
        
        print(f"オリコンニュース: {len(news_items)}件取得")
        return news_items
        
    except Exception as e:
        print(f"オリコンニュース取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return []


def extract_keywords(text):
    """タレント名・作品名等のキーワードを抽出"""
    keywords = []
    
    # カッコ内のテキストを優先的に抽出
    bracket_patterns = [
        r'「([^」]+)」',    # 「」
        r'『([^』]+)』',    # 『』
        r'【([^】]+)】',    # 【】
        r'"([^"]+)"',       # ""
    ]
    
    for pattern in bracket_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if 2 <= len(match) <= 20:  # 適切な長さ
                keywords.append(match)
    
    # 固有名詞らしき連続した日本語を抽出
    # カタカナ・漢字の連続
    name_pattern = r'[ァ-ヶー々〇〻\u3400-\u9FFF]{2,10}'
    names = re.findall(name_pattern, text)
    
    # ストップワード
    stopwords = {
        'エンタメ', 'ニュース', '発表', '出演', '放送', '公開', '映画', 
        'ドラマ', 'テレビ', '番組', '芸能', '俳優', '女優', 'アイドル',
        '速報', '話題', '注目', '最新', '情報', 'について', 'として',
        'による', 'など', 'から', 'まで', 'という', 'ための', 'における',
        '写真', '画像', '動画', 'コメント', 'インタビュー', 'さん', 'くん',
        'ちゃん', '氏', '様', '先生', '監督', '主演', '共演'
    }
    
    for name in names:
        if name not in stopwords and name not in keywords:
            keywords.append(name)
    
    # アルファベット名も抽出（グループ名など）
    alpha_pattern = r'[A-Za-z][A-Za-z0-9]{2,15}'
    alpha_names = re.findall(alpha_pattern, text)
    
    alpha_stopwords = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'http', 'https', 'www', 'html'}
    for name in alpha_names:
        if name.lower() not in alpha_stopwords and name not in keywords:
            keywords.append(name)
    
    # 重複除去して上位5件
    return list(dict.fromkeys(keywords))[:5]


if __name__ == "__main__":
    news = get_latest_news(5)
    for item in news:
        print(f"\n{item['title']}")
        print(f"  URL: {item['url']}")
        print(f"  Keywords: {item['keywords']}")
