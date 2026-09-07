import os
import io
import base64

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
app = Flask(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "XLabs-AI/flux-RealismLora"

if not HF_TOKEN:
    raise RuntimeError("未检测到 HF_TOKEN，请复制 .env.example 为 .env 并填入 Hugging Face Token。")

client = InferenceClient(provider="fal-ai", api_key=HF_TOKEN)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json(silent=True) or {}

        prompt = str(data.get("prompt", "")).strip()
        width = int(data.get("width", 768))
        height = int(data.get("height", 768))
        quality = int(data.get("quality", 28))

        if not prompt:
            return jsonify({"success": False, "message": "请输入 Prompt"}), 400

        # 基本范围校验
        width = max(512, min(1024, width))
        height = max(512, min(1024, height))
        quality = max(10, min(50, quality))

        print("=" * 60)
        print("开始调用 Hugging Face API")
        print("模型：", MODEL_ID)
        print("Prompt：", prompt)
        print(f"尺寸：{width} x {height}")
        print("推理步数：", quality)

        image = client.text_to_image(
            prompt=prompt,
            model=MODEL_ID,
            width=width,
            height=height,
            num_inference_steps=quality,
            guidance_scale=3.5
        )

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

        print("API 调用成功")
        print("图片尺寸：", image.size)
        print("=" * 60)

        return jsonify({
            "success": True,
            "image": f"data:image/png;base64,{encoded}"
        })

    except Exception as exc:
        print("API 调用失败：", str(exc))
        return jsonify({"success": False, "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
