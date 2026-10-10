from langchain.agents import create_agent
from utils.prompt_loader import load_system_prompts
from model.factory import chat_model
from agent.tools.agent_tools import (
    get_current_month,
    get_device_usage_record,
    get_user_location,
    get_weather,
    list_available_report_months,
    search_product_knowledge,
    start_report_generation,
    set_request_client_ip,
    validate_user_id,
)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[
                search_product_knowledge,
                get_user_location,
                get_weather,
                get_current_month,
                validate_user_id,
                list_available_report_months,
                get_device_usage_record,
                start_report_generation,
            ],
            middleware=[monitor_tool, log_before_model, report_prompt_switch]
        )

    def execute_stream(self, query: str, client_ip: str | None = None):
        set_request_client_ip(client_ip)
        input_dict = {
            "messages": [
                {"role": "user", "content": query}
            ]
        }

        res = self.agent.stream(input_dict, stream_mode="values", context={"report":False})
        for chunk in res:
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + '\n'


if __name__ == '__main__':
    agent = ReactAgent()
    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk , end='', flush=True)
