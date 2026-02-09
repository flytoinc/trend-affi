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
            'trendnews': ['scraped_at', 'title', 'url', 'keywords', 'status', 'selected_product', 'notes'],
            'posts': ['posted_at', 'news_url', 'news_title', 'product_title', 
                     'product_url', 'product_price', 'post_text', 'tweet_id',
                     'impressions', 'likes', 'retweets', 'replies', 'engagement_rate'],
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
        取得したニュース記事をログに記録
        
        Args:
            news_items: ニュース記事のリスト
        """
        try:
            worksheet = self.spreadsheet.worksheet('trendnews')
            
            for news in news_items:
                keywords_str = ', '.join(news.get('keywords', []))
                row = [
                    datetime.now().isoformat(),
                    news.get('title', ''),
                    news.get('url', ''),
                    keywords_str,
                    'scraped',  # status
                    '',  # selected_product
                    ''   # notes
                ]
                worksheet.append_row(row)
            
            print(f"trendnewsシートに{len(news_items)}件記録")
            
        except Exception as e:
            print(f"ニュースログ記録エラー: {e}")
    
    def update_news_status(self, news_url, status, product_title='', notes=''):
        """
        ニュースのステータスを更新
        
        Args:
            news_url: ニュースURL
            status: 'scraped', 'selected', 'posted', 'skipped'
            product_title: 選択された商品名
            notes: メモ
        """
        try:
            worksheet = self.spreadsheet.worksheet('trendnews')
            records = worksheet.get_all_records()
            
            for i, record in enumerate(records, start=2):
                if record.get('url') == news_url:
                    worksheet.update(f'E{i}:G{i}', [[status, product_title, notes]])
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
