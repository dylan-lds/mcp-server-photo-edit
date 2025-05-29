from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List
import requests
import time
from PIL import Image
import io
import json
import os
from dotenv import load_dotenv
import traceback

# 加载 .env 文件
load_dotenv()

class PositionInfo(BaseModel):
    x: int
    y: int

class TextInfo(BaseModel):
    text: str
    boundingPolygon: List[PositionInfo]

class OCRRequest(BaseModel):
    """OCR请求模型"""
    imagePath: str

# Create a named server
app = FastMCP("OCRServer", stateless_http=True)

@app.tool()
def ocr_image(request: OCRRequest):
    try:
        # Azure 计算机视觉API配置
        endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        subscription_key = os.getenv("AZURE_VISION_KEY")
        
        print(f"使用配置: \nEndpoint: {endpoint}\nKey: {subscription_key[:5]}...")

        if not endpoint or not subscription_key:
            return {
                "status": "error",
                "error": "未配置 Azure Vision API",
                "message": "请在 .env 文件中配置 AZURE_VISION_ENDPOINT 和 AZURE_VISION_KEY"
            }

        # 读取图片并转换为bytes
        image_path = request.imagePath
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        # 第一步：提交图片进行分析
        headers = {
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': subscription_key
        }
        
        analyze_url = f"{endpoint}/vision/v3.2/read/analyze"
        response = requests.post(analyze_url, headers=headers, data=image_data)
        response.raise_for_status()

        # 从响应头部获取操作位置
        operation_url = response.headers["Operation-Location"]

        # 第二步：等待并获取分析结果
        analysis = {}
        while True:
            response = requests.get(
                operation_url,
                headers={"Ocp-Apim-Subscription-Key": subscription_key}
            )
            analysis = response.json()

            if "status" in analysis and analysis["status"] not in ['notStarted', 'running']:
                break
            time.sleep(1)

        # 处理结果
        results = []
        if analysis.get("status") == "succeeded" and "analyzeResult" in analysis:
            print("\nAPI 返回的原始数据:")
            print(json.dumps(analysis, ensure_ascii=False, indent=2))
            
            for read_result in analysis["analyzeResult"]["readResults"]:
                for line in read_result["lines"]:
                    # 获取边界框坐标
                    bbox = line["boundingBox"]
                    print(f"\n处理文本行: {line['text']}")
                    print(f"边界框数据: {bbox}")
                    
                    # 创建四个角点的 PositionInfo 对象
                    polygon = []
                    for i in range(0, len(bbox), 2):
                        pos = PositionInfo(x=int(bbox[i]), y=int(bbox[i + 1]))
                        polygon.append(pos)
                        print(f"转换坐标点: {pos}")

                    result = TextInfo(
                        text=line["text"],
                        boundingPolygon=polygon
                    )
                    results.append(result)

        return {
            "status": "success",
            "results": [result.dict() for result in results],
            "message": f"成功识别 {len(results)} 行文本"
        }

    except Exception as e:
        print("\n发生错误:")
        print(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "message": "OCR识别过程中发生错误"
        }

if __name__ == "__main__":
    # 测试 OCR 功能
    test_request = OCRRequest(imagePath="C:\\Users\\Think\\Desktop\\lab_mt.jpg")
    print("正在测试OCR功能...")
    print(f"测试图片路径: {test_request.imagePath}")
    
    result = ocr_image(test_request)
    print("\nOCR 结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 启动OCR服务器
    app.settings.streamable_http_path = "/stream"
    app.run(transport="streamable-http")