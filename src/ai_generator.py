"""
AI投稿生成
Gemini APIを使用してX投稿を生成
個性的なキャラクター設定と多様な文体で自然な投稿を実現
API quota対策: リトライ + 充実したフォールバック
"""
import os
import random
import re
import time
import google.generativeai as genai


# 投稿スタイルのバリエーション
POST_STYLES = [
    "驚き・発見型（「え、これマジ？」系の反応）",
    "共感・納得型（「わかるわ〜」系の共感）",
    "豆知識型（「実はこれ〜」系のうんちく）",
    "お見立て型（「これ見て！」系の商品紹介）",
    "ニュース速報型（「〜だって！」系の速報感）",
    "独り言型（「〜気になるな」系のつぶやき）",
]


def generate_post(trend_data, product, learning_insights=""):
    """
    Gemini APIでトレンドと商品情報からX投稿を生成
    
    Args:
        trend_data: トレンド情報 {name, reason, keywords}
        product: 商品情報 {title, price, affiliate_url}
        learning_insights: 学習システムからのインサイト
    
    Returns:
        str: 投稿テキスト
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not set, falling back to template")
        return _generate_fallback(trend_data, product)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    trend_name = trend_data.get('name', 'トレンド')
    trend_reason = trend_data.get('reason', '話題')
    
    # 商品名のクリーンアップ
    product_title = product['title'].replace('US$', '').replace('$', '').strip()
    product_title = re.sub(r'\s+', ' ', product_title)
    product_price = product.get('price', 0)
    
    # ランダムにスタイルを選択
    selected_style = random.choice(POST_STYLES)
    
    # 学習インサイト部分
    learning_section = ""
    if learning_insights and learning_insights != "データなし" and learning_insights != "分析データなし":
        learning_section = f"""
【過去の高反応投稿から学んだパターン】
{learning_insights}
上記のパターンを参考にしつつ、毎回異なる表現を使ってください。
"""
    
    prompt = f"""あなたは「トレンドの裏にある面白い商品」を発掘するのが得意なXユーザーです。
フォロワーにとって「このアカウント面白い」「お宝情報がある」と思わせる投稿を作ってください。

【あなたのキャラクター】
- 好奇心旺盛で、トレンドの背景を掘り下げるのが好き
- メルカリで面白い商品を見つけるのが趣味
- 自然体でカジュアル、押し売り感ゼロ
- たまに独り言のような投稿もする

【トレンド情報】
- トレンド名: {trend_name}
- なぜ話題か: {trend_reason}

【見つけた商品】
- 商品名: {product_title}
- 価格: ¥{product_price:,}

【今回の投稿スタイル】
{selected_style}

{learning_section}

【投稿ルール】
1. 全体で120文字以内（URL・ハッシュタグ除く）
2. トレンドの話題に軽く触れつつ、商品を自然に紹介
3. 「pr」は必ず含める（広告表記として）
4. 口語調でカジュアルに
5. 毎回違う文体・構成にする（テンプレ感を出さない）
6. 自然なトーンで煽らない
7. ハッシュタグは0〜1個
8. 絵文字は0〜2個
9. 商品URLは含めない（自動付与される）
10. 投稿文のみを出力（それ以外の説明は不要）
11. 「話題だね」「トレンド入り」のような定番フレーズを避ける

投稿文:"""

    # リトライロジック（429 quota exceeded 対策）
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            post_text = response.text.strip()
            
            # 不要な引用符やマーカーを除去
            post_text = post_text.strip('"\'"「」')
            post_text = re.sub(r'^投稿文[:：]\s*', '', post_text)
            
            # prが含まれていない場合は追加
            if 'pr' not in post_text.lower():
                post_text += "\n\npr"
            
            # アフィリエイトURL追加
            affiliate_url = product.get('affiliate_url', product.get('url', ''))
            post_text = f"{post_text}\n\n{affiliate_url}"
            
            print(f"Gemini投稿生成完了（{len(post_text)}文字, スタイル: {selected_style[:10]}）")
            return post_text
            
        except Exception as e:
            error_msg = str(e)
            if '429' in error_msg or 'quota' in error_msg.lower():
                wait = 10 * (attempt + 1)
                print(f"Gemini API クォータ制限 (試行 {attempt+1}/{max_retries}): {wait}秒待機...")
                time.sleep(wait)
                continue
            print(f"Gemini API エラー: {e}")
            break
    
    print("→ フォールバックテンプレートを使用")
    return _generate_fallback(trend_data, product)


def _generate_fallback(trend_data, product):
    """
    Gemini API が使えない場合のフォールバック
    多彩なテンプレートでbot感を回避
    """
    trend_name = trend_data.get('name', 'トレンド')
    trend_reason = trend_data.get('reason', '話題')
    
    product_title = product['title'].replace('US$', '').replace('$', '').strip()
    product_title = re.sub(r'\s+', ' ', product_title)
    # 商品名を短くする
    short_product = product_title[:30] + ('...' if len(product_title) > 30 else '')
    price = product.get('price', 0)
    
    # 投稿パターン群（毎回違う文体になるよう大量に用意）
    templates = [
        # 驚き系
        f"え、「{trend_name}」の関連グッズがメルカリにあった。{short_product}、¥{price:,}は気になる",
        f"「{trend_name}」調べてたらメルカリで面白いの見つけた\n\n{short_product}（¥{price:,}）",
        f"ちょ、{trend_name}関連でこれ見つけちゃった👀\n{short_product}",
        # 独り言系
        f"メルカリ見てたら{trend_name}関連のやつ出てきた。{short_product}...買おうかな",
        f"{trend_name}、気になったからメルカリ検索したら良さげなの発見。\n{short_product}（¥{price:,}）",
        f"{trend_name}の便乗じゃないけど、こういうの好きなんだよね\n{short_product}",
        # ニュース系
        f"今日の話題「{trend_name}」\n{trend_reason[:40]}\n\n関連してこれ↓\n{short_product}",
        f"{trend_name}が盛り上がってる中、メルカリで掘り出し物を発見\n\n{short_product} ¥{price:,}",
        # 紹介系
        f"「{trend_name}」好きな人、これ知ってる？\n\n{short_product}がメルカリに出てた（¥{price:,}）",
        f"{trend_name}ファンに教えたい。メルカリで見つけた\n{short_product}",
        f"今{trend_name}で検索すると面白い。メルカリにもこんなのあった\n{short_product} ¥{price:,}",
        # カジュアル系
        f"あ、これいいかも。{trend_name}つながりで\n{short_product}（¥{price:,}）",
        f"{trend_name}×メルカリで検索した結果 → {short_product} が出てきた。意外と安い",
        f"ふと{trend_name}で検索してみたら{short_product}に辿り着いた。レア？",
        f"今日のメルカリ散歩（{trend_name}編）\n\n見つけたもの: {short_product} ¥{price:,}",
    ]
    
    template = random.choice(templates)
    
    post_text = f"""{template}

pr

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
    
    print("=== テスト投稿生成 ===")
    post = generate_post(test_trend, test_product, "・絵文字を使った投稿が多い\n・ハッシュタグありの投稿が多い")
    print(post)
