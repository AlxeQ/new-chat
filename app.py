import streamlit as st
import textwrap
import os
import requests

# --- 页面设置 ---
st.set_page_config(page_title="访谈内容结构化分析工具", layout="wide")
st.markdown("""
<style>
    body {
        background-color: #f0f4fa;
        color: #1a2c4e;
    }
    .stButton>button {
        background-color: #0066cc;
        color: white;
        border-radius: 5px;
        padding: 0.5em 1em;
    }
    .stTextArea textarea {
        background-color: #f7faff;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔵 访谈内容结构化分析工具")

# --- DeepSeek API Key 设置 ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# --- 文件上传区 ---
st.markdown("### 1️⃣ 上传访谈大纲与访谈原始内容（支持 PDF、Word、TXT）")
outline_file = st.file_uploader("上传访谈大纲文件", type=["pdf", "docx", "txt"])
content_file = st.file_uploader("上传访谈原始内容文件", type=["pdf", "docx", "txt"])

from io import StringIO
from PyPDF2 import PdfReader
import docx

def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""
    if uploaded_file.type == "application/pdf":
        pdf = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.type == "text/plain":
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        return stringio.read()
    return ""

outline_input = extract_text_from_file(outline_file)
interview_text = extract_text_from_file(content_file)

if st.button("🚀 开始分析"):
    if not outline_input.strip() or not interview_text.strip():
        st.warning("请确保已上传大纲和访谈内容文件。")
        st.stop()

    # --- 构建提示词 ---
    full_prompt = f"""
你是一个具备深度洞察力的「访谈分析专家」，熟悉新媒体营销、业务增长、组织管理等多个相关领域。
你的任务是对访谈内容进行结构化解析、深入提炼并提出可操作的延伸建议。你的目标不只是整理内容，而是帮助团队洞察规律、发现盲点、形成可复用的方法论。

---

【任务一｜逐条对照访谈大纲】
请根据下方访谈大纲，逐一检查受访者是否进行了明确回应：
- 若有回应，请详细提取相关内容，保留受访者典型表述、关键细节、实际数据。
- 若为“部分覆盖”或“未覆盖”，请提出**精准、延展性强的补问建议**，可用于后续追问或复采。

---

【任务二｜案例与线索提取】
请识别访谈中所有包含“时间 + 人物 + 行动 + 结果”的完整案例，纳入“案例补充”类；若有数据、因果、判断、方法等信息，请归为“数据线索”类。
- 案例要突出具体行为与转化结果
- 数据要反映因果逻辑或策略效果

---

【任务三｜故事模块提炼】
请在访谈中识别具代表性或启发意义的故事内容，具备以下特征之一即可提取：
- 能反映行业常见问题的应对方式；
- 体现受访者的独特经验与判断，具有迁移价值；
- 展现明显变化轨迹或转折点，有情节性。

请按以下结构输出故事表格，如内容缺失，可留空并补充建议：

### 故事编号：S01
| 要素 | 内容 |
|------|------|
| 故事名称 | 由你根据内容总结 |
| 时间点 |  |
| 角色 |  |
| 动机/初衷 |  |
| 面临的问题/挑战 |  |
| 行动过程 |  |
| 转折点 |  |
| 最终结果 |  |
| 启发意义 |  |
| 建议补问 | 用于补足空缺要素 |

---

【任务四｜结构化输出表格】
请输出以下 Markdown 表格：

| 类型 | 问题或主题 | 内容摘要 | 原始话术 | 覆盖情况 | 补问建议 |
|------|------------|----------|-----------|-----------|-----------|
- 类型：大纲对应 / 案例补充 / 数据线索（三选一）
- 内容摘要：不少于150字，尽量详实，还原受访者逻辑、现象与判断
- 原始话术：提取具代表性的原句（可略微润色但不改原意）
- 覆盖情况：是 / 否 / 部分覆盖
- 补问建议：若为“否”或“部分覆盖”，必须给出具体问题，**鼓励提出延伸性深度追问**

---

访谈大纲如下：
{outline_input}

访谈内容如下：
{interview_text}
"""

    with st.spinner("正在分析中，请稍候..."):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的访谈结构化分析助手。"},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.5
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            st.success("✅ 分析完成！")
            st.markdown(content)
        else:
            st.error("❌ 分析失败，请检查API配置或稍后重试。")

st.markdown("---")
st.markdown("💡 提示：如需导出结果，可直接复制 Markdown 表格或使用截图保存。")
