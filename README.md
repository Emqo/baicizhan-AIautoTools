# Baicizhan-AI-Script (百词斩AI智能答题脚本)



本项目是一个基于 `uiautomator2` 和多模态大模型（如 DeepSeek-VL, Qwen-VL）的百词斩学习自动化脚本。通过纯视觉识别屏幕截图，AI 可以自动识别题型、理解图片或文字含义，并给出正确答案，从而帮助用户快速完成每日单词任务。

**免责声明：** 本项目仅供学习和技术交流使用，请勿用于任何商业用途。使用本工具可能违反百词斩的用户协议，请自行承担风险。



## ✨ 主要功能



- **纯视觉识别：** 不依赖任何内部接口或 OCR 库，直接通过截图将题目发送给 AI 模型进行分析和作答。
- **多题型支持：**
  - **图片选择题：** 识别单词/例句，选择对应的图片。
  - **词义选择题：** 识别单词，选择正确的中文释义。
  - **拼写题：** 识别单词，自动输入正确的拼写。
- **多模型支持：** 支持 DeepSeek、通义千问（Qwen）、SiliconFlow、OpenRouter 等多种主流视觉大模型。
- **跨平台兼容：** 基于 `uiautomator2`，支持 Android 手机和主流模拟器（如 MuMu、雷电、夜神）。



## 🛠️ 环境要求





### 硬件与软件



1. **Android 设备或模拟器：** 推荐使用 Android 7.0 及以上版本。
2. **ADB 环境：** 确保电脑上安装了 ADB (Android Debug Bridge) 并能正常连接设备。
3. **Python 环境：** 推荐使用 Python 3.8+。



### Python 依赖



使用 `pip` 安装所需的库：

Bash

```
pip install uiautomator2 pillow requests
```



## 🚀 安装与配置





### 步骤一：连接设备



你需要将你的 Android 设备（手机或模拟器）通过 ADB 连接到电脑。

**推荐使用模拟器：**

1. 启动 MuMu 模拟器（或其他模拟器）。

2. 在模拟器设置中开启 ADB 连接。

3. 获取模拟器的 ADB 地址，例如 `127.0.0.1:7555`。

4. 运行以下命令进行测试：

   Bash

   ```
   adb connect 127.0.0.1:7555
   # 出现 "connected to 127.0.0.1:7555" 即连接成功
   ```



### 步骤二：获取 API Key



本项目依赖视觉大模型进行识别和推理。你需要选择一个 AI 服务并获取其 API Key。

| **服务商**      | **推荐模型**                       | **获取 Key 地址**                                            |
| --------------- | ---------------------------------- | ------------------------------------------------------------ |
| **DeepSeek**    | `deepseek-chat`                    | [DeepSeek Platform](https://platform.deepseek.com/)          |
| **通义千问**    | `qwen3-vl-flash`                   | [阿里云 DashScope](https://dashscope.console.aliyun.com/apiKey) |
| **OpenRouter**  | `google/gemini-2.0-flash-exp:free` | [OpenRouter Keys](https://openrouter.ai/keys)                |
| **SiliconFlow** | `Qwen/Qwen2-VL-7B-Instruct`        | [SiliconFlow 账号中心](https://siliconflow.cn/account/ak)    |



### 步骤三：修改脚本配置



打开 `[你的脚本文件名].py` 文件，修改 `main()` 函数中的配置区域：

Python

```
# [脚本文件名].py 中的 main() 函数部分

def main():
    # ...
    # ===== 配置区域 =====
    # ⬇️ 请将此处的 YOUR_DEVICE_IP_HERE 替换为你设备的实际 IP 地址 (例如 "127.0.0.1:7555")
    device_ip = "YOUR_DEVICE_IP_HERE"  # <--- 修改这里
    use_ai = True                      # 是否使用AI（推荐 True）
    api_type = "qwen"                  # <--- 根据你的 Key 选择对应的类型 (deepseek/qwen/siliconflow/openrouter)
    word_count = 20                    # 每日单词数量

    # ⚠️ 重要：请将此处的 YOUR_API_KEY_HERE 替换为你申请到的真实 API Key
    custom_api_key = "YOUR_API_KEY_HERE"  # <--- 修改这里
    # ===================
    # ...
```



## ▶️ 使用说明



配置完成后，在命令行中运行脚本即可：

Bash

```
python [你的脚本文件名].py
```

脚本将自动执行以下操作：

1. 连接设备。
2. 启动百词斩 App。
3. 进入学习模式。
4. 循环截图、调用 AI 分析、点击答案，直至完成设定的单词量。

------



## 常见问题 (FAQ)





### 1. 为什么 AI 答题总是出错？



- **API Key 错误：** 检查 `custom_api_key` 是否正确填写。
- **`api_type` 匹配错误：** 检查 `api_type` 是否与你的 `custom_api_key` 来源（例如 DeepSeek 或 Qwen）匹配。
- **网络问题：** 确保你的网络可以稳定访问 AI 服务的 API 地址。
- **模型限制：** 如果使用免费或较小的模型（如某些 OpenRouter 或 SiliconFlow 模型），识别准确率可能会有所下降，可尝试更换为 DeepSeek 或 Qwen。



### 2. 为什么脚本点不到按钮？



- **坐标偏差：** 本脚本中的点击坐标是针对作者的模拟器分辨率（通常是 1080p 竖屏）进行设置的。如果你的设备分辨率不同，可能需要微调脚本中 `answer_image_question_ai` 和 `answer_definition_question_ai` 方法中的 `positions` 字典的坐标值。
- **元素识别失败：** 检查 App 界面是否有更新，导致脚本中通过 `text` 定位元素（如 "继续"、"斩"）失败。



### 3. 如何知道我设备的 ADB 地址？



- **真机：** 需要开启开发者选项和 USB 调试，并通过数据线连接。地址通常是 `localhost:5037` 或不需要指定。
- **模拟器：**
  - MuMu：`127.0.0.1:7555`
  - 雷电：`127.0.0.1:5555`
  - 夜神：`127.0.0.1:62001`