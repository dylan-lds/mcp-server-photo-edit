from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Optional
import requests
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class TranslationRequest(BaseModel):
    """翻译请求模型"""
    texts: List[str]
    to_language: str
    from_language: Optional[str] = None

class TranslatorConfig(BaseModel):
    """Azure Translator配置"""
    key: str = os.getenv("AZURE_TRANSLATOR_KEY", "")
    region: str = os.getenv("AZURE_TRANSLATOR_REGION", "southeastasia")
    api_version: str = "3.0"

# Create a named server
app = FastMCP("TranslatorServer", stateless_http=True)

# 全局配置
translator_config = TranslatorConfig()

@app.tool()
def translate_text(request: TranslationRequest):
    """翻译文本

    Args:
        request: 翻译请求，包含要翻译的文本列表和目标语言

    Returns:
        翻译结果列表，每个元素包含原文和译文
    """
    if not translator_config.key:
        return {
            "status": "error",
            "error": "未配置 Azure Translator 密钥",
            "message": "请先调用 configure_translator 配置服务"
        }

    try:
        # 准备请求
        base_url = f"https://api.cognitive.microsofttranslator.com"
        path = "/translate"
        params = {
            "api-version": translator_config.api_version,
            "to": request.to_language
        }
        if request.from_language:
            params["from"] = request.from_language

        # 准备请求头
        headers = {
            "Ocp-Apim-Subscription-Key": translator_config.key,
            "Ocp-Apim-Subscription-Region": translator_config.region,
            "Content-type": "application/json"
        }

        # 准备请求体
        body = [{"text": text} for text in request.texts]

        # 发送请求
        response = requests.post(
            f"{base_url}{path}",
            params=params,
            headers=headers,
            json=body
        )
        response.raise_for_status()  # 检查响应状态

        # 处理响应
        translations = []
        for i, result in enumerate(response.json()):
            translations.append({
                "original": request.texts[i],
                "translated": result["translations"][0]["text"]
            })

        return {
            "status": "success",
            "translations": translations,
            "message": f"成功翻译 {len(translations)} 条文本"
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "翻译请求失败"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "翻译过程中发生错误"
        }