from mcp.server.fastmcp import FastMCP
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel
import os

class PositionInfo(BaseModel):
    x: int
    y: int

class TextInfo(BaseModel):
    text: str
    boundingPolygon: list[PositionInfo]

# class LineInfo(BaseModel):
#     text: str
#     boundingPolygon: list[PositionInfo]
#     words: list[TextInfo]


# Create a named server
app = FastMCP("PhotoEditServer", stateless_http=True)


@app.tool()
def photo_edit_tool(imagePath: str, textLines: list[TextInfo]):
    """在指定图片上编辑文字。
    
    Args:
        imagePath: 要编辑的图片路径。
        textLines: 文本行信息列表，每个文本行包含文本内容、边界框和单词信息。
    
    示例输入:
    {
        "imagePath": "C:\\Users\\Think\\Desktop\\example.png",
        "textLines": [
            {
                "text": "Hello World",
                "boundingPolygon": [
                    {"x": 10, "y": 10},  # 左上
                    {"x": 100, "y": 10},  # 右上
                    {"x": 100, "y": 50},  # 右下
                    {"x": 10, "y": 50}    # 左下
                ],
            }
        ]
    }
    """
    output_path = draw_text_on_image(imagePath, textLines)
    return f"处理后的图片已保存至: {output_path}"


def get_font_size(text: str, max_width: float, max_height: float, font_path: str) -> ImageFont.FreeTypeFont:
    """
    二分查找合适的字体大小
    """
    size_min = 1
    size_max = 100
    font = None
    target_font = None
    
    while size_min <= size_max:
        size = (size_min + size_max) // 2
        font = ImageFont.truetype(font_path, size)
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        if text_width <= max_width and text_height <= max_height:
            target_font = font
            size_min = size + 1
        else:
            size_max = size - 1
    
    return target_font or ImageFont.truetype(font_path, 1)

def draw_text_on_image(image_path: str, textLines: list[TextInfo], output_path=None):
    print(f"即将处理请求: {textLines}")
    """
    在图片OCR识别出的区域中绘制新文本
    Args:
        image_path: 原始图片路径
        textLines: 文本行列表
        output_path: 输出图片路径，如果为None则在原图片名后添加_output
    """
    # 打开原始图片
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    font_path = "NotoSansMonoCJK-VF.otf"

    # 遍历OCR结果中的每个文本区域
    if textLines:
        for line in textLines:
            # 获取边界多边形的坐标
            bbox = []
            for point in line.boundingPolygon:
                bbox.extend([point.x, point.y])
            
            # 计算文本框的尺寸
            x_coords = bbox[::2]  # 所有x坐标
            y_coords = bbox[1::2]  # 所有y坐标
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            
            # 计算文本框的中心点
            x1, y1 = bbox[0], bbox[1]  # 左上角
            x3, y3 = bbox[4], bbox[5]  # 右下角
            center_x = (x1 + x3) / 2
            center_y = (y1 + y3) / 2
            
            # 在原文本位置绘制白色背景
            draw.polygon([
                (bbox[0], bbox[1]),
                (bbox[2], bbox[3]),
                (bbox[4], bbox[5]),
                (bbox[6], bbox[7])
            ], fill='white')
            
            # 使用新的文本内容
            text = line.text
            
            # 获取适合边界框的字体大小
            try:
                font = get_font_size(text, width * 0.9, height * 0.9, font_path)  # 留出10%的边距
            except IOError:
                font = ImageFont.load_default()
                
            # 获取文本大小以居中显示
            text_bbox = font.getbbox(text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # 计算文本绘制位置（居中）
            text_x = center_x - text_width / 2
            text_y = center_y - text_height / 2
            
            # 绘制文本
            draw.text((text_x, text_y), text, fill='black', font=font)

    # 如果没有指定输出路径，则在原文件名后添加_output
    if output_path is None:
        file_name, file_ext = os.path.splitext(image_path)
        output_path = f"{file_name}_output{file_ext}"
    
    # 保存结果
    image.save(output_path)
    print(f"处理后的图片已保存至: {output_path}")
    return output_path

if __name__ == "__main__":
    # 启动FastMCP服务器
    app.settings.streamable_http_path = "/stream"
    app.run(transport="streamable-http")