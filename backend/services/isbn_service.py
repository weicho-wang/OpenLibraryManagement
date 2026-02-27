import httpx
from typing import Optional, Dict, Any


class ISBNService:
    """豆瓣API查询图书信息（免费，有频率限制）"""
    
    DOUBAN_API = "https://api.douban.com/v2/book/isbn/{}"
    
    @staticmethod
    async def query_douban(isbn: str) -> Optional[Dict[str, Any]]:
        """查询豆瓣API"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # 豆瓣API需要API Key，这里用公开接口（可能有频率限制）
                # 实际生产建议：1. 申请豆瓣API Key 2. 或使用国家图书馆API 3. 或自建爬虫
                url = f"https://book.feelyou.top/isbn/{isbn}"
                resp = await client.get(url)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "isbn": isbn,
                        "title": data.get("title", ""),
                        "author": ", ".join(data.get("author", [])) if isinstance(data.get("author"), list) else data.get("author", ""),
                        "publisher": data.get("publisher", ""),
                        "publish_date": data.get("pubdate", ""),
                        "cover_url": data.get("images", {}).get("large") or data.get("cover"),
                        "summary": data.get("summary", ""),
                        "tags": [t.get("name") for t in data.get("tags", [])][:5]  # 取前5个标签
                    }
        except Exception as e:
            print(f"ISBN query failed: {e}")
        
        return None
    
    @staticmethod
    async def query_openlibrary(isbn: str) -> Optional[Dict[str, Any]]:
        """备用：OpenLibrary API（英文书较多）"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                url = f"https://openlibrary.org/isbn/{isbn}.json"
                resp = await client.get(url)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "isbn": isbn,
                        "title": data.get("title", ""),
                        "author": "",
                        "publisher": "",
                        "publish_date": "",
                        "cover_url": f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
                        "summary": "",
                        "tags": []
                    }
        except Exception:
            pass
        
        return None


isbn_service = ISBNService()
