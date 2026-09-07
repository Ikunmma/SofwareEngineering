1. # FLUX Realism Web

   本项目使用 Hugging Face 提供的模型推理服务，调用 `XLabs-AI/flux-RealismLora` 模型生成写实图像，并在 API 调用的基础上结合 Flask、HTML、CSS 和 JavaScript，实现了一个简单的交互式 AI 图像生成网页。

   用户可以在网页中输入 Prompt，并调整图片宽度、高度和生成清晰度。模型生成完成后，图片会直接显示在网页右侧，同时支持将生成结果下载到本地。

   ## 1. 项目功能

   本项目主要实现以下功能：

   - 调用 Hugging Face 上的 FLUX Realism 模型生成图片
   - 通过 Web 页面输入和修改 Prompt
   - 自定义生成图片的宽度和高度
   - 调节模型生成图片时的推理步数
   - 在网页中实时显示生成结果
   - 下载生成的 PNG 图片
   - 在后端终端输出 API 调用记录

   ### Web 交互界面

   项目运行后的前端页面如下：

   ![web-interface](https://raw.githubusercontent.com/Ikunmma/picture-picgo/main/20260907180118609.png)

   ## 2. 项目结构

   ```
   flux-realism-web/
   │
   ├── app.py
   ├── requirements.txt
   ├── .env.example
   ├── .gitignore
   ├── README.md
   │
   ├── images/
   │   ├── web-interface.png
   │   ├── api-success.png
   │   ├── prompt-v1.png
   │   ├── prompt-v2.png
   │   └── prompt-v3.png
   │
   └── templates/
       └── index.html
   ```

   其中：

   - `app.py`：Flask 后端程序，负责接收前端请求以及调用 Hugging Face API。
   - `templates/index.html`：前端页面，实现 Prompt 输入、参数调节、图片预览和下载。
   - `images/`：存放实验过程和 README 使用的截图。
   - `.env.example`：Hugging Face Token 配置示例。
   - `.gitignore`：避免 Token、虚拟环境等文件上传至 GitHub。
   - `requirements.txt`：项目运行需要安装的 Python 依赖。

   ## 3. Hugging Face API 配置

   首先在 Hugging Face 官网注册并登录个人账号，然后进入个人设置中的 **Access Tokens** 页面创建用于调用模型的 Token。

   本项目使用的模型为：

   ```
   XLabs-AI/flux-RealismLora
   ```

   为了避免 Token 泄漏，没有将真实 Token 直接写入 Python 或 JavaScript 代码，而是通过环境变量进行读取。

   将项目中的：

   ```
   .env.example
   ```

   复制并重命名为：

   ```
   .env
   ```

   然后填写自己的 Hugging Face Token：

   ```
   HF_TOKEN=hf_你的HuggingFaceToken
   ```

   `.env` 已经加入 `.gitignore`，因此不会随项目代码一起提交到 GitHub。

   ## 4. 项目运行

   ### 4.1 创建虚拟环境

   ```
   python -m venv venv
   ```

   Windows：

   ```
   venv\Scripts\activate
   ```

   macOS / Linux：

   ```
   source venv/bin/activate
   ```

   ### 4.2 安装依赖

   ```
   pip install -r requirements.txt
   ```

   ### 4.3 启动 Flask

   ```
   python app.py
   ```

   运行成功后访问：

   ```
   http://127.0.0.1:5000
   ```

   即可进入图像生成页面。

   ## 5. API 调用与前端交互

   本项目没有直接在前端调用 Hugging Face API，而是通过 Flask 后端完成模型请求。

   前端通过 JavaScript 获取用户输入的 Prompt、图片宽度、图片高度以及清晰度参数，然后使用 Fetch 向 Flask 的 `/generate` 接口发送 POST 请求。

   Flask 接收到请求后，通过 Hugging Face `InferenceClient` 调用模型。模型返回图片后，后端将图片转换为 Base64 数据返回给浏览器，并最终显示在网页右侧。

   为了方便观察模型调用过程，我在后端加入了运行日志。调用成功后终端会显示：

   ![image-20260907174726067](https://raw.githubusercontent.com/Ikunmma/picture-picgo/main/20260907180140252.png)

   ## 6. Prompt 设计与修改过程

   为了比较不同 Prompt 对生成效果的影响，我选择橘猫作为主要生成对象，并通过三次 Prompt 修改逐渐增加环境、主体细节以及摄影特征。

   ### 6.1 第一版：确定基本内容

   最开始只描述需要生成的主体以及基本场景：

   ```
   A realistic photo of an orange tabby cat sitting on a street.
   ```

   这一版本的主要目的是确定图片中的基本内容，因此 Prompt 只包含橘猫、街道以及真实照片三个主要信息。

   模型能够正确生成橘猫和街道，但是由于缺少对光照、环境以及猫的外观细节描述，生成结果中的场景比较普通，整体真实感仍有提升空间。

   **第一版生成结果：**

   ![1](https://raw.githubusercontent.com/Ikunmma/picture-picgo/main/20260907174901114.png)

   ### 6.2 第二版：增加环境和主体细节

   第二次生成时，在原 Prompt 的基础上加入雨后环境、自然光以及毛发细节：

   ```
   A realistic photo of an orange tabby cat sitting on a wet street after rain, natural light, detailed fur, photorealistic.
   ```

   这一版本主要增加：

   ```
   wet street after rain
   natural light
   detailed fur
   photorealistic
   ```

   其中，雨后的街道可以增加地面水迹、反光等现实环境细节；自然光可以减少过于明显的人工布光效果；`detailed fur` 则用于提高猫毛发部分的细节表现。

   与第一版相比，第二版生成结果中的环境更加完整，猫的毛发也更加清晰，整体开始具有真实摄影的效果。

   **第二版生成结果：**

   ![2](https://raw.githubusercontent.com/Ikunmma/picture-picgo/main/20260907174917566.png)

   ### 6.3 第三版：增强真实摄影感

   最后一次修改主要针对图片中可能出现的“AI 感”进行优化。

   最终 Prompt 为：

   ```
   A candid photo of an orange tabby cat sitting on a wet street after rain, natural daylight, detailed slightly messy fur, realistic eyes and whiskers, natural pose, shallow depth of field, photorealistic.
   ```

   相比第二版，进一步增加：

   ```
   candid photo
   slightly messy fur
   realistic eyes and whiskers
   natural pose
   shallow depth of field
   ```

   其中 `slightly messy fur` 用于避免猫的毛发过于整齐；`natural pose` 强调动物自然状态而不是刻意摆拍；`realistic eyes and whiskers` 加强眼睛和胡须等容易影响真实感的细节；`shallow depth of field` 则模拟真实摄影中的景深效果，使主体与背景之间形成更加自然的层次。

   相比单纯加入 `8K`、`masterpiece` 等强调画质的关键词，这种方法更加注重现实摄影本身具有的特征。

   **最终生成结果：**

   ![3](https://raw.githubusercontent.com/Ikunmma/picture-picgo/main/20260907174938220.png)

   通过三次 Prompt 调整可以发现，提示词不仅需要告诉模型“生成什么”，还需要进一步描述主体所处的环境、光照以及希望呈现的细节。尤其是在生成写实图片时，相比单纯堆叠表示高画质的关键词，加入现实世界中的自然状态、环境细节和摄影特征，更有助于让最终生成结果接近真实照片。

   ## 7. 实验体验与心得

   通过本次实验，我完成了从 Hugging Face 模型选择、API Token 配置、模型调用，到 Flask 后端和前端页面交互的完整过程。

   在实际操作过程中，我发现模型 API 本身的调用代码并不复杂，但要真正将模型集成到一个可以使用的 Web 应用中，还需要考虑前后端数据传递、API Token 安全以及异常处理等问题。例如，一开始可以直接在 JavaScript 中调用 API，但这样容易导致 Token 暴露，因此最终选择通过 Flask 后端统一处理 Hugging Face API 请求。

   Prompt 的设计也是本次实验中比较明显的一点。最开始使用简单 Prompt 时，模型虽然能够生成正确的主体，但对图片细节的控制比较有限。随着自然光、环境、毛发、眼睛、姿态以及景深等描述逐渐加入，生成结果也更加符合预期。

   这次实验让我认识到，使用生成式 AI 不仅仅是简单地调用一个模型。如何准确描述需求、根据生成结果不断调整 Prompt，以及如何将模型能力集成到实际程序中，同样是生成式 AI 应用开发中非常重要的部分。

   ## 8. 技术栈

   - Python
   - Flask
   - Hugging Face Inference API
   - FLUX Realism LoRA
   - HTML
   - CSS
   - JavaScript

   ## 9. 注意事项

   1. Hugging Face Token 不应直接写入前端代码。
   2. `.env` 文件不要上传至 GitHub。
   3. 图片尺寸和推理步数越高，生成所需要的时间通常也会增加。
   4. 不同 Prompt 会明显影响最终生成结果，因此可以通过多次调整 Prompt 获得更加符合要求的图片。
