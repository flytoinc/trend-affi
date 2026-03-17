"""
Trend-Affi: 自律型エンタメアフィリエイト・マーケター
情報源: Google Trends / X（交互に使用）
投稿生成: Gemini API（学習インサイト反映）
商品選定: メルカリ（意味的マッチング付き）
シャドウバン回避: ランダム遅延、投稿数削減
"""
import os
import sys
import traceback
import random
import re
import time
from datetime import datetime

from src.google_trends_scraper import get_trending_topics
from src.x_trends_scraper import get_x_trending_topics
from src.trend_researcher import research_trend_reason
from src.mercari_search import find_related_products
from src.ai_generator import generate_post
from src.x_poster import post_to_x, post_to_x_with_image, quote_retweet
from src.sheets_manager import SheetsManager
from src.learning import get_top_posts_insights
from src.x_engagement_finder import find_popular_tweet
from src.metrics_updater import update_pending_metrics


def is_trend_duplicate(trend_name, recent_trends):
    """
    トレンドが既に投稿済みかチェック（完全一致 + 正規化一致）
    
    Args:
        trend_name: チェックするトレンド名
        recent_trends: 過去の投稿済みトレンド名のセット
    
    Returns:
        bool: 重複している場合True
    """
    # 完全一致チェック
    if trend_name in recent_trends:
        return True
    
    # 正規化して一致チェック（スペース除去・小文字化）
    normalized = re.sub(r'\s+', '', trend_name).lower()
    if normalized in recent_trends:
        return True
    
    return False


def main():
    """メイン実行関数"""
    print("=" * 60)
    print(f"Trend-Affi 実行開始: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # 環境変数チェック
    required_vars = [
        'X_API_KEY', 'X_API_SECRET', 
        'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET',
        'GOOGLE_CREDENTIALS_JSON', 'GOOGLE_SHEET_KEY'
    ]
    
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        print(f"Error: Missing environment variables: {missing}")
        sys.exit(1)
    
    # 情報源の決定（環境変数 TREND_SOURCE で切替）
    trend_source = os.environ.get('TREND_SOURCE', 'google_trends')
    print(f"\n情報源: {trend_source}")
    
    # ドライランモード
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("⚠️ ドライランモード: 実際の投稿は行いません")
    
    try:
        # シャドウバン回避: ランダム遅延（0-30分）
        delay_minutes = random.randint(0, 30)
        delay_seconds = delay_minutes * 60
        print(f"\n⏰ シャドウバン回避のため{delay_minutes}分待機...")
        if not dry_run:
            time.sleep(delay_seconds)
        
        # 1. Google Sheets接続
        print("\n[1/8] Google Sheets接続...")
        sheets = SheetsManager(
            os.environ['GOOGLE_CREDENTIALS_JSON'],
            os.environ['GOOGLE_SHEET_KEY']
        )
        
        # 2. エンゲージメント回収（過去投稿のメトリクスを更新）
        print("\n[2/8] エンゲージメント回収...")
        try:
            updated = update_pending_metrics(sheets, hours_after_post=6, max_updates=15)
            print(f"メトリクス更新: {updated}件")
        except Exception as e:
            print(f"メトリクス回収エラー（続行）: {e}")
        
        # 3. 学習インサイト取得
        print("\n[3/8] 学習インサイト取得...")
        learning_insights = get_top_posts_insights(sheets, limit=10)
        print(f"学習インサイト:\n{learning_insights}")
        
        # 3. トレンド取得（情報源に応じて切替）
        print(f"\n[4/8] トレンド取得 ({trend_source})...")
        if trend_source == 'x_trends':
            trends = get_x_trending_topics(limit=10)
        else:
            trends = get_trending_topics(limit=10)
        
        if not trends:
            print("トレンドが取得できませんでした")
            return
        
        print(f"取得トレンド: {len(trends)}件")
        for i, trend in enumerate(trends[:5], 1):
            print(f"  {i}. {trend['name']}")
        
        # 過去投稿済みトレンドを取得（重複防止）
        recent_trends = sheets.get_recent_trends(hours=72)
        print(f"\n過去72時間の投稿済みトレンド: {len(recent_trends)}件")
        
        # 未投稿のトレンドをフィルタリング（1つのトレンドは1投稿のみ）
        new_trends = [
            t for t in trends 
            if not is_trend_duplicate(t['name'], recent_trends)
        ]
        
        if not new_trends:
            print("新規トレンドがありません（全て72時間以内に投稿済み）")
            return
        
        print(f"未投稿トレンド: {len(new_trends)}件")
        
        # 上位1件のトレンドを処理（シャドウバン回避: 1回の実行で1投稿）
        posts_count = 0
        target_count = 1
        
        for trend in new_trends[:5]:  # 最大5件まで試行
            if posts_count >= target_count:
                break
            
            print(f"\n{'='*60}")
            print(f"処理中 ({posts_count + 1}/{target_count}): {trend['name']}")
            print(f"{'='*60}")
            
            # 4. トレンドの理由を調査
            print("\n[5/8] トレンド理由調査...")
            trend_reason = research_trend_reason(trend)
            print(f"理由: {trend_reason}")
            
            # 5. メルカリで関連商品を検索（意味的マッチング付き）
            print("\n[6/8] メルカリ商品検索（意味マッチング付き）...")
            
            news_item = {
                'title': trend['name'],
                'keywords': [trend['name']],
                'url': ''
            }
            
            trend_data = {
                'name': trend['name'],
                'reason': trend_reason,
                'keywords': [trend['name']]
            }
            
            products = find_related_products(news_item, limit=5, trend_data=trend_data)
            
            if not products:
                print(f"  → 関連商品なし、スキップ")
                continue
            
            selected_product = products[0]
            print(f"選択商品: {selected_product['title'][:50]}...")
            print(f"価格: ¥{selected_product['price']:,}")
            if 'relevance_score' in selected_product:
                print(f"関連性スコア: {selected_product['relevance_score']}/10")
            
            # 6. 投稿生成（Gemini API + 学習インサイト）
            print("\n[7/8] 投稿生成 (Gemini API)...")
            
            post_text = generate_post(trend_data, selected_product, learning_insights)
            print(f"生成投稿:\n{post_text}")
            
            # 7. X投稿
            print("\n[8/8] X投稿...")
            
            # 商品画像URL
            image_url = selected_product.get('image_url', '')
            if image_url:
                print(f"商品画像: {image_url[:60]}...")
            
            if dry_run:
                print("⚠️ ドライラン: 投稿スキップ")
                result = {'success': True, 'tweet_id': 'DRY_RUN'}
            else:
                result = post_to_x_with_image(post_text, image_url)
            
            if result['success']:
                print(f"投稿成功! Tweet ID: {result['tweet_id']}")
                
                # スプレッドシートに記録
                trend_record = {
                    'trend_name': trend['name'],
                    'trend_reason': trend_reason,
                    'title': trend['name'],
                    'url': '',
                    'keywords': [trend['name']],
                    'source': trend_source
                }
                
                sheets.log_news_items([trend_record])
                
                sheets.record_post(
                    news_url='',
                    news_title=trend['name'],
                    product_title=selected_product['title'],
                    product_url=selected_product.get('affiliate_url', selected_product['url']),
                    product_price=selected_product['price'],
                    post_text=post_text,
                    tweet_id=result['tweet_id']
                )
                print("スプレッドシートに記録完了")
                
                # === 引用リツイートステップ ===
                _do_quote_retweet(trend, sheets, dry_run)
                
                posts_count += 1
            else:
                print(f"投稿失敗: {result['error']}")
                continue
        
        print(f"\n{'='*60}")
        print(f"投稿完了: {posts_count}件 (情報源: {trend_source})")
        print(f"Trend-Affi 実行完了: {datetime.now().isoformat()}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nエラー発生: {e}")
        traceback.print_exc()
        sys.exit(1)


def _do_quote_retweet(trend, sheets, dry_run=False):
    """
    トレンドワードの人気投稿を引用リツイートする
    1トレンドにつき1回まで
    """
    trend_name = trend['name']
    
    # 引用RT済みチェック
    quoted_trends = sheets.get_recent_quote_retweet_trends(hours=72)
    if is_trend_duplicate(trend_name, quoted_trends):
        print(f"\n引用RTスキップ: 「{trend_name}」は既に引用RT済み")
        return
    
    print(f"\n--- 引用リツイートステップ: {trend_name} ---")
    
    # 人気投稿を検索
    popular_tweet = find_popular_tweet(trend_name, min_likes=50)
    
    if not popular_tweet:
        print(f"  → 引用RT対象の投稿が見つかりませんでした")
        return
    
    # Geminiで引用コメントを生成
    quote_comment = _generate_quote_comment(trend_name, popular_tweet)
    
    if dry_run:
        print(f"  ⚠️ ドライラン: 引用RTスキップ")
        print(f"  引用コメント: {quote_comment}")
        return
    
    # 少し間を置く（シャドウバン回避）
    delay = random.randint(30, 120)
    print(f"  → {delay}秒待機後に引用RT...")
    time.sleep(delay)
    
    # 引用リツイート実行
    result = quote_retweet(quote_comment, popular_tweet['tweet_id'])
    
    if result['success']:
        print(f"  引用RT成功! Tweet ID: {result['tweet_id']}")
        
        # スプレッドシートに記録
        sheets.record_quote_retweet(
            trend_name=trend_name,
            original_tweet_id=popular_tweet['tweet_id'],
            original_author=popular_tweet.get('author', ''),
            original_text=popular_tweet.get('text', ''),
            quote_text=quote_comment,
            quote_tweet_id=result['tweet_id']
        )
    else:
        print(f"  引用RT失敗: {result['error']}")


def _generate_quote_comment(trend_name, popular_tweet):
    """
    Geminiで引用リツイートのコメントを生成
    """
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return f"「{trend_name}」が話題だね👀"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""以下のXの投稿に対する引用リツイートのコメントを生成してください。

【トレンド】{trend_name}
【元投稿】@{popular_tweet.get('author', '')}: {popular_tweet.get('text', '')[:100]}

【ルール】
1. 30文字以内の短いコメント
2. 元投稿に共感・反応する自然なトーン
3. カジュアルな口調
4. 絵文字0～1個
5. コメントのみを出力（他の説明不要）

コメント:"""
        
        response = model.generate_content(prompt)
        comment = response.text.strip().strip('"\'「」')
        
        # 40文字以上ならトリム
        if len(comment) > 40:
            comment = comment[:38] + '..'
        
        return comment
        
    except Exception as e:
        print(f"  引用コメント生成エラー: {e}")
        return f"「{trend_name}」が話題だね👀"


if __name__ == "__main__":
    main()
