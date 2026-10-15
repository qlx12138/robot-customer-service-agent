import streamlit as st
from agent.react_agent import ReactAgent


st.title("智扫通机器人智能客服")
st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "message" not in st.session_state:
    st.session_state["message"] = []

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

#用户输入提示词
prompt = st.chat_input()
if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role":"user", "content":prompt})

    reponse_messages = []
    with st.spinner("智能客服思考中..."):
        try:
            headers = st.context.headers
            client_ip = headers.get("X-Forwarded-For") or headers.get("X-Real-Ip")
        except (AttributeError, RuntimeError):
            client_ip = None

        res_stream = st.session_state["agent"].execute_stream(prompt, client_ip=client_ip)

        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                yield chunk

        st.chat_message("assistant").write_stream(capture(res_stream, reponse_messages))
        st.session_state["message"].append({"role":"assistant", "content":reponse_messages[-1]})
        st.rerun()
