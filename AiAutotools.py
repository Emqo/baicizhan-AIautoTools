"""
百词斩AI智能答题脚本 - 纯视觉识别版本 v2.3 (修复 'answer_pos' 未定义错误)
支持: 图片选择(单词/例句)、词义选择、拼写题
需要安装: pip install uiautomator2 pillow requests
"""

import uiautomator2 as u2
import time
import random
import base64
import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Dict
import re


class AIHelper:
    """AI助手类 - 直接通过截图识别答案"""

    def __init__(self, api_type: str = "deepseek"):
        """
        初始化AI助手
        :param api_type: AI类型，支持 'deepseek', 'qwen', 'siliconflow', 'openrouter'
        """
        self.api_type = api_type
        self.api_config = self._get_api_config()

    def _get_api_config(self) -> Dict:
        """获取API配置"""
        configs = {
            # DeepSeek API（推荐）
            "deepseek": {
                "url": "https://api.deepseek.com/chat/completions",
                "key": "YOUR_DEEPSEEK_API_KEY",  # <--- 敏感信息已替换
                "model": "deepseek-chat"
            },
            # 阿里通义千问
            "qwen": {
                "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                "key": "YOUR_QWEN_API_KEY",  # <--- 敏感信息已替换
                "model": "qwen3-vl-flash"
            },
            # SiliconFlow（免费）
            "siliconflow": {
                "url": "https://api.siliconflow.cn/v1/chat/completions",
                "key": "YOUR_SILICONFLOW_API_KEY",  # <--- 敏感信息已替换
                "model": "Qwen/Qwen2-VL-7B-Instruct"
            },
            # OpenRouter（聚合多个免费模型）
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "key": "YOUR_OPENROUTER_API_KEY",  # <--- 敏感信息已替换
                "model": "google/gemini-2.0-flash-exp:free"
            }
        }
        return configs.get(self.api_type, configs["deepseek"])

    def image_to_base64(self, image: Image.Image) -> str:
        """将PIL Image转为base64"""
        buffered = BytesIO()
        # 压缩图片以节省token
        image = image.resize((image.width // 2, image.height // 2), Image.Resampling.LANCZOS)
        image.save(buffered, format="PNG", optimize=True)
        return base64.b64encode(buffered.getvalue()).decode()

    def detect_question_type(self, screenshot: Image.Image) -> str:
        """
        让AI检测题目类型
        :param screenshot: 屏幕截图
        :return: 'image' 图片选择 / 'definition' 词义选择 / 'spelling' 拼写题
        """
        try:
            print("正在让AI识别题型...")
            img_base64 = self.image_to_base64(screenshot)

            prompt = """请判断这是百词斩的哪种题型：

1. 图片选择题 (image): 顶部有单词或例句，下方有4张图片(2x2排列)，需要选择匹配的图片。
2. 词义选择题 (definition): 顶部有单词，下方有4个中文词义选项(垂直排列)，需要选择正确的释义。
3. 拼写题 (spelling): 顶部有单词，下方有释义，底部有输入框需要输入单词。

请只回答题型名称：
- 如果是图片选择题，回答：image
- 如果是词义选择题，回答：definition
- 如果是拼写题，回答：spelling  

只回答一个单词，不要其他内容。"""

            headers = {
                "Authorization": f"Bearer {self.api_config['key']}",
                "Content-Type": "application/json"
            }

            if self.api_type == "openrouter":
                headers["HTTP-Referer"] = "https://github.com/baicizhan-auto"
                headers["X-Title"] = "Baicizhan Auto"

            data = {
                "model": self.api_config['model'],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }

            response = requests.post(
                self.api_config['url'],
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content'].strip().lower()
                print(f"AI识别题型: {answer}")

                # 提取关键词
                if 'image' in answer:
                    return 'image'
                elif 'spell' in answer:
                    return 'spelling'
                elif 'defin' in answer:  # 匹配 'definition'
                    return 'definition'
                else:
                    return answer if answer in ['image', 'spelling', 'definition'] else 'unknown'
            else:
                print(f"题型识别失败 [{response.status_code}]")

        except Exception as e:
            print(f"✗ 题型检测失败: {e}")

        return 'unknown'

    def analyze_image_question(self, screenshot: Image.Image) -> int:
        """
        分析图片选择题 (Word/Sentence -> 4 Images)
        :param screenshot: 屏幕截图
        :return: 答案位置 1=左上, 2=右上, 3=左下, 4=右下
        """
        try:
            print("正在将截图发送给AI分析(图片题)...")
            img_base64 = self.image_to_base64(screenshot)

            prompt = """这是一个英语单词学习APP的截图。
            
界面说明：
- 顶部显示了一个英文单词，或者一个包含高亮英文单词的例句。
- 下方有4张图片选项，排列为2行2列（左上、右上、左下、右下）。

任务：请理解顶部的单词或例句中的高亮单词，并判断哪张图片最能代表这个单词的含义。

请只回答一个数字：
1 - 左上角的图片正确
2 - 右上角的图片正确
3 - 左下角的图片正确
4 - 右下角的图片正确

注意：只回答数字1、2、3或4，不要有任何其他文字。"""

            # 调用AI API
            headers = {
                "Authorization": f"Bearer {self.api_config['key']}",
                "Content-Type": "application/json"
            }

            # 根据不同API调整请求格式
            if self.api_type == "openrouter":
                headers["HTTP-Referer"] = "https://github.com/baicizhan-auto"
                headers["X-Title"] = "Baicizhan Auto"

            data = {
                "model": self.api_config['model'],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }

            response = requests.post(
                self.api_config['url'],
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                answer_text = result['choices'][0]['message']['content'].strip()
                print(f"AI回答: {answer_text}")

                # 提取数字
                numbers = re.findall(r'[1-4]', answer_text)
                if numbers:
                    answer = int(numbers[0])
                    print(f"✓ AI选择答案: {answer}")
                    return answer
            else:
                print(f"✗ API调用失败 [{response.status_code}]: {response.text}")

        except Exception as e:
            print(f"✗ AI(图片题)分析异常: {e}")

        # 失败时返回随机答案
        fallback = random.randint(1, 4)
        print(f"⚠ 使用随机答案: {fallback}")
        return fallback

    def analyze_definition_question(self, screenshot: Image.Image) -> int:
        """
        分析词义选择题 (Word -> 4 Definitions)
        :param screenshot: 屏幕截图
        :return: 答案位置 1=第一个, 2=第二个, 3=第三个, 4=第四个
        """
        try:
            print("正在将截图发送给AI分析(词义题)...")
            img_base64 = self.image_to_base64(screenshot)

            prompt = """这是一个英语单词学习APP的截图。

界面说明：
- 顶部显示了一个英文单词 (例如 "pot")。
- 下方有4个中文词义选项，垂直排列。

任务：请判断哪个中文选项是顶部英文单词的正确释义。

请只回答一个数字：
1 - 第1个中文选项正确
2 - 第2个中文选项正确
3 - 第3个中文选项正确
4 - 第4个中文选项正确

注意：只回答数字1、2、3或4，不要有任何其他文字。"""

            # 调用AI API
            headers = {
                "Authorization": f"Bearer {self.api_config['key']}",
                "Content-Type": "application/json"
            }

            if self.api_type == "openrouter":
                headers["HTTP-Referer"] = "https://github.com/baicizhan-auto"
                headers["X-Title"] = "Baicizhan Auto"

            data = {
                "model": self.api_config['model'],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }

            response = requests.post(
                self.api_config['url'],
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                answer_text = result['choices'][0]['message']['content'].strip()
                print(f"AI回答: {answer_text}")

                # 提取数字
                numbers = re.findall(r'[1-4]', answer_text)
                if numbers:
                    answer = int(numbers[0])
                    print(f"✓ AI选择答案: {answer}")
                    return answer
            else:
                print(f"✗ API调用失败 [{response.status_code}]: {response.text}")

        except Exception as e:
            print(f"✗ AI(词义题)分析异常: {e}")

        # 失败时返回随机答案
        fallback = random.randint(1, 4)
        print(f"⚠ 使用随机答案: {fallback}")
        return fallback

    def recognize_word(self, screenshot: Image.Image) -> str:
        """
        识别拼写题的单词
        :param screenshot: 屏幕截图
        :return: 识别出的单词
        """
        try:
            print("正在识别单词...")
            img_base64 = self.image_to_base64(screenshot)

            prompt = """这是一个英语单词学习APP的拼写测试截图。

界面说明：
- 顶部显示了一个英文单词
- 下方有该单词的中文释义和例句
- 需要识别顶部的英文单词

任务：请识别并返回顶部显示的英文单词。

注意：只回答英文单词本身，全部小写，不要有任何其他内容。"""

            headers = {
                "Authorization": f"Bearer {self.api_config['key']}",
                "Content-Type": "application/json"
            }

            if self.api_type == "openrouter":
                headers["HTTP-Referer"] = "https://github.com/baicizhan-auto"
                headers["X-Title"] = "Baicizhan Auto"

            data = {
                "model": self.api_config['model'],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 20
            }

            response = requests.post(
                self.api_config['url'],
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                word = result['choices'][0]['message']['content'].strip().lower()
                print(f"✓ AI识别单词: {word}")

                # 提取纯英文单词
                word_match = re.search(r'[a-z]+', word)
                if word_match:
                    return word_match.group()
                return word
            else:
                print(f"✗ 识别失败 [{response.status_code}]")

        except Exception as e:
            print(f"✗ 单词识别异常: {e}")

        return ""


class BaicizhanAuto:
    def __init__(self, device_ip: str = "127.0.0.1:7555", use_ai: bool = True, api_type: str = "deepseek"):
        """
        初始化自动化脚本
        :param device_ip: MuMu模拟器的ADB连接地址
        :param use_ai: 是否使用AI识别答案
        :param api_type: AI类型
        """
        print(f"正在连接设备: {device_ip}")
        self.d = u2.connect(device_ip)
        print(f"设备信息: {self.d.info}")
        self.package_name = "com.jiongji.andriod.card"

        # AI助手
        self.use_ai = use_ai
        if use_ai:
            print(f"✓ 启用AI识别模式: {api_type}")
            self.ai = AIHelper(api_type)
        else:
            print("✓ 使用随机答题模式")
            self.ai = None

    def random_sleep(self, min_sec: float = 1.0, max_sec: float = 2.0):
        """随机延迟，模拟人工操作"""
        time.sleep(random.uniform(min_sec, max_sec))

    def start_app(self):
        """启动百词斩应用"""
        print("\n▶ 启动百词斩...")
        self.d.app_start(self.package_name)
        self.random_sleep(3, 5) # (保留) 等待App加载

    def stop_app(self):
        """关闭百词斩应用"""
        print("\n■ 关闭百词斩...")
        self.d.app_stop(self.package_name)

    def click_by_text(self, text: str, timeout: int = 5) -> bool:
        """通过文本点击元素"""
        try:
            if self.d(text=text).wait(timeout=timeout):
                self.d(text=text).click()
                print(f"  → 点击: {text}")
                return True
        except Exception as e:
            print(f"  ✗ 点击失败 {text}: {e}")
        return False

    def click_by_coordinate(self, x: int, y: int):
        """通过坐标点击"""
        self.d.click(x, y)
        print(f"  → 点击坐标: ({x}, {y})")

    def take_screenshot(self) -> Optional[Image.Image]:
        """截取当前屏幕"""
        try:
            screenshot = self.d.screenshot(format='pillow')
            if screenshot:
                # 保存截图用于调试
                screenshot.save('last_question.png')
                print("  ✓ 截图成功")
                return screenshot
        except Exception as e:
            print(f"  ✗ 截图失败: {e}")
        return None

    def answer_spelling_question(self, screenshot: Image.Image):
        """
        处理拼写题 - 让AI识别单词并输入
        """
        try:
            # 检查传入的 screenshot
            if not screenshot:
                print("  ⚠ 截图失败，跳过此题")
                return

            # 让AI识别单词
            if self.use_ai and self.ai:
                word = self.ai.recognize_word(screenshot)
                print(f"  → AI识别的单词: {word}")
            else:
                print("  ⚠ 未启用AI，无法完成拼写题")
                return

            if word:
                # 点击输入框
                input_box = self.d(className="android.widget.EditText")
                if input_box.exists:
                    input_box.click()
                    self.random_sleep(0.2, 0.4) # (已优化) 等待键盘弹出

                    # 输入单词
                    input_box.set_text(word)
                    print(f"  ✓ 已输入: {word}")
                    self.random_sleep(0.1, 0.2) # (已优化)

                    # 确认/提交
                    self.d.press("enter")
                    self.random_sleep(0.5, 0.8) # (已优化) 等待结果页面
                else:
                    print("  ✗ 未找到输入框")

        except Exception as e:
            print(f"  ✗ 拼写题处理失败: {e}")

    def enter_study_mode(self):
        """进入学习模式"""
        print("\n▶ 尝试进入学习模式...")

        entry_texts = ["开始背单词吧", "继续背诵", "开始学习", "复习", "背单词"]

        for text in entry_texts:
            if self.click_by_text(text, timeout=3):
                self.random_sleep(2, 3) # (保留) 等待学习页面加载
                return True

        print("  → 尝试点击屏幕中心...")
        width, height = self.d.window_size()
        self.click_by_coordinate(width // 2, height // 2)
        self.random_sleep(2, 3) # (保留) 等待学习页面加载
        return True

    def answer_question(self):
        """
        回答问题 - (新版: 路由)
        让AI识别题型后处理
        """
        # 先截图
        screenshot = self.take_screenshot()
        if not screenshot:
            print("  ⚠ 截图失败，跳过此题")
            # 尝试点击屏幕继续
            width, height = self.d.window_size()
            self.click_by_coordinate(width // 2, height * 4 // 5)
            return

        # 让AI检测题型
        question_type = 'unknown'
        if self.use_ai and self.ai:
            question_type = self.ai.detect_question_type(screenshot)
        else:
            # 不用AI时，尝试简单检测
            if self.d(className="android.widget.EditText").exists:
                question_type = 'spelling'
            else:
                # 无法区分 image 和 definition，默认 image
                question_type = 'image'

        print(f"  ✓ 题型: {question_type}")

        # 根据题型处理
        if question_type == 'spelling':
            # 拼写题
            self.answer_spelling_question(screenshot)
        elif question_type == 'image':
            # 图片选择题
            self.answer_image_question_ai(screenshot)
        elif question_type == 'definition':
            # 词义选择题
            self.answer_definition_question_ai(screenshot)
        else:
            # 未知题型，默认按图片题处理
            print("  ⚠ 未知题型，尝试按图片题处理")
            self.answer_image_question_ai(screenshot)

    def answer_image_question_ai(self, screenshot: Image.Image):
        """
        回答图片选择题（2x2布局）
        """
        width, height = self.d.window_size()

        # 四个图片选项的位置 (2x2 布局)
        positions = {
            1: (319,1234),      # 左上
            2: (723,1232),  # 右上
            3: (304,1608),      # 左下
            4: (788,1582),  # 右下
        }

        answer_num = None

        if self.use_ai and self.ai:
            # 让AI分析图片题截图
            answer_num = self.ai.analyze_image_question(screenshot)
        else:
            # 随机选择
            answer_num = random.randint(1, 4)
            print(f"  → 随机选择: {answer_num}")

        # 点击答案
        if answer_num and answer_num in positions:
            answer_pos = positions[answer_num]
            self.click_by_coordinate(answer_pos[0], answer_pos[1])
            self.random_sleep(0.5, 0.8) # (已优化) 等待结果页面

    def answer_definition_question_ai(self, screenshot: Image.Image):
        """
        回答词义选择题（垂直布局）
        """
        width, height = self.d.window_size()

        # 四个词义选项的位置 (垂直布局) - (这些Y坐标是估计值，可能需要微调)
        positions = {
            1: (322,1072),      # 选项1 (约40%)
            2: (405,1254),    # 选项2 (约55%)
            3: (430,1482),     # 选项3 (约70%)
            4: (454,1679),    # 选项4 (约85%)
        }

        answer_num = None

        if self.use_ai and self.ai:
            # 让AI分析词义题截图
            answer_num = self.ai.analyze_definition_question(screenshot)
        else:
            # 随机选择
            answer_num = random.randint(1, 4)
            print(f"  → 随机选择: {answer_num}")

        # 点击答案
        if answer_num and answer_num in positions:
            # 修复：使用 answer_num 作为键来获取坐标
            answer_pos = positions[answer_num]
            self.click_by_coordinate(answer_pos[0], answer_pos[1])
            self.random_sleep(0.5, 0.8) # (已优化) 等待结果页面

    def continue_after_answer(self):
        """回答后继续下一题"""
        width, height = self.d.window_size()

        # 尝试点击 '斩' 或 '继续' 按钮 (无需等待超时，因为结果页通常会立刻出现按钮)
        if self.d(text="斩").exists:
            self.d(text="斩").click()
            print("  → 点击: 斩")
        elif self.d(text="继续做题").exists:
            self.d(text="继续做题").click()
            print("  → 点击: 继续做题")
        elif self.d(text="继续").exists:
            self.d(text="继续").click()
            print("  → 点击: 继续")
        else:
            # 备用：点击屏幕底部中心 (对应 540, 1824)
            self.click_by_coordinate(width // 2, height * 19 // 20)

        # 无论哪种方式，点击后等待下一题加载
        self.random_sleep(0.5, 0.8)
    
    def handle_popup(self):
        """处理可能出现的弹窗"""
        popup_texts = ["跳过", "关闭", "取消", "暂不", "以后再说", "我知道了", "继续做题"]

        for text in popup_texts:
            if self.d(text=text).exists:
                self.click_by_text(text, timeout=1)
                self.random_sleep(0.2, 0.4) # (已优化) 等待弹窗消失
                return True
        return False

    def complete_daily_task(self, word_count: int = 35):
        """完成每日学习任务"""
        print(f"\n{'='*60}")
        print(f"开始学习任务 - 目标: {word_count} 个单词")
        print(f"{'='*60}")

        # 增加循环次数，因为拼写题等可能需要多步
        max_loops = word_count * 3

        for i in range(max_loops):
            print(f"\n【第 {i + 1} 步】")

            # 检查弹窗
            self.handle_popup()

            # 回答问题 (新的路由方法)
            self.answer_question()

            # 继续下一题
            self.continue_after_answer()

            # 再次检查弹窗
            self.handle_popup()

            # 检查是否完成
            if (i + 1) % 5 == 0:
                print("\n  ⏳ 检查任务完成状态...")
                if self.d(textContains="完成").exists or \
                        self.d(textContains="恭喜").exists or \
                        self.d(textContains="已斩").exists or \
                        self.d(text="开始背单词吧").exists: # 回到主页也算完成
                    print("\n" + "="*60)
                    print("✓ 任务已完成！")
                    print("="*60)
                    break

            # 防止无限循环
            if i >= max_loops - 1:
                print("\n  ⚠ 已达到最大操作次数")
                break

    def run(self, word_count: int = 20):
        """运行完整流程"""
        try:
            self.start_app()
            self.enter_study_mode()
            self.complete_daily_task(word_count)
            self.random_sleep(1, 1.5) # (保留) 任务完成后的收尾延迟
            print("\n✓ 脚本执行完成！")
        except Exception as e:
            print(f"\n✗ 执行出错: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    print("="*60)
    print("         百词斩AI智能答题脚本 v2.3")
    print("         (修复了 answer_pos 引用问题)")
    print("="*60)

    # ===== 配置区域 =====
    # ⬇️ 请将此处的 YOUR_DEVICE_IP_HERE 替换为你设备的实际 IP 地址 (例如 "127.0.0.1:7555")
    device_ip = "YOUR_DEVICE_IP_HERE"  # MuMu模拟器地址或真机地址
    use_ai = True                      # 是否使用AI（True=AI识别，False=随机）
    api_type = "qwen"                  # AI类型: deepseek/qwen/siliconflow/openrouter
    word_count = 20                    # 每日单词数量

    # ⚠️ 重要：请将此处的 YOUR_API_KEY_HERE 替换为你申请到的真实 API Key
    custom_api_key = "YOUR_API_KEY_HERE"  # 替换为你的真实API Key
    # ===================

    # 检查API Key
    if custom_api_key == "YOUR_API_KEY_HERE":
        print("\n⚠️  错误：请先配置API Key！")
        print("\n获取API Key步骤：")
        print("1. DeepSeek: https://platform.deepseek.com/ (注册后在API Keys页面获取)")
        print("2. OpenRouter: https://openrouter.ai/keys (注册后直接创建)")
        print("3. SiliconFlow: https://siliconflow.cn/account/ak (注册后获取)")
        print("4. Qwen: https://dashscope.console.aliyun.com/apiKey (注册后获取)")
        print("\n获取后，修改脚本中的 custom_api_key = '你的Key'\n")
        return

    print(f"设备地址: {device_ip}")
    print(f"AI模式: {'启用 - ' + api_type if use_ai else '关闭（随机答题）'}")
    print(f"目标单词: {word_count} 个")
    # 隐藏部分API Key
    display_key = f"{custom_api_key[:4]}...{custom_api_key[-4:]}" if len(custom_api_key) > 8 else custom_api_key
    print(f"API Key: {display_key}")
    print("="*60)

    # 创建自动化实例并注入API Key
    bot = BaicizhanAuto(device_ip, use_ai=use_ai, api_type=api_type)
    if use_ai:
        # 确保所有配置中的 key 都被这个 custom_api_key 覆盖
        for key in bot.ai.api_config:
            if key == 'key':
                bot.ai.api_config['key'] = custom_api_key  # 使用自定义的API Key
                break

    # 运行任务
    bot.run(word_count=word_count)


if __name__ == "__main__":
    main()