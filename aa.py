import streamlit as st
import bs4
from langchain_community.document_loaders import WebBaseLoader
from fake_useragent import UserAgent
import re
import google.generativeai as genai

# 커스텀 CSS 추가
st.markdown("""
<style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
        padding: 3rem 2rem;
        background-color: #f8f9fc;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    .main-title {
        color: #2c3e50;
        font-size: 2.25rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 1.5rem;
        border-bottom: 3px solid #e2e8f0;
        letter-spacing: -0.025em;
    }
    /* 입력 컨테이너 스타일 */
    .input-container {
        position: relative;
        width: 100%;
        margin-bottom: 1rem;
    }
    /* text_input 영역에 패딩을 넉넉히 주어 오른쪽 공간 확보 */
    div[data-testid="stTextInput"] > div {
        padding-right: 3rem;
    }
    /* 버튼을 입력창 오른쪽 안쪽에 겹치도록 위치시킴 */
    .input-container > div.stButton {
        position: absolute;
        right: 1rem;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        box-shadow: none;
    }
    .input-container > div.stButton > button {
        background: none;
        border: none;
        font-size: 1.5rem;
        color: #475569;
        padding: 0;
        cursor: pointer;
    }
    .input-container > div.stButton > button:hover {
        color: #334155;
    }
    
    .results-container {
        background-color: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.1);
        margin-top: 2rem;
        border: 1px solid #e2e8f0;
    }
    .results-container h3 {
        color: #334155;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
        letter-spacing: -0.025em;
    }
    .results-container p {
        color: #475569;
        font-size: 1.1rem;
        line-height: 1.8;
        margin: 0;
        white-space: pre-line;
    }
    .stSpinner {
        text-align: center;
        color: #64748b;
    }
    .stError {
        background-color: #fef2f2;
        color: #991b1b;
        padding: 1rem;
        border-radius: 0.75rem;
        border: 1px solid #fee2e2;
        margin-top: 1rem;
        font-weight: 500;
    }
    .stMarkdown {
        color: #334155;
    }
    .stButton button {
        background-color: #475569;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">웹페이지 요약 by 제임스</h1>', unsafe_allow_html=True)

API_KEY = st.secrets["GEMINI_API_KEY"]

# 입력창과 버튼을 같은 컨테이너 안에 넣고 버튼을 겹치기
container = st.container()
with container:
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    url = st.text_input("URL을 입력하세요:", placeholder="https://example.com", key="url_input")
    arrow_clicked = st.button("➜", help="URL 요약 실행")
    st.markdown('</div>', unsafe_allow_html=True)

summary_style = st.selectbox(
    "요약 스타일을 선택하세요:",
    [
        "일반 요약",
        "세줄 요약",
        "TLDR 한 줄 요약",
        "5가지 핵심 키워드",
        "Q&A 형식"
    ]
)

if (arrow_clicked or (url and st.session_state.get("url_input"))) and st.session_state["url_input"].strip():
    try:
        with st.spinner('웹 페이지를 분석 중입니다...'):
            use_url = st.session_state["url_input"].strip()
            loader = WebBaseLoader(use_url, header_template={'User-Agent': UserAgent().chrome})
            docs = loader.load()
            raw_page_content = docs[0].page_content
            cleaned_text = re.sub(r'\n+', '\n', raw_page_content)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            cleaned_text = cleaned_text.strip()

            model_name = "gemini-1.5-pro"
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 0
            }
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]

            base_instruction = """
            기본 규칙:
            1. 모든 답변에는 마크다운 형식 적용
            2. 모든 답변은 자연스러운 한국어로 제공할 것
            3. 전문용어가 있다면 쉽게 풀어서 설명할 것
            4. 문장은 간결하고 명확하게 작성할 것
            5. 존댓말을 사용할 것
            """

            system_instructions = {
                "일반 요약": """
                다음 내용을 먼저 일반적인 텍스트로 간단히 요약하고, 불렛 포인트를 활용하여 가독성을 높여주세요.
                """,
                "세줄 요약": """
                다음 내용을 3개의 핵심 포인트로 요약해주세요.
                규칙:
                1. 각 포인트 사이에는 한 줄의 공백을 줄 것
                2. 각 줄 앞에는 관련된 이모지를 넣을 것
                3. 문장은 '~입니다', '~했습니다'로 끝낼 것
                4. 가장 중요한 내용만 간단명료하게 작성할 것
                """,
                "TLDR 한 줄 요약": """
                다음 내용의 핵심을 단 한 문장으로 요약해주세요.
                규칙:
                1. 30단어 이내로 작성할 것
                3. 가장 중요한 핵심 메시지만 포함할 것
                """,
                "5가지 핵심 키워드": """
                다음 내용에서 가장 중요한 5개의 키워드를 추출하고 설명해주세요.
                형식:
                1. [키워드1]: 설명
                2. [키워드2]: 설명
                3. [키워드3]: 설명
                4. [키워드4]: 설명
                5. [키워드5]: 설명
                """,
                "Q&A 형식": """
                다음 내용을 Q&A 형식으로 정리해주세요.
                규칙:
                1. 가장 중요한 3가지 질문을 선정할 것
                2. 각 질문은 'Q: '로 시작
                3. 각 답변은 'A: '로 시작
                4. 답변은 명확하고 구체적으로 작성
                5. 질문과 답변 사이는 한 줄 띄울 것
                6. 답변과 그 다음 질문 사이도 한 줄 띄울 것
                """
            }

            system_instruction = system_instructions[summary_style]

            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            prompt = f"""
            역할: 당신은 전문적인 콘텐츠 요약 도우미입니다.
            
            {base_instruction}
            
            구체적 지시사항: {system_instruction}
            
            내용:
            {cleaned_text}
            """

            response = model.generate_content(prompt)

            st.markdown(f"""
            <div class="results-container">
                <h3>요약 결과</h3>
                <p>{response.text}</p>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
