from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from ocr import ocr_image, OCRRequest
from translator import translate_text, TranslationRequest
from photoedit import photo_edit_tool, TextInfo, PositionInfo

class PhotoTranslationRequest(BaseModel):
    """图片翻译请求模型"""
    imagePath: str
    to_language: str = Field(default="en", description="目标语言，默认为英文")
    from_language: Optional[str] = None

# Create a named server
app = FastMCP("PhotoTranslatorServer", stateless_http=True)

@app.tool()
def translate_image(request: PhotoTranslationRequest):
    """翻译图片中的文字

    Args:
        request: 图片翻译请求，包含图片路径和目标语言
    """
    try:
        # 1. OCR识别图片中的文字
        print(f"开始OCR识别: {request.imagePath}")
        ocr_request = OCRRequest(imagePath=request.imagePath)
        ocr_result = ocr_image(ocr_request)
        
        if ocr_result["status"] != "success":
            return ocr_result
        
        # 提取需要翻译的文本
        texts_to_translate = []
        text_positions = []
        for item in ocr_result["results"]:
            texts_to_translate.append(item["text"])
            text_positions.append(item["boundingPolygon"])
        
        if not texts_to_translate:
            return {
                "status": "error",
                "message": "未在图片中识别到文字"
            }
        
        # 2. 翻译识别出的文字
        print(f"开始翻译 {len(texts_to_translate)} 段文本...")
        translation_request = TranslationRequest(
            texts=texts_to_translate,
            to_language=request.to_language,
            from_language=request.from_language
        )
        translation_result = translate_text(translation_request)
        
        if translation_result["status"] != "success":
            return translation_result
        
        # 3. 将翻译结果写回图片
        print("开始更新图片...")
        text_lines = []
        for i, translation in enumerate(translation_result["translations"]):
            text_line = TextInfo(
                text=translation["translated"],
                boundingPolygon=[
                    PositionInfo(**pos) for pos in text_positions[i]
                ]
            )
            text_lines.append(text_line)
        
        # 生成输出文件路径
        output_message = photo_edit_tool(
            imagePath=request.imagePath,
            textLines=text_lines
        )
        
        return {
            "status": "success",
            "original_texts": texts_to_translate,
            "translations": [t["translated"] for t in translation_result["translations"]],
            "output_message": output_message,
            "message": "图片翻译完成"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "图片翻译过程中发生错误"
        }

if __name__ == "__main__":
    # 测试图片翻译功能
    # test_request = PhotoTranslationRequest(
    #     imagePath="/Users/liudashuai/workspace/mt.jpg",
    #     to_language="en"
    # )
    # print("正在测试图片翻译功能...")
    # print(f"测试图片路径: {test_request.imagePath}")
    
    # result = translate_image(test_request)
    # print("\n翻译结果:")
    # print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 启动服务器
    app.settings.streamable_http_path = "/stream"
    app.run(transport="streamable-http")