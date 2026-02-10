"""
トレンド理由調査
トレンドがなぜ話題なのかを調査
"""
import re


def research_trend_reason(trend_data):
    """
    トレンドがなぜ話題なのかを調査
    
    Args:
        trend_data: {'name': str, 'traffic': str, 'articles': []}
    
    Returns:
        str: トレンドの理由（簡潔に、30文字以内）
    """
    trend_name = trend_data['name']
    articles = trend_data.get('articles', [])
    
    # 記事タイトルから理由を抽出
    if articles:
        # 最初の記事タイトルから理由を推測
        first_article = articles[0]['title']
        
        # 理由を示すキーワードを抽出
        reason = extract_reason_from_title(first_article, trend_name)
        
        if reason:
            return reason
    
    # 記事がない場合はトラフィック情報から
    traffic = trend_data.get('traffic', '')
    if traffic:
        # "50万回以上の検索" などから理由を推測
        return f"{traffic}の検索"
    
    # デフォルト
    return "話題"


def extract_reason_from_title(title, trend_name):
    """
    記事タイトルから理由を抽出
    
    Args:
        title: 記事タイトル
        trend_name: トレンド名
    
    Returns:
        str: 理由（簡潔に）
    """
    # トレンド名を除去
    title = title.replace(trend_name, '').strip()
    
    # 理由を示すパターン
    patterns = [
        r'(.{2,20}?)(?:が|で|に|を|と)',  # 「〜が」「〜で」など
        r'(.{2,20}?)(?:した|する|発表|公開|開催)',  # 動詞
        r'(.{2,20}?)(?:話題|注目|人気)',  # 話題性
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            reason = match.group(1).strip()
            # 短すぎる or 長すぎる場合はスキップ
            if 2 <= len(reason) <= 30:
                return reason
    
    # パターンマッチしない場合、最初の20文字
    if len(title) > 2:
        return title[:20].strip()
    
    return None


if __name__ == "__main__":
    # テスト
    test_trend = {
        'name': '仲間由紀恵',
        'traffic': '5万回以上の検索',
        'articles': [
            {'title': '仲間由紀恵、震災15年の今を見つめる特番に出演', 'url': 'https://example.com'}
        ]
    }
    
    reason = research_trend_reason(test_trend)
    print(f"理由: {reason}")
