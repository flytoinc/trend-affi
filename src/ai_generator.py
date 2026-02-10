"""
AI投稿生成
固定フォーマットでX投稿を生成
"""


def generate_post(trend_data, product):
    """
    トレンドと商品情報からX投稿を生成
    
    Args:
        trend_data: トレンド情報 {name, reason, keywords}
        product: 商品情報 {title, price, affiliate_url}
    
    Returns:
        str: 投稿テキスト
    """
    trend_name = trend_data.get('name', 'トレンド')
    trend_reason = trend_data.get('reason', '話題')
    keywords = trend_data.get('keywords', [])
    
    # 商品名からUS$表記を削除
    product_title = product['title'].replace('US$', '').replace('$', '').strip()
    import re
    product_title = re.sub(r'\s+', ' ', product_title)
    
    # ハッシュタグ生成（キーワードから2個）
    hashtags = []
    for kw in keywords[:2]:
        # ハッシュタグに適さない文字を削除
        clean_kw = re.sub(r'[!?。、\s]', '', kw)
        if clean_kw:
            hashtags.append(f'#{clean_kw}')
    
    hashtags_str = ' '.join(hashtags) if hashtags else f'#{trend_name}'
    
    # 投稿フォーマット
    post_text = f"""「{trend_name}」が話題だね。{trend_reason}があったみたい。そんな{trend_name}の激レア商品はこちら。貴重なものなので、急いで。

あの日の思い出も、メルカリで

{hashtags_str} pr

{product.get('affiliate_url', product['url'])}"""
    
    return post_text


if __name__ == "__main__":
    # テスト
    test_trend = {
        'name': '仲間由紀恵',
        'reason': '震災15年特番に出演',
        'keywords': ['仲間由紀恵', '震災15年']
    }
    test_product = {
        'title': '「美女と男子」DVD 全10巻',
        'price': 15000,
        'url': 'https://jp.mercari.com/item/m12345',
        'affiliate_url': 'https://jp.mercari.com/item/m12345?afid=3578578619'
    }
    
    post = generate_post(test_trend, test_product)
    print(post)
