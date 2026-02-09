"""
メルカリ商品検索
※現在はダミー商品を返す（Google検索がブロックされるため）
"""
import os


def find_related_products(news_item, limit=5):
    """
    ニュースから関連商品を検索
    
    現在はダミー商品を返す（テスト用）
    """
    keywords = news_item.get('keywords', [])
    
    if not keywords:
        keywords = ['エンタメ']
    
    print(f"検索キーワード: {keywords}")
    
    # ダミー商品を返す（メルカリアンバサダーリンクのテスト用）
    dummy_products = [
        {
            'title': f'{keywords[0]}関連グッズ',
            'price': 2980,
            'likes': 0,
            'url': 'https://jp.mercari.com/item/m12345678901',
            'affiliate_url': generate_affiliate_url('m12345678901'),
            'item_id': 'm12345678901'
        }
    ]
    
    print(f"メルカリ商品: {len(dummy_products)}件取得（ダミー）")
    return dummy_products


def generate_affiliate_url(item_id):
    """
    メルカリアンバサダーのアフィリエイトリンクを生成
    """
    ambassador_id = os.environ.get('MERCARI_AMBASSADOR_ID', '')
    
    if ambassador_id:
        return f"https://jp.mercari.com/item/{item_id}?afid={ambassador_id}"
    else:
        return f"https://jp.mercari.com/item/{item_id}"


if __name__ == "__main__":
    test_news = {
        'title': '【速報】人気アイドルグループ「乃木坂46」新メンバー発表',
        'keywords': ['乃木坂46']
    }
    
    products = find_related_products(test_news)
    for p in products:
        print(f"\n{p['title']}")
        print(f"  ¥{p['price']}")
        print(f"  {p['affiliate_url']}")
