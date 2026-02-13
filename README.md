# AI Coding 学习网站（MVP）

这是一个围绕 **AI Coding 学习与内容共建** 的基础项目，提供：

- AI 工具教程、实战案例、skills 内容库
- 用户上传内容
- 接入 AI 质量审查（当前为可替换的 mock reviewer）
- 定期网络资源更新（当前为可替换的 mock crawler）

## 快速启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问 <http://127.0.0.1:8000>

## 下一步建议

1. 将 `AIQualityReviewer` 替换为真实模型调用（OpenAI/Anthropic/自建模型）
2. 将 `ResourceCrawler` 替换为搜索 API（SerpAPI/Tavily/自建爬虫）
3. 增加用户认证与权限控制
4. 增加内容版本历史、举报机制、审核工作台
5. 增加 RAG 检索与学习路径推荐
