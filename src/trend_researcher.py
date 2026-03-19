"""
トレンド理由調査
Gemini APIを使用してトレンドの背景・理由をリアルタイムに調査
"""
import os
import re
import random
import time


def research_trend_reason(trend_data):
    """
    トレンドがなぜ話題なのかをGemini APIで調査
    
    Args:
        trend_data: {'name': str, 'traffic': str, 'articles': []}
    
    Returns:
        str: トレンドの理由（具体的な内容）
    """
    trend_name = trend_data['name']
    articles = trend_data.get('articles', [])
    
    # 記事タイトルがある場合はそこから理由を抽出
    if articles:
        first_article = articles[0]['title']
        reason = first_article.replace(trend_name, '').strip()
        reason = clean_article_title(reason)
        if len(reason) >= 15:
            return reason
    
    # Gemini APIで調査
    reason = _research_with_gemini(trend_name)
    if reason:
        return reason
    
    # Gemini APIが使えない場合のフォールバック
    traffic = trend_data.get('traffic', '')
    if traffic:
        return f"{traffic}の検索が急上昇しているみたい"
    
    return _get_fallback_reason()


def _research_with_gemini(trend_name):
    """
    Gemini APIでトレンドの理由をリアルタイム調査
    Google Searchツール（grounding）を使用
    """
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return None
        
        genai.configure(api_key=api_key)
        
        # Google Search grounding を使用してリアルタイム情報を取得
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            tools='google_search_retrieval'
        )
        
        prompt = f"""「{trend_name}」が今X(Twitter)やGoogleでトレンド入りしています。
なぜ話題になっているのか、具体的な理由を1〜2文で簡潔に教えてください。

【ルール】
1. 50〜100文字程度で
2. 具体的な出来事・ニュースに基づくこと
3. 「〜とのこと」「〜らしい」のような伝聞調で
4. 理由のみを出力（余計な前置き不要）

理由:"""
        
        # リトライロジック（429 対策）
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                reason = response.text.strip()
                
                # 不要なプレフィックスを除去
                reason = re.sub(r'^理由[:：]\s*', '', reason)
                reason = reason.strip('"\'「」')
                
                # 長すぎる場合はトリム
                if len(reason) > 150:
                    cut_pos = reason[:150].rfind('。')
                    if cut_pos > 50:
                        reason = reason[:cut_pos + 1]
                    else:
                        reason = reason[:148] + '…'
                
                if len(reason) >= 10:
                    print(f"  Gemini調査結果: {reason}")
                    return reason
                
                return None
                
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'quota' in error_msg.lower():
                    wait = 10 * (attempt + 1)
                    print(f"  Gemini クォータ制限 (試行 {attempt+1}/3): {wait}秒待機...")
                    time.sleep(wait)
                    continue
                print(f"  Geminiトレンド調査エラー: {e}")
                break
        
        # リトライ全失敗 or 非429エラー
        return _research_with_gemini_fallback(trend_name)


def _research_with_gemini_fallback(trend_name):
    """
    Google Search grounding が使えない場合のフォールバック
    通常のGeminiモデルでトレンド理由を推定
    """
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""「{trend_name}」がトレンド入りしている理由を推測してください。
この人物・キーワードについての一般的な知識から、今話題になりうる理由を1〜2文で述べてください。
50〜100文字程度で、「〜とのこと」「〜らしい」のような伝聞調で。
理由のみを出力してください。

理由:"""
        
        # リトライロジック（429 対策）
        for attempt in range(2):
            try:
                response = model.generate_content(prompt)
                reason = response.text.strip()
                reason = re.sub(r'^理由[:：]\s*', '', reason)
                reason = reason.strip('"\'「」')
                
                if len(reason) > 150:
                    cut_pos = reason[:150].rfind('。')
                    if cut_pos > 50:
                        reason = reason[:cut_pos + 1]
                    else:
                        reason = reason[:148] + '…'
                
                if len(reason) >= 10:
                    return reason
                
                return None
                
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'quota' in error_msg.lower():
                    wait = 15 * (attempt + 1)
                    print(f"  Gemini フォールバッククォータ制限 ({attempt+1}/2): {wait}秒待機...")
                    time.sleep(wait)
                    continue
                print(f"  Geminiフォールバック調査エラー: {e}")
                break
        
        return None


def _get_fallback_reason():
    """Gemini APIが使えない場合のフォールバック理由"""
    default_reasons = [
        "SNSやニュースで大きな話題になっている",
        "各メディアで取り上げられて注目を集めている",
        "ネットで急速に拡散されて話題沸騰中",
        "多くの人が検索していて注目度が高い",
        "今まさに旬な話題として盛り上がっている",
        "ソーシャルメディアを中心に大きな反響",
        "今日のトレンドとして多くの人が注目",
        "ネット上で大きな話題を呼んでいる",
        "SNSでバズっていて見逃せない",
        "各メディアが競って報道している話題",
    ]
    return random.choice(default_reasons)


def clean_article_title(title):
    """
    記事タイトルから不要なメタ情報を削除
    """
    title = title.replace('\n', ' ')
    title = re.sub(r'[（(][^）)]*[）)]', '', title)
    title = re.sub(r'\d+\s*[分時日]前\s*[●・]', '', title)
    title = re.sub(r'昨日\s*[●・]', '', title)
    title = re.sub(r'Yahoo!ニュース', '', title)
    title = re.sub(r'[A-Za-z\s]+TIMES', '', title)
    title = re.sub(r'スポニチアネックス', '', title)
    title = re.sub(r'日本テレビ', '', title)
    title = re.sub(r'RBC琉球放送', '', title)
    title = re.sub(r'リアルサウンド', '', title)
    title = re.sub(r'\s+', ' ', title)
    title = title.strip('、。：:・ \t')
    return title


if __name__ == "__main__":
    # テスト
    test_trend = {
        'name': '仲間由紀恵',
        'traffic': '5万回以上の検索',
        'articles': []
    }
    
    reason = research_trend_reason(test_trend)
    print(f"理由: {reason}")
