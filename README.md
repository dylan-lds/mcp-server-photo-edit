启动、使用图片翻译功能步骤如下：
0.部署Azure服务，包括Azure OpenAI（本人使用的模型为gpt-4o-mini）、Azure Comuter Vision、Azure Translator. 部署请自行参考官网链接.
ps:以上服务需要使用Azure国际版
1.安装CherryStudio，下载地址如下：
https://www.cherry-ai.com/download
2.安装python环境(本人安装的版本为Python 3.12.3)，参考如下地址安装：
https://blog.csdn.net/sensen_kiss/article/details/141940274
3.用 VS code 打开 mcp-server-photo-edit 项目，该项目在本文件统计目录下，同时已上传到github，地址如下：
https://github.com/dylan-lds/mcp-server-photo-edit.git
Repo访问需要申请权限，请联系15254118710@163.com。
4.替换环境变量。打开 mcp-server-photo-edit 根目录下的 .env 文件，将 Azure computer Vision 信息以及 Azure Translator 信息替换成自己的。
获取 Azure computer Vision 以及 Azure Translator 信息的方法请参考Azure官网链接。
5.启动mcp服务。在 mcp-server-photo-edit 根目录下执行 python3 phototranslator.py 命令即可。
6.在CherryStudio中配置mcp server:
打开CherryStudio -> 左下角的设置 -> MCP服务器 -> 添加服务器，类型为streamableHttp，没有修改代码配置的情况下，URL为http://localhost:8000/stream -> 保存
7.添加模型服务:
设置 -> 模型服务 -> Azure OpenAI -> 填写密钥、API地址(URL中需要携带着api-version)、API版本
8.修改默认模型：
设置 -> 默认模型 -> 全都修改为Azure OpenAI模型
9.对话中使用mcp：
新建助手 -> 对话框的下方有MCP服务器按钮 -> 选中配置的mcp server -> 传入本地图片路径，比如:"帮我翻译/Users/dylan/workspace/mt.jpg这个图片，翻译为韩文，翻译成功后告知我图片的位置"
10.查看图片翻译效果。