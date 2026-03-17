"""
エンゲージメント自動回収
投稿後24時間以上経過した投稿のインプレッション・いいね・RT・リプライを
X APIで取得し、スプレッドシートに反映する
"""
import os
import tweepy
from datetime import datetime, timedelta


def update_pending_metrics(sheets_manager, hours_after_post=24, max_updates=20):
    """
    エンゲージメントが未回収の投稿を取得し、メトリクスを更新する
    
    Args:
        sheets_manager: SheetsManagerインスタンス
        hours_after_post: 投稿後何時間以上経過した投稿を対象にするか
        max_updates: 1回の実行で更新する最大件数
    
    Returns:
        int: 更新した件数
    """
    # X API認証
    api_key = os.environ.get('X_API_KEY')
    api_secret = os.environ.get('X_API_SECRET')
    access_token = os.environ.get('X_ACCESS_TOKEN')
    access_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')
    
    if not all([api_key, api_secret, access_token, access_secret]):
        print("X API認証情報が不足しています")
        return 0
    
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )
    
    # 未回収の投稿を取得
    pending_posts = sheets_manager.get_pending_metrics_posts(
        hours_after_post=hours_after_post
    )
    
    if not pending_posts:
        print("メトリクス未回収の投稿はありません")
        return 0
    
    print(f"メトリクス未回収: {len(pending_posts)}件（最大{max_updates}件更新）")
    
    updated_count = 0
    
    for post in pending_posts[:max_updates]:
        tweet_id = post.get('tweet_id', '')
        
        if not tweet_id or tweet_id == 'DRY_RUN':
            continue
        
        try:
            # X APIでメトリクスを取得
            response = client.get_tweet(
                tweet_id,
                tweet_fields=['public_metrics']
            )
            
            if response.data and response.data.public_metrics:
                metrics = {
                    'impressions': response.data.public_metrics.get('impression_count', 0),
                    'likes': response.data.public_metrics.get('like_count', 0),
                    'retweets': response.data.public_metrics.get('retweet_count', 0),
                    'replies': response.data.public_metrics.get('reply_count', 0)
                }
                
                sheets_manager.update_engagement_metrics(tweet_id, metrics)
                updated_count += 1
                
                print(f"  ✓ {tweet_id}: "
                      f"{metrics['impressions']}imp, "
                      f"{metrics['likes']}♡, "
                      f"{metrics['retweets']}RT, "
                      f"{metrics['replies']}💬")
            else:
                print(f"  ✗ {tweet_id}: データ取得不可（削除済み？）")
                # 削除済み投稿はメトリクスを0で記録
                sheets_manager.update_engagement_metrics(tweet_id, {
                    'impressions': 0, 'likes': 0, 'retweets': 0, 'replies': 0
                })
                updated_count += 1
                
        except tweepy.TooManyRequests:
            print(f"  ⚠️ レート制限に到達。ここまでの更新: {updated_count}件")
            break
        except tweepy.NotFound:
            print(f"  ✗ {tweet_id}: ツイートが見つかりません")
            sheets_manager.update_engagement_metrics(tweet_id, {
                'impressions': 0, 'likes': 0, 'retweets': 0, 'replies': 0
            })
            updated_count += 1
        except Exception as e:
            print(f"  ✗ {tweet_id}: エラー - {e}")
            continue
    
    print(f"\nメトリクス更新完了: {updated_count}/{len(pending_posts)}件")
    return updated_count


if __name__ == "__main__":
    from sheets_manager import SheetsManager
    
    creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    key = os.environ.get('GOOGLE_SHEET_KEY')
    
    if creds and key:
        sheets = SheetsManager(creds, key)
        update_pending_metrics(sheets)
    else:
        print("環境変数が設定されていません")
