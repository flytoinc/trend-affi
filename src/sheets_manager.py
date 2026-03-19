"""
Google Sheets管理
投稿記録・ニュースログ・学習データの保存・取得
"""
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials


class SheetsManager:
    """Google Sheetsとの接続・データ管理"""
    
    def __init__(self, credentials_json, sheet_key):
        """
        初期化
        
        Args:
            credentials_json: サービスアカウントのJSON（文字列）
            sheet_key: スプレッドシートのキー
        """
        self.sheet_key = sheet_key
        
        # 認証情報をパース
        if isinstance(credentials_json, str):
            creds_dict = json.loads(credentials_json)
        else:
            creds_dict = credentials_json
        
        # スコープ設定
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        self.client = gspread.authorize(credentials)
        
        # スプレッドシートを開く
        self.spreadsheet = self.client.open_by_key(sheet_key)
        
        # シート初期化
        self._init_sheets()
    
    def _init_sheets(self):
        """必要なシートを初期化"""
        required_sheets = {
            'trendnews': ['scraped_at', 'trend_name', 'trend_reason', 'title', 'url', 'keywords', 'status', 'selected_product', 'notes', 'source'],
            'posts': ['posted_at', 'news_url', 'news_title', 'product_title', 
                     'product_url', 'product_price', 'post_text', 'tweet_id',
                     'impressions', 'likes', 'retweets', 'replies', 'engagement_rate'],
            'quote_retweets': ['quoted_at', 'trend_name', 'original_tweet_id', 'original_author',
                              'original_text', 'quote_text', 'quote_tweet_id'],
            'config': ['key', 'value']
        }
        
        existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()]
        
        for sheet_name, headers in required_sheets.items():
            if sheet_name not in existing_sheets:
                worksheet = self.spreadsheet.add_worksheet(sheet_name, 1000, len(headers))
                worksheet.update('A1', [headers])
                print(f"シート作成: {sheet_name}")
            else:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                # ヘッダーがなければ追加
                if not worksheet.row_values(1):
                    worksheet.update('A1', [headers])
    
    def log_news_items(self, news_items):
        """
        取得したトレンド/ニュース記事をログに記録
        
        Args:
            news_items: ニュース記事のリスト
        """
        try:
            worksheet = self.spreadsheet.worksheet('trendnews')
            
            for news in news_items:
                keywords_str = ', '.join(news.get('keywords', []))
                row = [
                    datetime.now().isoformat(),
                    news.get('trend_name', ''),  # トレンド名
                    news.get('trend_reason', ''),  # トレンド理由
                    news.get('title', ''),
                    news.get('url', ''),
                    keywords_str,
                    'scraped',  # status
                    '',  # selected_product
                    '',  # notes
                    news.get('source', '')  # source (google_trends / x_trends)
                ]
                worksheet.append_row(row)
            
            print(f"trendnewsシートに{len(news_items)}件記録")
            
        except Exception as e:
            print(f"ニュースログ記録エラー: {e}")
    
    def update_news_status(self, news_url, status, product_title='', notes=''):
        """
        ニュースのステータスを更新
        空ヘッダー/重複ヘッダー対策済み
        """
        try:
            worksheet = self.spreadsheet.worksheet('trendnews')
            # get_all_records はヘッダー重複でエラーになるので get_all_values を使用
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                return
            
            headers = all_values[0]
            # url列のインデックスを探す
            url_col = None
            status_col = None
            for i, h in enumerate(headers):
                if h == 'url':
                    url_col = i
                elif h == 'status':
                    status_col = i
            
            if url_col is None:
                return
            
            for row_idx, row in enumerate(all_values[1:], start=2):
                if row_idx > len(all_values):
                    break
                if len(row) > url_col and row[url_col] == news_url:
                    if status_col is not None:
                        worksheet.update_cell(row_idx, status_col + 1, status)
                    print(f"ニュースステータス更新: {status}")
                    return
            
        except Exception as e:
            print(f"ニュースステータス更新エラー: {e}")
    
    def get_posted_urls(self):
        """投稿済みニュースURLを取得"""
        try:
            worksheet = self.spreadsheet.worksheet('posts')
            records = worksheet.get_all_records()
            return {r['news_url'] for r in records if r.get('news_url')}
        except Exception as e:
            print(f"投稿済みURL取得エラー: {e}")
            return set()
    
    def get_logged_urls(self):
        """trendnewsに記録済みのURLを取得"""
        try:
            worksheet = self.spreadsheet.worksheet('trendnews')
            records = worksheet.get_all_records()
            return {r['url'] for r in records if r.get('url')}
        except Exception as e:
            print(f"記録済みURL取得エラー: {e}")
            return set()
    
    def record_post(self, news_url, news_title, product_title, product_url, 
                   product_price, post_text, tweet_id):
        """
        投稿を記録
        """
        try:
            worksheet = self.spreadsheet.worksheet('posts')
            
            row = [
                datetime.now().isoformat(),
                news_url,
                news_title,
                product_title,
                product_url,
                product_price,
                post_text,
                tweet_id,
                '',  # impressions（後で更新）
                '',  # likes
                '',  # retweets
                '',  # replies
                ''   # engagement_rate
            ]
            
            worksheet.append_row(row)
            print(f"投稿記録完了: {tweet_id}")
            
            # trendnewsのステータスも更新
            self.update_news_status(news_url, 'posted', product_title)
            
        except Exception as e:
            print(f"投稿記録エラー: {e}")
    
    def get_top_engagement_posts(self, limit=10):
        """
        高エンゲージメント投稿を取得
        """
        try:
            worksheet = self.spreadsheet.worksheet('posts')
            records = worksheet.get_all_records()
            
            valid_records = [
                r for r in records 
                if r.get('engagement_rate') and float(r.get('engagement_rate', 0)) > 0
            ]
            
            sorted_records = sorted(
                valid_records,
                key=lambda x: float(x.get('engagement_rate', 0)),
                reverse=True
            )
            
            return sorted_records[:limit]
            
        except Exception as e:
            print(f"高反応投稿取得エラー: {e}")
            return []
    
    def update_engagement_metrics(self, tweet_id, metrics):
        """
        エンゲージメントデータを更新
        """
        try:
            worksheet = self.spreadsheet.worksheet('posts')
            records = worksheet.get_all_records()
            
            for i, record in enumerate(records, start=2):
                if str(record.get('tweet_id')) == str(tweet_id):
                    impressions = metrics.get('impressions', 0)
                    if impressions > 0:
                        likes = metrics.get('likes', 0)
                        retweets = metrics.get('retweets', 0)
                        replies = metrics.get('replies', 0)
                        engagement_rate = (likes + retweets * 2 + replies * 3) / impressions * 100
                    else:
                        engagement_rate = 0
                    
                    worksheet.update(f'I{i}:M{i}', [[
                        metrics.get('impressions', ''),
                        metrics.get('likes', ''),
                        metrics.get('retweets', ''),
                        metrics.get('replies', ''),
                        round(engagement_rate, 2)
                    ]])
                    
                    print(f"メトリクス更新: {tweet_id}")
                    return
            
            print(f"該当投稿が見つかりません: {tweet_id}")
            
        except Exception as e:
            print(f"メトリクス更新エラー: {e}")


    def get_pending_metrics_posts(self, hours_after_post=24):
        """
        エンゲージメントが未回収の投稿を取得
        投稿後N時間以上経過し、impressionsが空の投稿
        
        Args:
            hours_after_post: 投稿後何時間以上経過した投稿を対象にするか
        
        Returns:
            list: 未回収の投稿レコードのリスト
        """
        try:
            from datetime import timedelta
            
            worksheet = self.spreadsheet.worksheet('posts')
            records = worksheet.get_all_records()
            
            cutoff_time = datetime.now() - timedelta(hours=hours_after_post)
            pending = []
            
            for record in records:
                posted_at_str = record.get('posted_at', '')
                tweet_id = record.get('tweet_id', '')
                impressions = record.get('impressions', '')
                
                if not posted_at_str or not tweet_id or tweet_id == 'DRY_RUN':
                    continue
                
                # 既に回収済み（impressionsが入っている）ならスキップ
                if impressions != '' and impressions != 0:
                    continue
                
                try:
                    posted_at = datetime.fromisoformat(posted_at_str)
                    if posted_at <= cutoff_time:
                        pending.append(record)
                except:
                    continue
            
            return pending
            
        except Exception as e:
            print(f"未回収投稿取得エラー: {e}")
            return []
    
    def get_recent_trends(self, hours=48):
        """
        過去N時間以内に投稿したトレンド名を取得
        完全一致 + 正規化（スペース除去・小文字化）で重複を判定
        
        Args:
            hours: 何時間前までを対象とするか
        
        Returns:
            set: トレンド名のセット（原文 + 正規化済みの両方を含む）
        """
        try:
            from datetime import timedelta
            import re
            
            worksheet = self.spreadsheet.worksheet('trendnews')
            records = worksheet.get_all_records()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_trends = set()
            
            for record in records:
                scraped_at_str = record.get('scraped_at', '')
                trend_name = record.get('trend_name', '')
                
                if not scraped_at_str or not trend_name:
                    continue
                
                try:
                    scraped_at = datetime.fromisoformat(scraped_at_str)
                    if scraped_at >= cutoff_time:
                        recent_trends.add(trend_name)
                        # 正規化版も追加（スペース除去・小文字化）
                        normalized = re.sub(r'\s+', '', trend_name).lower()
                        recent_trends.add(normalized)
                except:
                    continue
            
            print(f"過去{hours}時間のトレンド: {len(recent_trends)}件")
            return recent_trends
            
        except Exception as e:
            print(f"過去トレンド取得エラー: {e}")
            return set()

    def record_quote_retweet(self, trend_name, original_tweet_id, original_author,
                             original_text, quote_text, quote_tweet_id):
        """引用リツイートを記録"""
        try:
            worksheet = self.spreadsheet.worksheet('quote_retweets')
            row = [
                datetime.now().isoformat(),
                trend_name,
                original_tweet_id,
                original_author,
                original_text[:200],
                quote_text[:200],
                quote_tweet_id
            ]
            worksheet.append_row(row)
            print(f"引用RT記録完了: {trend_name}")
        except Exception as e:
            print(f"引用RT記録エラー: {e}")

    def get_recent_quote_retweet_trends(self, hours=72):
        """
        過去N時間以内に引用RT済みのトレンド名を取得
        
        Returns:
            set: 引用RT済みトレンド名のセット
        """
        try:
            from datetime import timedelta
            import re as re_mod
            
            worksheet = self.spreadsheet.worksheet('quote_retweets')
            records = worksheet.get_all_records()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            quoted_trends = set()
            
            for record in records:
                quoted_at_str = record.get('quoted_at', '')
                trend_name = record.get('trend_name', '')
                
                if not quoted_at_str or not trend_name:
                    continue
                
                try:
                    quoted_at = datetime.fromisoformat(quoted_at_str)
                    if quoted_at >= cutoff_time:
                        quoted_trends.add(trend_name)
                        normalized = re_mod.sub(r'\s+', '', trend_name).lower()
                        quoted_trends.add(normalized)
                except:
                    continue
            
            return quoted_trends
            
        except Exception as e:
            print(f"引用RT履歴取得エラー: {e}")
            return set()


if __name__ == "__main__":
    import os
    
    print("Google Sheets Manager テスト")
    
    creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    key = os.environ.get('GOOGLE_SHEET_KEY')
    
    if creds and key:
        manager = SheetsManager(creds, key)
        print("接続成功")
        
        urls = manager.get_posted_urls()
        print(f"投稿済みURL: {len(urls)}件")
    else:
        print("環境変数が設定されていません")
