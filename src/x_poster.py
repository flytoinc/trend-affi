"""
X（Twitter）投稿機能
tweepyを使用してX APIで投稿
403エラー対策: リトライロジック、詳細エラーログ、重複検出
"""
import os
import time
import tweepy


def post_to_x(text, max_retries=3):
    """
    Xに投稿する（リトライロジック付き）
    
    Args:
        text: 投稿テキスト
        max_retries: 最大リトライ回数
    
    Returns:
        dict: {success: bool, tweet_id: str, error: str}
    """
    try:
        # 認証情報取得
        api_key = os.environ.get('X_API_KEY')
        api_secret = os.environ.get('X_API_SECRET')
        access_token = os.environ.get('X_ACCESS_TOKEN')
        access_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')
        
        if not all([api_key, api_secret, access_token, access_secret]):
            return {
                'success': False,
                'tweet_id': None,
                'error': 'Missing X API credentials'
            }
        
        # Twitter API v2 Client
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # リトライロジック
        for attempt in range(max_retries):
            try:
                # 投稿
                response = client.create_tweet(text=text)
                
                tweet_id = response.data['id']
                
                print(f"X投稿成功: ID={tweet_id}")
                
                return {
                    'success': True,
                    'tweet_id': tweet_id,
                    'error': None
                }
                
            except tweepy.TweepyException as e:
                error_msg = str(e)
                print(f"X投稿エラー (試行 {attempt + 1}/{max_retries}): {error_msg}")
                
                # エラーの詳細情報を出力
                if hasattr(e, 'response'):
                    print(f"  レスポンスステータス: {e.response.status_code}")
                    print(f"  レスポンス内容: {e.response.text}")
                
                # 403エラーの場合の詳細分析
                if '403' in error_msg or (hasattr(e, 'response') and e.response.status_code == 403):
                    print("  → 403 Forbidden エラー検出")
                    print("  → 考えられる原因:")
                    print("     1. アプリ権限不足（Read and Write権限が必要）")
                    print("     2. 重複投稿検出（同じ内容を短時間に投稿）")
                    print("     3. レート制限超過")
                    print("     4. アカウント制限（シャドウバン等）")
                    
                    # 重複投稿の可能性がある場合はリトライしない
                    if 'duplicate' in error_msg.lower():
                        print("  → 重複投稿エラー: リトライしません")
                        return {
                            'success': False,
                            'tweet_id': None,
                            'error': f"Duplicate content: {error_msg}"
                        }
                    
                    # 権限エラーの場合もリトライしない
                    if 'authorization' in error_msg.lower() or 'permission' in error_msg.lower():
                        print("  → 権限エラー: リトライしません")
                        return {
                            'success': False,
                            'tweet_id': None,
                            'error': f"Authorization error: {error_msg}"
                        }
                
                # 429エラー（レート制限）の場合は長めに待機
                if '429' in error_msg or (hasattr(e, 'response') and e.response.status_code == 429):
                    wait_time = 60 * (attempt + 1)  # 1分、2分、3分...
                    print(f"  → レート制限エラー: {wait_time}秒待機します")
                    time.sleep(wait_time)
                    continue
                
                # その他のエラーは指数バックオフでリトライ
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1秒、2秒、4秒...
                    print(f"  → {wait_time}秒後にリトライします")
                    time.sleep(wait_time)
                else:
                    # 最後の試行でも失敗
                    return {
                        'success': False,
                        'tweet_id': None,
                        'error': error_msg
                    }
        
        # すべてのリトライが失敗
        return {
            'success': False,
            'tweet_id': None,
            'error': 'Max retries exceeded'
        }
        
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'tweet_id': None,
            'error': str(e)
        }


def get_tweet_metrics(tweet_id):
    """
    投稿のエンゲージメントデータを取得
    
    Args:
        tweet_id: ツイートID
    
    Returns:
        dict: {impressions, likes, retweets, replies}
    """
    try:
        api_key = os.environ.get('X_API_KEY')
        api_secret = os.environ.get('X_API_SECRET')
        access_token = os.environ.get('X_ACCESS_TOKEN')
        access_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')
        
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # ツイート情報取得
        response = client.get_tweet(
            tweet_id,
            tweet_fields=['public_metrics']
        )
        
        if response.data:
            metrics = response.data.public_metrics
            return {
                'impressions': metrics.get('impression_count', 0),
                'likes': metrics.get('like_count', 0),
                'retweets': metrics.get('retweet_count', 0),
                'replies': metrics.get('reply_count', 0)
            }
        
        return None
        
    except Exception as e:
        print(f"メトリクス取得エラー: {e}")
        return None


if __name__ == "__main__":
    # テスト（実際には投稿しない）
    print("X投稿モジュール テスト")
    print("環境変数:")
    print(f"  X_API_KEY: {'設定済' if os.environ.get('X_API_KEY') else '未設定'}")
    print(f"  X_API_SECRET: {'設定済' if os.environ.get('X_API_SECRET') else '未設定'}")
    print(f"  X_ACCESS_TOKEN: {'設定済' if os.environ.get('X_ACCESS_TOKEN') else '未設定'}")
    print(f"  X_ACCESS_TOKEN_SECRET: {'設定済' if os.environ.get('X_ACCESS_TOKEN_SECRET') else '未設定'}")
