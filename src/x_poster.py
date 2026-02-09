"""
X（Twitter）投稿機能
tweepyを使用してX APIで投稿
"""
import os
import tweepy


def post_to_x(text):
    """
    Xに投稿する
    
    Args:
        text: 投稿テキスト
    
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
        print(f"X投稿エラー: {error_msg}")
        
        return {
            'success': False,
            'tweet_id': None,
            'error': error_msg
        }
    except Exception as e:
        print(f"予期せぬエラー: {e}")
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
