import streamlit as st
import bs4
from langchain_community.document_loaders import WebBaseLoader
from fake_useragent import UserAgent
import re
import google.generativeai as genai

# 커스텀 CSS 추가
st.markdown("""
<style>
    /* 기존 CSS 스타일들은 그대로 두고... */

    /* 새로운 입력창을 위한 스타일 추가 */
    .input-group {
        position: relative;
        width: 100%;
        margin: 20px 0;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    #url-input {
        width: 100%;
        padding: 12px 40px 12px 15px;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        font-size: 16px;
        outline: none;
        transition: border-color 0.2s;
    }

    .submit-btn {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: #4a5568;
        cursor: pointer;
        font-size: 20px;
        padding: 5px;
        transition: color 0.2s;
    }
</style>

<!-- 2. HTML 입력창 추가 -->
<div class="input-group">
    <input type="text" id="url-input" placeholder="URL을 입력하세요" />
    <button class="submit-btn">→</button>
</div>

<!-- 3. JavaScript 코드 추가 -->
<script>
    // 페이지가 로드되면 실행될 코드
    window.addEventListener('DOMContentLoaded', function() {
        // 입력창과 버튼 요소 가져오기
        const urlInput = document.getElementById('url-input');
        const submitBtn = document.querySelector('.submit-btn');
        
        // URL을 Streamlit으로 전송하는 함수
        function handleSubmit() {
            const url = urlInput.value;
            window.parent.postMessage({
                type: 'streamlit:set_component_value',
                key: 'hidden_url_input',
                value: url
            }, '*');
        }
        
        // 버튼 클릭 시 실행
        submitBtn.addEventListener('click', handleSubmit);
        
        // Enter 키 입력 시 실행
        urlInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleSubmit();
            }
        });
    });
</script>
""", unsafe_allow_html=True)

# 4. Streamlit 히든 입력창 추가
if 'url_state' not in st.session_state:
    st.session_state.url_state = ''

url = st.text_input("", 
                    key="hidden_url_input", 
                    label_visibility="collapsed",
                    value=st.session_state.url_state)

# 5. URL이 입력되었을 때의 처리
if url != st.session_state.url_state:
    st.session_state.url_state = url
    st.experimental_rerun()

# 요약 스타일 선택 (기존 코드)
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

# URL 처리 부분 (기존 코드)
if url:
    try:
        with st.spinner('웹 페이지를 분석 중입니다...'):
            # 기존 처리 로직...
            pass
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
