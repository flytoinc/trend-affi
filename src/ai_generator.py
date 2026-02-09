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
    
    prompt = f"""あなたはX（Twitter）で話題のエンタメ情報を発信する人気アカウントです。
以下のニュースと商品情報から、反応が良くなる投稿を作成してください。

【ニュース】
タイトル: {news['title']}

【商品】
商品名: {product['title']}
価格: ¥{product['price']}

【過去の高反応投稿の傾向】
{insights if insights else "特になし"}

【投稿ルール】
1. 読んだ人が思わず反応したくなる内容
2. ニュースの話題と商品を自然につなげる
3. 文字数: 100〜130文字（URLは別で追加されます）
4. 一人称で、感情や本音を込める
5. 読点（、）でつなげて自然な文に
6. 絵文字は1〜2個まで
7. ハッシュタグは最後に1〜2個

【禁止】
- 宣伝臭い表現
- 命令口調
- 「おすすめ」「お得」などの直接的な売り込み

出力: 投稿文のみ"""

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
    templates = [
        "話題の{keyword}関連、これ見つけた👀\n\n{product_title}\n¥{price}\n\n{url}",
        "{keyword}のニュース見て、つい関連グッズ探しちゃった✨\n\n{product_title}\n\n{url}",
        "今話題の{keyword}！ファンなら気になるかも？\n\n{product_title}\n¥{price}\n\n{url}",
    ]
    
    import random
    template = random.choice(templates)
    
    keyword = news['keywords'][0] if news.get('keywords') else "エンタメ"
    
    return template.format(
        keyword=keyword,
        product_title=product['title'][:30],
        price=product['price'],
        url=product.get('affiliate_url', product['url'])
    )


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
