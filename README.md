# 📘 百词斩自动刷题脚本（基于 uiautomator2 + AI 识别）

## 🚀 功能说明
本脚本通过 `uiautomator2` 控制 Android 设备或模拟器，结合大模型接口自动识别百词斩题目并作答。  
可识别普通词义选择题、自动输入拼写题答案（可关闭）。  

支持的 AI 模型：
- Qwen3-VL
- DeepSeek-VL
- SiliconFlow Qwen2-VL
- OpenRouter Gemini Flash  

## ⚙️ 环境要求
- Python 3.9+
- 已安装 `uiautomator2`、`requests`、`Pillow`、`adb` 工具
- 模拟器或手机已通过 `adb` 连接（可用命令 `adb devices` 验证）
- 百词斩 App 已安装，包名：`com.jiongji.andriod.card`

## 📦 安装依赖
```bash
pip install uiautomator2 requests pillow
初始化设备（只需一次）：

bash
复制代码
python -m uiautomator2 init
🧩 使用说明
启动模拟器（推荐分辨率 1080x1920）

关闭百词斩内的以下功能（非常重要）：

❌ 图片显示（防止AI识别干扰）

❌ 拼写题（暂不稳定，可在百词斩设置中关闭拼写练习）

❌ 音频播放（不方便识别或影响自动点击）

在百词斩主界面停留在首页。

运行脚本：

bash
复制代码
python main.py
程序会自动：

连接模拟器（默认 127.0.0.1:7555）

启动百词斩 App

自动点击“学习”按钮

识别题目截图 → AI判断正确答案 → 自动点击选项

自动进入下一题，循环执行

⚠️ 注意事项
脚本会自动保存截图为 last_question.png

如果找不到“学习”按钮，会用默认坐标点击（可根据设备分辨率自行调整）

API 调用频繁时可能受限，请使用自己的有效 API Key

如果 AI 返回异常，程序会随机选择一个选项防止卡死

若要改动设备连接地址，请修改：

python
复制代码
bot = BaicizhanAuto(device_ip="你的adb地址", ...)
若要彻底关闭拼写题识别，可注释掉：

python
复制代码
if self.d(className="android.widget.EditText").exists:
    self.answer_spelling_question(screenshot)
🧠 示例日志
mathematica
复制代码
📱 正在连接设备:127.0.0.1:7555
✅ 设备连接成功
🚀 正在启动百词斩 App...
✅ 已点击学习按钮
🚀 开始自动刷题（按 Ctrl+C 停止）
🧠 正在让AI判断正确选项...
✅ AI 判断答案：2
👉 点击坐标 (534,1124)
💡 建议
若运行在夜间，请关闭模拟器音量

可使用 DeepSeek 或 Qwen API 以提高识别速度
