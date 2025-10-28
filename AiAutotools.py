
import uiautomator2 as u2
import time
import random
import base64
import requests
from io import BytesIO
from PIL import Image
import re


class AIHelper:
    """负责AI图像识别、答案判断"""

    def __init__(self, api_type="qwen", api_key="YOUR_API_KEY"):
        self.api_type = api_type
        self.api_key = api_key
        self.api_config = self._get_api_config()

    def _get_api_config(self):
        configs = {
            "deepseek": {
                "url": "https://api.deepseek.com/chat/completions",
                "model": "deepseek-chat"
            },
            "qwen": {
                "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                "model": "qwen3-vl-flash"
            },
            "siliconflow": {
                "url": "https://api.siliconflow.cn/v1/chat/completions",
                "model": "Qwen/Qwen2-VL-7B-Instruct"
            },
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "model": "google/gemini-2.0-flash-exp:free"
            }
        }
        return configs[self.api_type]

    def image_to_base64(self, image: Image.Image) -> str:
        buffered = BytesIO()
        image = image.resize((image.width // 2, image.height // 2), Image.Resampling.LANCZOS)
        image.save(buffered, format="PNG", optimize=True)
        return base64.b64encode(buffered.getvalue()).decode()

    def analyze_choice_question(self, screenshot: Image.Image) -> int:
        """通用AI识别（图片 or 词义题）"""
        print("🧠 正在让AI判断正确选项...")
        try:
            img_base64 = self.image_to_base64(screenshot)
            prompt = """这是百词斩的题目截图。
上方显示一个单词或短句，下方有四个选项（可能是图片，也可能是中文释义）。
请根据题意判断正确答案是哪一个：
从上到下为 1 到 4。
只返回纯数字 1~4。"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.api_config["model"],
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                    ]}
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }

            resp = requests.post(self.api_config["url"], headers=headers, json=data, timeout=25)
            if resp.status_code == 200:
                result = resp.json()
                answer_text = result['choices'][0]['message']['content'].strip()
                nums = re.findall(r"[1-4]", answer_text)
                if nums:
                    ans = int(nums[0])
                    print(f"✅ AI 判断答案：{ans}")
                    return ans
            else:
                print(f"❌ API请求失败: {resp.status_code}")
        except Exception as e:
            print(f"⚠ AI识别出错: {e}")
        ans = random.randint(1, 4)
        print(f"⚠ 回退随机答案: {ans}")
        return ans

    def recognize_word(self, screenshot: Image.Image) -> str:
        """识别拼写题单词"""
        print("🔤 正在识别拼写单词...")
        try:
            img_base64 = self.image_to_base64(screenshot)
            prompt = "请识别图片中显示的英文单词，只返回单词本身（小写）。"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            data = {
                "model": self.api_config["model"],
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                    ]}
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }
            resp = requests.post(self.api_config["url"], headers=headers, json=data, timeout=25)
            if resp.status_code == 200:
                word = resp.json()["choices"][0]["message"]["content"].strip().lower()
                m = re.search(r"[a-z]+", word)
                if m:
                    print(f"✅ AI识别单词: {m.group()}")
                    return m.group()
        except Exception as e:
            print(f"拼写识别异常: {e}")
        return ""


class BaicizhanAuto:
    def __init__(self, device_ip="127.0.0.1:7555", api_type="qwen", api_key="YOUR_API_KEY"):
        print("📱 正在连接设备:"+device_ip)
        self.d = u2.connect(device_ip)
        self.ai = AIHelper(api_type, api_key)
        print("✅ 设备连接成功")
    def enter_study_page(self):
        print("🚀 正在启动百词斩 App...")
        try:
            self.d.app_start("com.jiongji.andriod.card")
            time.sleep(5)
            if self.d(text="学习").exists:
                self.d(text="学习").click()
                print("✅ 已点击学习按钮")
            else:
                self.d.click(540, 1780)
                print("⚠ 未识别文字按钮，使用坐标点击")
            time.sleep(3)
        except Exception as e:
            print(f"❌ 启动百词斩失败:{e}")
    def take_screenshot(self):
        try:
            img = self.d.screenshot(format='pillow')
            img.save("last_question.png")
            return img
        except Exception as e:
            print(f"截图失败: {e}")
            return None

    def click_by_coordinate(self, x, y):
        self.d.click(x, y)
        print(f"👉 点击坐标 ({x},{y})")

    def answer_choice_question(self, screenshot: Image.Image):
        ans = self.ai.analyze_choice_question(screenshot)
        w, h = self.d.window_size()
        pos = {
            1: (522,875),
            2: (534,1124),
            3: (528,1375),
            4: (528,1610)
        }
        if ans in pos:
            self.click_by_coordinate(*map(int, pos[ans]))

    def answer_spelling_question(self, screenshot: Image.Image):
        word = self.ai.recognize_word(screenshot)
        if word and self.d(className="android.widget.EditText").exists:
            edit = self.d(className="android.widget.EditText")
            edit.set_text(word)
            print(f"✍ 输入: {word}")
            self.d.press("enter")


    def run_forever(self):

        print("🚀 开始自动刷题（按 Ctrl+C 停止）")
        while True:
            try:
                screenshot = self.take_screenshot()
                if not screenshot:
                    continue

                if self.d(className="android.widget.EditText").exists:
                    self.answer_spelling_question(screenshot)
                else:
                    self.answer_choice_question(screenshot)

                time.sleep(1.5)
                self.d.click(722,1829)
                time.sleep(1.5)
            except KeyboardInterrupt:
                print("⏹ 手动停止")
                break
            except Exception as e:
                print(f"⚠ 循环异常: {e}")
                time.sleep(2)
                continue


if __name__ == "__main__":
    bot = BaicizhanAuto(device_ip="127.0.0.1:7555",api_type="qwen", api_key="sk-xxxxxxxxxxxxxxxxxxx")
    bot.enter_study_page()
    bot.run_forever()
