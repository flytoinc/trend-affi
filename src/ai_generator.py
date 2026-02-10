"""
AI投稿生成
固定フォーマットでX投稿を生成（シャドウバン回避対策付き）
"""
import random
import re


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
    
    # トレンド理由を50文字以上に拡張（全体で140文字に収まる範囲）
    fixed_text = f"「{trend_name}」が話題だね。......なんだって。そんな{trend_name}の激レア商品はこちら。"
    fixed_length = len(fixed_text)
    
    # トレンド理由の最大文字数（140文字 - 固定部分）
    max_reason_length = 140 - fixed_length
    
    # トレンド理由を50文字以上、最大文字数以内に調整
    if len(trend_reason) < 50:
        extended_reason = trend_reason
    elif len(trend_reason) > max_reason_length:
        extended_reason = trend_reason[:max_reason_length]
    else:
        extended_reason = trend_reason
    
    # 商品名からUS$表記を削除
    product_title = product['title'].replace('US$', '').replace('$', '').strip()
    product_title = re.sub(r'\s+', ' ', product_title)
    
    # シャドウバン回避: 締めフレーズのバリエーション（20種類）
    closing_phrases = [
        "貴重なものなので、急いで。",
        "在庫わずかだから、お早めに。",
        "見つけたらラッキーかも。",
        "気になる人はチェックしてみて。",
        "レアアイテムだから、見逃さないで。",
        "今のうちにゲットしておこう。",
        "こういうの探してた人いるかな。",
        "数量限定っぽいから、気になる人は早めに。",
        "掘り出し物見つけちゃった。",
        "これは見逃せないかも。",
        "タイミング良ければ手に入るかも。",
        "興味ある人は要チェック。",
        "こんなの出てるんだね。",
        "ファンなら見逃せないやつ。",
        "珍しいから、気になる人はぜひ。",
        "売り切れる前にどうぞ。",
        "レア度高めだから、お見逃しなく。",
        "こういうの好きな人いそう。",
        "今がチャンスかもね。",
        "気になったら早めにチェック。",
    ]
    
    # シャドウバン回避: テンプレートのバリエーション（3種類）
    templates = [
        # オリジナル
        "「{name}」が話題だね。{reason}......なんだって。そんな{name}の激レア商品はこちら。{closing}",
        # バリエーション1
        "「{name}」がトレンド入り。{reason}......らしい。関連商品をメルカリで見つけたよ。{closing}",
        # バリエーション2
        "話題の「{name}」。{reason}......みたい。メルカリにレアなアイテムがあったから紹介するね。{closing}",
    ]
    
    template = random.choice(templates)
    closing = random.choice(closing_phrases)
    main_text = template.format(name=trend_name, reason=extended_reason, closing=closing)
    
    # シャドウバン回避: タグラインを50%の確率で省略
    tagline = ""
    if random.random() < 0.5:
        taglines = [
            "あの日の思い出も、メルカリで",
            "思い出の品も、メルカリで見つかるかも",
            "懐かしいアイテム、メルカリにあるよ",
        ]
        tagline = f"\n\n{random.choice(taglines)}"
    
    # シャドウバン回避: ハッシュタグを50%の確率で省略、ただし"pr"は必須
    hashtags_str = ""
    if random.random() < 0.5:
        # ハッシュタグを1つだけ生成 + pr
        if keywords:
            clean_kw = re.sub(r'[!?。、\s]', '', keywords[0])
            if clean_kw:
                hashtags_str = f"\n\n#{clean_kw} pr"
        else:
            hashtags_str = f"\n\n#{trend_name} pr"
    else:
        # ハッシュタグなしでもprは必須
        hashtags_str = "\n\npr"
    
    # 投稿フォーマット
    post_text = f"""{main_text}{tagline}{hashtags_str}

{product.get('affiliate_url', product['url'])}"""
    
    return post_text


if __name__ == "__main__":
    # テスト
    test_trend = {
        'name': '仲間由紀恵',
        'reason': '震災15年特番に出演し、当時の思いを語る',
        'keywords': ['仲間由紀恵', '震災15年']
    }
    test_product = {
        'title': '「美女と男子」DVD 全10巻',
        'price': 15000,
        'url': 'https://jp.mercari.com/item/m12345',
        'affiliate_url': 'https://jp.mercari.com/item/m12345?afid=3578578619'
    }
    
    print("=== テスト投稿生成（5回） ===")
    for i in range(5):
        post = generate_post(test_trend, test_product)
        print(f"\n--- 投稿{i+1} ---")
        print(post)
