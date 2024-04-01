from bs4 import BeautifulSoup
import abc
from typing import Any
from langchain.tools import BaseTool
import requests

class WebPageScraper(BaseTool, abc.ABC):
    name = "WebPageScraper"
    description = "此工具用于获取网页内容，使用时请传入需要查询的网页地址作为参数，如：https://www.baidu.com/。" 
 
    def __init__(self):
        super().__init__()

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        # 用例中没有用到 arun 不予具体实现
        pass

    def _run(self, para) -> str:
        try:
            response = requests.get(para)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except Exception as e:
            print("Http Error:", e)
            return '无法获取该网页内容'
        
if __name__ == "__main__":
    tool = WebPageScraper()
    result = tool.run("https://www.thepaper.cn/newsDetail_forward_25053714")
    print(result)
