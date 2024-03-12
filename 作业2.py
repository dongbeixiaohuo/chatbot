import os
import itertools
from typing import Iterator, Optional
from dotenv import load_dotenv
from datetime import datetime
import streamlit as st

# 通过.env文件设置环境变量
load_dotenv()

import api
from api import get_characterglm_response
from data_types import TextMsg, TextMsgList, filter_text_msg

st.set_page_config(page_title="CharacterGLM Chat Demo", page_icon="🤖", layout="wide")
debug = os.getenv("DEBUG", "").lower() in ("1", "yes", "y", "true", "t", "on")

def update_api_key(key: Optional[str] = None):
    if debug:
        print(f'update_api_key. st.session_state["API_KEY"] = {st.session_state["API_KEY"]}, key = {key}')
    key = key or st.session_state["API_KEY"]
    if key:
        api.API_KEY = key

# 设置API KEY
api_key = st.sidebar.text_input("API_KEY", value=os.getenv("API_KEY", ""), key="API_KEY", type="password", on_change=update_api_key)
update_api_key(api_key)

# 初始化
if "history" not in st.session_state:
    st.session_state["history"] = []
if "meta" not in st.session_state:
    st.session_state["meta"] = {
        "user_info": "",
        "bot_info": "",
        "bot_name": "",
        "user_name": ""
    }

def init_session():
    st.session_state["history"] = []

# 输入框，设置meta的4个字段
meta_labels = {
    "bot_name": "机器人1名",
    "user_name": "机器人2名", 
    "bot_info": "机器人1人设",
    "user_info": "机器人2人设"
}

# 2x2 layout
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(label="机器人1名", key="bot_name", on_change=lambda : st.session_state["meta"].update(bot_name=st.session_state["bot_name"]), help="机器人1的名字，不可以为空")
        st.text_area(label="机器人1人设", key="bot_info", on_change=lambda : st.session_state["meta"].update(bot_info=st.session_state["bot_info"]), help="机器人1的详细人设信息，不可以为空")
        
    with col2:
        st.text_input(label="机器人2名", value="机器人2", key="user_name", on_change=lambda : st.session_state["meta"].update(user_name=st.session_state["user_name"]), help="机器人2的名字，默认为机器人2")
        st.text_area(label="机器人2人设", value="", key="user_info", on_change=lambda : st.session_state["meta"].update(user_info=st.session_state["user_info"]), help="机器人2的详细人设信息，可以为空")

def verify_meta() -> bool:
    # 检查`机器人1名`和`机器人1人设`是否空，若为空，则弹出提醒
    if st.session_state["meta"]["bot_name"] == "" or st.session_state["meta"]["bot_info"] == "":
        st.error("机器人1名和机器人1人设不能为空")
        return False
    else:
        return True

# 在同一行排列按钮
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        clear_meta = st.button("清空人设", key="clear_meta")
        if clear_meta:
            st.session_state["meta"] = {
                "user_info": "",
                "bot_info": "",
                "bot_name": "",
                "user_name": ""
            }
            st.rerun()
    
    with col2:
        clear_history = st.button("清空对话历史", key="clear_history")
        if clear_history:
            init_session()
            st.rerun()
    
    with col3:
        n_rounds = st.number_input("设置聊天轮次", min_value=1, value=5, step=1, key="n_rounds")
        start_chat = st.button("开始聊天", key="start_chat")

# 展示对话历史
for msg in st.session_state["history"]:
    if msg["role"] == "user":
        with st.chat_message(name="user", avatar="user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.markdown(msg["content"])
    else:
        raise Exception("Invalid role")

def start_chatting():
    if not verify_meta():
        return
    if not api.API_KEY:
        st.error("未设置API_KEY")
        return

    current_role = "user"  # 初始发言者为机器人2
    for i in range(st.session_state["n_rounds"]):
        query = f"机器人{2 - int(current_role == 'user')}发言"  # 切换发言者
        st.session_state["history"].append(TextMsg({"role": current_role, "content": query}))

        response_stream = get_characterglm_response(filter_text_msg(st.session_state["history"]), meta=st.session_state["meta"])
        bot_response = "".join(response_stream)
        print(f"LLM Response: {bot_response}")  # 打印 LLM 输出
        if not bot_response:
            st.error("生成出错")
            st.session_state["history"].pop()
            return
        else:
            st.session_state["history"].append(TextMsg({"role": "assistant" if current_role == "user" else "user", "content": bot_response}))
            with st.chat_message(name=current_role, avatar=current_role):
                st.markdown(query)
            with st.chat_message(name="assistant" if current_role == "user" else "user", avatar="assistant" if current_role == "user" else "user"):
                st.markdown(bot_response)

        current_role = "assistant" if current_role == "user" else "user"  # 切换发言者
if start_chat:
    start_chatting()
def export_chat_history():
    """
    生成对话历史的字符串表示。
    """
    chat_history_str = ""
    for msg in st.session_state["history"]:
        role = msg["role"]
        content = msg["content"]
        chat_history_str += f"{role}: {content}\n"
    return chat_history_str

# 在适当的位置添加导出按钮
with st.sidebar:
    if st.button("导出对话历史"):
        chat_history = export_chat_history()
        if chat_history:
            # 生成当前时间戳，用于文件名
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"chat_history_{timestamp}.txt"
            
            # 使用st.download_button提供下载链接
            st.download_button(
                label="下载对话历史",
                data=chat_history,
                file_name=filename,
                mime="text/plain"
            )
        else:
            st.warning("没有对话历史可导出。")