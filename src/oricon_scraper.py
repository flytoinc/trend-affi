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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_items = []
        
        # 記事リストを取得（複数のセレクタを試す）
        articles = soup.select('article, div.article-list-item, li.news-item, .news-list a')
        
        if not articles:
            articles = soup.select('a[href*="/news/"]')
        
        for article in articles[:limit * 2]:  # 多めに取得してフィルタ
            try:
                # URLとタイトル取得
                if article.name == 'a':
                    link = article
                    title = article.get_text(strip=True)
                else:
                    link = article.select_one('a[href*="/news/"]')
                    title_elem = article.select_one('h2, h3, .title, .headline, p')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not link:
                    continue
                
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = f"https://www.oricon.co.jp{href}"
                
                if not title:
                    title = link.get_text(strip=True)
                
                # バリデーション
                if not title or len(title) < 10 or '/news/' not in href:
                    continue
                
                # キーワード抽出
                keywords = extract_keywords(title)
                
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
                continue
        
        print(f"オリコンニュース: {len(news_items)}件取得")
        return news_items
        
    except Exception as e:
        print(f"オリコンニュース取得エラー: {e}")
        return []


def extract_keywords(text):
    """タレント名・作品名等のキーワードを抽出"""
    keywords = []
    
    # カッコ内のテキスト
    for pattern in [r'「(.+?)」', r'『(.+?)』', r'【(.+?)】']:
        keywords.extend(re.findall(pattern, text))
    
    # 固有名詞らしき語
    names = re.findall(r'[ァ-ヶー々〇〻\u3400-\u9FFF]{2,8}', text)
    
    stopwords = {'エンタメ', 'ニュース', '発表', '出演', '放送', '公開', '映画', 
                 'ドラマ', 'テレビ', '番組', '芸能', '俳優', '女優', 'アイドル'}
    
    for name in names:
        if name not in stopwords and name not in keywords:
            keywords.append(name)
    
    return list(dict.fromkeys(keywords))[:5]


if __name__ == "__main__":
    news = get_latest_news(5)
    for item in news:
        print(f"\n{item['title']}")
        print(f"  Keywords: {item['keywords']}")
