"""
大模型相关操作类
"""

from langchain_core.messages.ai import AIMessage

from config.llm_config import LLMConfig

class LLMOperator():
    def __init__(self, llm_config: LLMConfig) -> None:
        model_name = llm_config.model_name
        api_key = llm_config.api_key
        base_url = llm_config.base_url
        api_type = llm_config.api_type
        low_model_name = model_name.lower().strip()
        if api_type == 'openai':
            from langchain_openai import ChatOpenAI
            if 'qwen3' in low_model_name:
                llm: ChatOpenAI = ChatOpenAI(
                    model=model_name,
                    base_url=base_url,
                    api_key=api_key,
                    streaming=False,
                    max_retries=5,
                    extra_body={
                        # 下面是vllm本地部署的配置
                        "chat_template_kwargs": {"enable_thinking": False},
                    }
                )
            else:
                llm: ChatOpenAI = ChatOpenAI(
                    model=model_name,
                    base_url=base_url,
                    api_key=api_key,
                    streaming=False,
                    max_retries=5,
                )
            

            self.model: ChatOpenAI = llm
        elif api_type == 'bailian':
            from langchain_openai import ChatOpenAI
            if 'qwen3' in low_model_name:
                llm: ChatOpenAI = ChatOpenAI(
                    model=model_name,
                    base_url=base_url,
                    api_key=api_key,
                    streaming=True,
                    max_retries=5,
                    # extra_body={
                    #     # 下面是使用千问平台的配置
                    #     "enable_thinking": False,
                    # }
                )
            else:
                llm: ChatOpenAI = ChatOpenAI(
                    model=model_name,
                    base_url=base_url,
                    api_key=api_key,
                    streaming=False,
                    max_retries=5,
                )
            self.model: ChatOpenAI = llm
        elif api_type == 'ollama':
            from langchain_ollama import ChatOllama
            if 'qwen3' in low_model_name:
                llm: ChatOllama = ChatOllama(
                    model=model_name,
                    base_url=base_url,
                    api_key=api_key,
                    streaming=True,
                    max_retries=5,
                )
            else:
                llm: ChatOllama = ChatOllama(
                    model=model_name,
                    base_url=base_url,
                    api_key=api_key,
                    streaming=False,
                    max_retries=5,
                )
            self.model: ChatOpenAI = llm
        else:
            print(f'不支持当前格式的api_type: {api_type}')


    def get_llm(self):
        return self.model



if __name__ == '__main__':
    llm_config: LLMConfig = LLMConfig()

    llm = LLMOperator(
        llm_config
    ).get_llm()

    ret_str: AIMessage = llm.invoke(
        input='你是谁', 
    )

    print(ret_str)