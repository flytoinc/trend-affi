"""
AI投稿生成
Gemini APIを使用してXに最適化された投稿を生成
"""
import os
import google.generativeai as genai


def generate_post(news, product, insights=""):
    """
    ニュースと商品情報からX投稿を生成
    
    Args:
        news: ニュース情報 {title, url, keywords}
        product: 商品情報 {title, price, affiliate_url}
        insights: 過去の高反応投稿から得た知見
    
    Returns:
        str: 投稿テキスト
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not set, using template")
        return _template_post(news, product)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config=genai.GenerationConfig(
            temperature=0.8,
            top_p=0.9,
        )
    )
    
    prompt = f"""あなたはメルカリ公式のエンタメトレンド情報を発信するアカウントです。
以下のニュースと商品情報から、トレンドに注目している人に見つけてもらえる投稿を作成してください。

【ニュース】
タイトル: {news['title']}
キーワード: {', '.join(news.get('keywords', [])[:3])}

【商品】
商品名: {product['title']}
価格: ¥{product['price']:,}

【過去の高反応投稿の傾向】
{insights if insights else "特になし"}

【投稿フォーマット】
1行目: ヘッダーメッセージ（公式ぽい × 一人称、30-50文字）
2行目: 空行
3行目: 商品名（そのまま）
4行目: 価格（¥表記のみ、US$不要）
5行目: 空行
6行目: 「あの日の思い出も、メルカリで」（固定）
7行目: 空行
8行目: ハッシュタグ（トレンドに関連する2-3個）

【ヘッダーメッセージのルール】
- トレンドに注目している人の興味を引く
- 公式感がありつつ親しみやすい一人称
- 絵文字は1個まで
- 「おすすめ」「お得」などの直接的な売り込みは禁止

【ハッシュタグのルール】
- ニュースのキーワードから2-3個選ぶ
- トレンド検索で見つけてもらいやすいもの
- 例: #仲間由紀恵 #震災15年 #美女と男子

【禁止事項】
- US$表記
- 宣伝臭い表現
- 命令口調

出力: 投稿文のみ（URLは別で追加されます）"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # 投稿に商品リンクを追加
        if product.get('affiliate_url'):
            text = f"{text}\n\n{product['affiliate_url']}"
        
        # 文字数チェック（URLなしで130文字以内）
        main_text = text.split('\n\n')[0]
        if len(main_text) > 140:
            # 長すぎる場合は再生成せず単にカット
            main_text = main_text[:135] + "..."
            text = f"{main_text}\n\n{product.get('affiliate_url', '')}"
        
        return text
        
    except Exception as e:
        print(f"AI生成エラー: {e}")
        return _template_post(news, product)


def _template_post(news, product):
    """フォールバック用テンプレート投稿"""
    keyword = news['keywords'][0] if news.get('keywords') else "エンタメ"
    keywords = news.get('keywords', ['エンタメ'])[:3]
    
    # ハッシュタグ生成
    hashtags = ' '.join([f'#{kw}' for kw in keywords[:2]])
    
    # 商品名からUS$表記を削除
    product_title = product['title'].replace('US$', '').replace('$', '').strip()
    # 連続する空白を1つに
    import re
    product_title = re.sub(r'\s+', ' ', product_title)
    
    templates = [
        f"話題の{keyword}、メルカリで見つけました✨\n\n{product_title}\n¥{product['price']:,}\n\nあの日の思い出も、メルカリで\n\n{hashtags}",
        f"{keyword}のニュース見て気になって探してみた\n\n{product_title}\n¥{product['price']:,}\n\nあの日の思い出も、メルカリで\n\n{hashtags}",
        f"今話題の{keyword}関連グッズ\n\n{product_title}\n¥{product['price']:,}\n\nあの日の思い出も、メルカリで\n\n{hashtags}",
    ]
    
    import random
    post_text = random.choice(templates)
    
    # URLを追加
    if product.get('affiliate_url'):
        post_text = f"{post_text}\n\n{product['affiliate_url']}"
    
    return post_text


if __name__ == "__main__":
    # テスト
    test_news = {
        'title': '人気アイドル「乃木坂46」新曲MVが1000万再生突破',
        'keywords': ['乃木坂46', '新曲']
    }
    test_product = {
        'title': '乃木坂46 生写真セット',
        'price': 2980,
        'affiliate_url': 'https://example.com/item/xxx'
    }
    
    post = generate_post(test_news, test_product, "絵文字を使うと反応が良い")
    print(post)
