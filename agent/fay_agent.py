import os
import math

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.memory import VectorStoreRetrieverMemory
import faiss
from langchain.docstore import InMemoryDocstore
from langchain.vectorstores import FAISS
from langchain.agents import Tool, initialize_agent, agent_types

from agent.tools.MyTimer import MyTimer
from agent.tools.Weather import Weather
from agent.tools.CheckSensor import CheckSensor
from agent.tools.Switch import Switch
from agent.tools.Knowledge import Knowledge
from agent.tools.Say import Say
from agent.tools.QueryTimerDB import QueryTimerDB
from agent.tools.DeleteTimer import DeleteTimer
from agent.tools.GetSwitchLog import GetSwitchLog
from agent.tools.getOnRunLinkage import getOnRunLinkage
from agent.tools.QueryTime import QueryTime
from agent.tools.PythonExecutor import PythonExecutor
from agent.tools.WebPageRetriever import WebPageRetriever

from langchain.callbacks import get_openai_callback
from langchain.retrievers import TimeWeightedVectorStoreRetriever

import utils.config_util as utils
from utils import util


class FayAgentCore():
    def __init__(self):
        utils.load_config()
        os.environ['OPENAI_API_KEY'] = utils.key_gpt_api_key
        os.environ['OPENAI_API_BASE'] = utils.gpt_base_url
        #使用open ai embedding
        embedding_size = 1536  # OpenAIEmbeddings 的维度
        index = faiss.IndexFlatL2(embedding_size)
        embedding_fn = OpenAIEmbeddings()

        #创建llm
        self.llm = ChatOpenAI(model="gpt-4-0125-preview", verbose=True)

        #创建向量数据库
        def relevance_score_fn(score: float) -> float:
            return 1.0 - score / math.sqrt(2)
        vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {}, relevance_score_fn=relevance_score_fn)

        # 创建记忆(斯坦福小镇同款记忆检索机制:时间、相关性、重要性三个维度)
        retriever = TimeWeightedVectorStoreRetriever(vectorstore=vectorstore, other_score_keys=["importance"], k=3)  
        self.agent_memory = VectorStoreRetrieverMemory(memory_key="history", retriever=retriever)

        # 保存基本信息到记忆
        utils.load_config()
        attr_info = ", ".join(f"{key}: {value}" for key, value in utils.config["attribute"].items())
        self.agent_memory.save_context({"input": "我的基本信息是?"}, {"output": attr_info})

        #内存保存聊天历史
        self.chat_history = []

        #创建agent chain
        my_timer = MyTimer()
        weather_tool = Weather()
        check_sensor_tool = CheckSensor()
        switch_tool = Switch()
        knowledge_tool = Knowledge()
        say_tool = Say()
        query_timer_db_tool = QueryTimerDB()
        delete_timer_tool = DeleteTimer()
        get_switch_log = GetSwitchLog()
        get_on_run_linkage = getOnRunLinkage()
        python_executor = PythonExecutor()
        web_page_retriever = WebPageRetriever()
        
        self.tools = [
            Tool(
                name=python_executor.name,
                func=python_executor.run,
                description=python_executor.description
            ),
            Tool(
                name=my_timer.name,
                func=my_timer.run,
                description=my_timer.description
            ),
            Tool(
                name=weather_tool.name,
                func=weather_tool.run,
                description=weather_tool.description
            ),
            Tool(
                name=check_sensor_tool.name,
                func=check_sensor_tool.run,
                description=check_sensor_tool.description
            ),
            Tool(
                name=switch_tool.name,
                func=switch_tool.run,
                description=switch_tool.description
            ),
            Tool(
                name=knowledge_tool.name,
                func=knowledge_tool.run,
                description=knowledge_tool.description
            ),
            Tool(
                name=say_tool.name,
                func=say_tool.run,
                description=say_tool.description
            ),
            Tool(
                name=query_timer_db_tool.name,
                func=query_timer_db_tool.run,
                description=query_timer_db_tool.description
            ),
            Tool(
                name=delete_timer_tool.name,
                func=delete_timer_tool.run,
                description=delete_timer_tool.description
            ),
            Tool(
                name=get_switch_log.name,
                func=get_switch_log.run,
                description=get_switch_log.description
            ),
            Tool(
                name=get_on_run_linkage.name,
                func=get_on_run_linkage.run,
                description=get_on_run_linkage.description
            ),
            Tool(
                name=web_page_retriever.name,
                func=web_page_retriever.run,
                description=web_page_retriever.description
            )
        ]

        #agent用于执行任务
        self.agent = initialize_agent(agent_types=agent_types.AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                         tools=self.tools, llm=self.llm, verbose=True,
                         max_history=5, handle_parsing_errors=True)

        #记录一轮执行有无调用过say tool
        self.is_use_say_tool = False   
        self.say_tool_text = ""

        self.total_tokens = 0
        self.total_cost = 0

    #记忆prompt
    def format_history_str(self, str):
        result = ""
        history_string = str['history']

        # Split the string into lines
        lines = history_string.split('input:')

        # Initialize an empty list to store the formatted history
        formatted_history = []

        #处理记忆流格式
        for line in lines:
            if "output" in line:
                input_line = line.split("output:")[0].strip()
                output_line = line.split("output:")[1].strip()
                formatted_history.append({"input": input_line, "output": output_line})

        
        # 记忆流转换成字符串
        result += "-以下是与用户说话关连度最高的记忆：\n"
        for i in range(len(formatted_history)):
            if i >= 3:
                break
            line = formatted_history[i]
            result += f"--input：{line['input']}\n--output：{line['output']}\n"
        if len(formatted_history) == 0:
            result += "--没有记录\n"


        #添加内存记忆
        formatted_history = []
        for line in self.chat_history:
            formatted_history.append({"input": line[0], "output": line[1]})
        
        #格式化内存记忆字符串
        result += "\n-以下刚刚的对话：\n"
        for i in range(len(formatted_history)):
            line = formatted_history[i]
            result += f"--input：{line['input']}\n--output：{line['output']}\n"
        if len(formatted_history) == 0:
            result += "--没有记录\n"

        return result
    
    def run(self, input_text):
        self.is_use_say_tool = False
        self.say_tool_text = ""
        
        result = ""
        history = self.agent_memory.load_memory_variables({"input":input_text.replace('主人语音说了：', '').replace('主人文字说了：', '')})
        history = self.format_history_str(history)
        try:
            input_text = input_text.replace('主人语音说了：', '').replace('主人文字说了：', '')
            agent_prompt = """
现在时间是：{now_time}。你是一个智慧农业系统中的AI，负责协助主人打理农作物和陪伴主人生活、工作。请依据以下信息为主人服务 ：
{history}
input：{input_text}
output：
""".format(history=history, input_text=input_text, now_time=QueryTime().run(""))
            with get_openai_callback() as cb:
                result = self.agent.run(agent_prompt)
                self.total_tokens = self.total_tokens + cb.total_tokens
                self.total_cost = self.total_cost + cb.total_cost
                util.log(1, "本次消耗token:{}， Cost (USD):{}，共消耗token:{}， Cost (USD):{}".format(cb.total_tokens, cb.total_cost, self.total_tokens, self.total_cost))
                    
        except Exception as e:
            print(e)
        
        result = "执行完毕" if result is None or result == "N/A" else result
        chat_text = self.say_tool_text if self.is_use_say_tool else result

        #保存到记忆流和聊天对话
        self.agent_memory.save_context({"input": input_text.replace('主人语音说了：', '').replace('主人文字说了：', '')},{"output": result})
        self.chat_history.append((input_text.replace('主人语音说了：', '').replace('主人文字说了：', ''), chat_text))
        if len(self.chat_history) > 5:
            self.chat_history.pop(0)

        return self.is_use_say_tool, chat_text

if __name__ == "__main__":
    agent = FayAgentCore()
    print(agent.run("你好"))
