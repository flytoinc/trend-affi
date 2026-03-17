"""
X（Twitter）投稿機能
tweepyを使用してX APIで投稿
画像添付対応: 商品画像をダウンロード→アップロード→添付投稿
403エラー対策: リトライロジック、詳細エラーログ、重複検出
"""
import os
import time
import tempfile
import requests
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


def _download_image(image_url, timeout=15):
    """
    画像URLからファイルをダウンロードし一時ファイルに保存
    
    Args:
        image_url: 画像URL
        timeout: タイムアウト秒
    
    Returns:
        str or None: 一時ファイルパス（失敗時None）
    """
    try:
        response = requests.get(image_url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        response.raise_for_status()
        
        # Content-Typeから拡張子を判定
        content_type = response.headers.get('Content-Type', '')
        if 'png' in content_type:
            ext = '.png'
        elif 'gif' in content_type:
            ext = '.gif'
        elif 'webp' in content_type:
            ext = '.webp'
        else:
            ext = '.jpg'
        
        tmp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tmp_file.write(response.content)
        tmp_file.close()
        
        return tmp_file.name
        
    except Exception as e:
        print(f"  画像ダウンロードエラー: {e}")
        return None


def post_to_x_with_image(text, image_url, max_retries=3):
    """
    画像付きでXに投稿する
    画像アップロード失敗時はテキストのみで投稿
    
    Args:
        text: 投稿テキスト
        image_url: 商品画像のURL
        max_retries: 最大リトライ回数
    
    Returns:
        dict: {success: bool, tweet_id: str, error: str}
    """
    if not image_url:
        return post_to_x(text, max_retries=max_retries)
    
    try:
        api_key = os.environ.get('X_API_KEY')
        api_secret = os.environ.get('X_API_SECRET')
        access_token = os.environ.get('X_ACCESS_TOKEN')
        access_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')
        
        if not all([api_key, api_secret, access_token, access_secret]):
            return post_to_x(text, max_retries=max_retries)
        
        # 画像をダウンロード
        print(f"  画像ダウンロード中: {image_url[:80]}...")
        image_path = _download_image(image_url)
        
        if not image_path:
            print("  → 画像取得失敗、テキストのみで投稿")
            return post_to_x(text, max_retries=max_retries)
        
        try:
            # v1.1 API で画像アップロード（media_upload は v1.1 のみ）
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_secret
            )
            api_v1 = tweepy.API(auth)
            
            media = api_v1.media_upload(filename=image_path)
            media_id = media.media_id
            
            print(f"  画像アップロード成功: media_id={media_id}")
            
            # v2 Client で画像付き投稿
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret
            )
            
            for attempt in range(max_retries):
                try:
                    response = client.create_tweet(
                        text=text,
                        media_ids=[media_id]
                    )
                    tweet_id = response.data['id']
                    print(f"  画像付き投稿成功! Tweet ID: {tweet_id}")
                    return {
                        'success': True,
                        'tweet_id': tweet_id,
                        'error': None
                    }
                except tweepy.TweepyException as e:
                    error_msg = str(e)
                    print(f"  画像付き投稿エラー (attempt {attempt + 1}): {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        # 画像付きが失敗したらテキストのみで再試行
                        print("  → 画像付き投稿失敗、テキストのみで再試行")
                        return post_to_x(text, max_retries=1)
            
        finally:
            # 一時ファイルを削除
            try:
                os.unlink(image_path)
            except:
                pass
        
    except Exception as e:
        print(f"  画像投稿エラー: {e}、テキストのみで投稿")
        return post_to_x(text, max_retries=max_retries)


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


def quote_retweet(text, quote_tweet_id, max_retries=3):
    """
    引用リツイートを投稿する
    
    Args:
        text: 引用コメント
        quote_tweet_id: 引用する元ツイートのID
        max_retries: 最大リトライ回数
    
    Returns:
        dict: {success: bool, tweet_id: str, error: str}
    """
    try:
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
        
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        for attempt in range(max_retries):
            try:
                response = client.create_tweet(
                    text=text,
                    quote_tweet_id=quote_tweet_id
                )
                
                tweet_id = response.data['id']
                print(f"引用RT成功: ID={tweet_id}")
                
                return {
                    'success': True,
                    'tweet_id': tweet_id,
                    'error': None
                }
                
            except tweepy.TweepyException as e:
                error_msg = str(e)
                print(f"引用RTエラー (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
                if '403' in error_msg:
                    print("  → 403 Forbidden。30秒待機して再試行...")
                    time.sleep(30)
                elif '429' in error_msg:
                    print("  → レート制限。60秒待機して再試行...")
                    time.sleep(60)
                elif '187' in error_msg:
                    return {
                        'success': False,
                        'tweet_id': None,
                        'error': 'Status is a duplicate'
                    }
                else:
                    time.sleep(10)
        
        return {
            'success': False,
            'tweet_id': None,
            'error': f'Max retries ({max_retries}) exceeded'
        }
        
    except Exception as e:
        return {
            'success': False,
            'tweet_id': None,
            'error': str(e)
        }


if __name__ == "__main__":
    # テスト（実際には投稿しない）
    print("X投稿モジュール テスト")
    print("環境変数:")
    print(f"  X_API_KEY: {'設定済' if os.environ.get('X_API_KEY') else '未設定'}")
    print(f"  X_API_SECRET: {'設定済' if os.environ.get('X_API_SECRET') else '未設定'}")
    print(f"  X_ACCESS_TOKEN: {'設定済' if os.environ.get('X_ACCESS_TOKEN') else '未設定'}")
    print(f"  X_ACCESS_TOKEN_SECRET: {'設定済' if os.environ.get('X_ACCESS_TOKEN_SECRET') else '未設定'}")
