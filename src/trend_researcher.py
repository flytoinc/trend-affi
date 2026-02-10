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
        str: トレンドの理由（50文字以上推奨）
    """
    trend_name = trend_data['name']
    articles = trend_data.get('articles', [])
    
    # 記事タイトルから理由を抽出
    if articles:
        # 最初の記事タイトルをそのまま使用（トレンド名を除去）
        first_article = articles[0]['title']
        
        # トレンド名を除去
        reason = first_article.replace(trend_name, '').strip()
        
        # 前後の句読点を削除
        reason = reason.lstrip('、。：:・').rstrip('、。')
        
        # 50文字以上になるように調整
        if len(reason) >= 50:
            # 適切な長さの場合はそのまま返す
            return reason
        elif len(reason) > 0:
            # 短い場合でも記事タイトルがあればそれを使う
            return reason
    
    # 記事がない場合はトラフィック情報から
    traffic = trend_data.get('traffic', '')
    if traffic:
        return f"{traffic}の検索が急上昇しているみたい"
    
    # デフォルト（50文字以上を目指す）
    return f"SNSやニュースで大きな話題になっている"


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
