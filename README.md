# 1. Information about Acrome Education Kit Controlling with AI.


This guide explains how to obtain and configure API keys for **Groq Cloud** and **Hugging Face**, which are necessary for running the application.

---

## 🚀 Quick Start

Follow the steps below to set up API keys for both platforms:

1. **Groq Cloud**: Create and save your API key.
2. **Hugging Face**: Generate a personal access token.
3. **Important**: Store your keys securely in `.txt` files.

---

## 🧑‍💻 1. Setting Up Groq Cloud API Key

1. **Visit the Groq Cloud Playground**: [https://console.groq.com/playground](https://console.groq.com/playground).
2. Navigate to **"API Keys"**:
   - If you are **not logged in**, you will see a login screen. Log in using **GitHub**, **Google**, or by creating a regular account.

     ![Groq Cloud Login Screen](#)

3. Once logged in:
   - Click on **"Create API Key"**.
   - Provide a **name** for your API key.
   - Click **Generate** to create the key.

4. **Important:**
   - Save the API key securely, as it will only be displayed **once**.
   - The application reads API keys from a `.txt` file. If the key file is lost or deleted, you will need to generate a new key.

---

## 🤖 2. Setting Up Hugging Face API Key

1. **Go to Hugging Face**: [https://huggingface.co/](https://huggingface.co/).
2. Log in to your account:
   - If you don’t have an account, click **Sign Up** to register.
3. After logging in:
   - Click on your profile picture (top-right corner).
   - From the dropdown menu, select **"Access Tokens"**.


4. Click **"Create New Token"**:
   - Select the token type: **Read**, **Write**, or **Fine-grained**.
   - Choose **Read** for this application.
   - Provide a name for your token and click **Create Token**.

5. **Save your token securely**:
   - The token will be displayed only **once**.
   - You will need this token to integrate Hugging Face into your application.

     

---

## 📂 File Management

- Store both API keys in `.txt` files, as the application reads them from these files.

## Convert .py to .exe 
- Firstly, you should download repo.
- Secondly, you should change AcromeChatbotandController.py file to AcromeChatbotandController.pyw
- Thirdly, you should use pip install -r requirements.txt
- Fourtly, open the terminal and **pyinstaller --onefile --windowed --hidden-import="chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2" --hidden-import="onnxruntime" --hidden-import="tokenizers" --hidden-import="tqdm" --hidden-import="chromadb.telemetry.product.posthog" --hidden-import="chromadb.api.segment" --hidden-import="chromadb.db.impl" --hidden-import="chromadb.db.impl.sqlite" --hidden-import="chromadb.migrations" --hidden-import="chromadb.migrations.embeddings_queue" --hidden-import="chromadb.segment.impl.manager" --hidden-import="chromadb.segment.impl.manager.local" --hidden-import="chromadb.execution.executor.local" --hidden-import="chromadb.quota.simple_quota_enforcer" --hidden-import="chromadb.rate_limit.simple_rate_limit" --hidden-import="chromadb.segment.impl.metadata" --hidden-import="chromadb.segment.impl.metadata.sqlite" --collect-all=chromadb --console --icon=ac.ico AcromeChatbotandController.pyw** 
**(note:This command must be on a single line. )**

## Importance:
- **After making the exe, put the data folder in the location where the exe was installed.**
- If you want more information, you can read AcromeEduControl.

# 2. Information about Acrome Smart Motion Device Controlling with AI.
---

## 🚀 Quick Start

Follow the steps below to set up API keys for both platforms:

1. **Groq Cloud**: Create and save your API key.
3. **Important**: Store your keys securely in `.txt` files.

---
## 🧑‍💻 1. Setting Up Groq Cloud API Key

1. **Visit the Groq Cloud Playground**: [https://console.groq.com/playground](https://console.groq.com/playground).
2. Navigate to **"API Keys"**:
   - If you are **not logged in**, you will see a login screen. Log in using **GitHub**, **Google**, or by creating a regular account.

     ![Groq Cloud Login Screen](#)

3. Once logged in:
   - Click on **"Create API Key"**.
   - Provide a **name** for your API key.
   - Click **Generate** to create the key.

4. **Important:**
   - Save the API key securely, as it will only be displayed **once**.
   - The application reads API keys from a `.txt` file. If the key file is lost or deleted, you will need to generate a new key.

---
## 📂 File Management

- Store  API key in `.txt` files, as the application reads them from these files.

## Convert .py to .exe 
- Firstly, you should download repo.
- Secondly, you should use pip install -r requirements.txt
- Thirdly, open the terminal and **pyinstaller robot-control-groq-car.py --onefile --icon=ac.ico --noconsole** 
**(note:This command must be on a single line. )**
-You also have to send the robot_car.py file to the raspberry pi. Also install the requirements.txt file both on your pc and on the raspberry pi (I mean the libraries inside.) (pip install -r requirements.txt)



- If you want to learn application, you can read  AcromeSmartMotionDevice Controlling With Ai.
