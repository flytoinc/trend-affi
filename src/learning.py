"""
学習システム
過去の投稿データから高反応パターンを分析
"""


def get_top_posts_insights(sheets_manager, limit=10):
    """
    過去の高反応投稿から学習インサイトを抽出
    
    Args:
        sheets_manager: SheetsManagerインスタンス
        limit: 分析する投稿数
    
    Returns:
        str: プロンプトに含める学習インサイト
    """
    try:
        # 高エンゲージメント投稿を取得
        top_posts = sheets_manager.get_top_engagement_posts(limit)
        
        if not top_posts:
            return "データなし"
        
        # パターン分析
        insights = analyze_patterns(top_posts)
        
        return insights
        
    except Exception as e:
        print(f"学習データ取得エラー: {e}")
        return "分析データなし"


def analyze_patterns(posts):
    """
    高反応投稿のパターンを分析
    
    Args:
        posts: 投稿データのリスト
    
    Returns:
        str: 分析結果のサマリー
    """
    if not posts:
        return "データなし"
    
    patterns = []
    
    # 文字数分析
    char_counts = [len(p.get('post_text', '')) for p in posts if p.get('post_text')]
    if char_counts:
        avg_chars = sum(char_counts) / len(char_counts)
        patterns.append(f"平均文字数: {int(avg_chars)}文字")
    
    # 絵文字使用率
    emoji_count = sum(1 for p in posts if has_emoji(p.get('post_text', '')))
    if emoji_count > len(posts) * 0.5:
        patterns.append("絵文字を使った投稿が多い")
    
    # 疑問形の使用
    question_count = sum(1 for p in posts if '?' in p.get('post_text', '') or '？' in p.get('post_text', ''))
    if question_count > len(posts) * 0.3:
        patterns.append("疑問形を含む投稿が反応が良い")
    
    # 時間帯分析（簡易）
    # 実際にはposted_atから時間帯を分析
    
    # ハッシュタグ分析
    hashtag_posts = sum(1 for p in posts if '#' in p.get('post_text', ''))
    if hashtag_posts > len(posts) * 0.7:
        patterns.append("ハッシュタグありの投稿が多い")
    
    # 価格帯分析
    prices = [p.get('product_price', 0) for p in posts if p.get('product_price')]
    if prices:
        avg_price = sum(prices) / len(prices)
        if avg_price > 5000:
            patterns.append("高単価商品の方が反応が良い傾向")
        elif avg_price < 2000:
            patterns.append("手頃な価格帯が好まれる傾向")
    
    if not patterns:
        patterns.append("特定パターンなし - 様々なスタイルを試してください")
    
    return "・" + "\n・".join(patterns)


def has_emoji(text):
    """テキストに絵文字が含まれるかチェック"""
    import re
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return bool(emoji_pattern.search(text))


def calculate_engagement_rate(impressions, likes, retweets, replies):
    """エンゲージメント率を計算"""
    if not impressions or impressions == 0:
        return 0.0
    
    engagements = (likes or 0) + (retweets or 0) * 2 + (replies or 0) * 3
    return round(engagements / impressions * 100, 2)


if __name__ == "__main__":
    # テスト
    test_posts = [
        {'post_text': '話題の商品見つけた！✨ これ欲しい', 'product_price': 3000},
        {'post_text': 'これって買い？迷うな〜 #エンタメ', 'product_price': 4500},
    ]
    
    insights = analyze_patterns(test_posts)
    print(insights)
