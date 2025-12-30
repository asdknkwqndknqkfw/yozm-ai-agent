from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.types import Message
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI

""" 
Agent Executor: A2A 서버에서 받은 유저의 메시지를 Agent에 전달 및 실행하고 결괏값을 돌려주는 역할을 하는 클래스
1. execute: 메시지 전달, 에이전트 호출
2. cancel: 요청 취소 (에이전트가 처리할 수 없는 요청)
3. etc: 예제는 단순 인사를 하는 Agent → 취소 기능 구현 X
"""

load_dotenv()

class HelloAgent:
    """① 랭체인과 OpenAI를 사용한 간단한 Hello World 에이전트."""

    def __init__(self):
        self.chat = ChatOpenAI(
            model="gpt-4o-mini",
        )

        self.prompt = ChatPromptTemplate.from_messages([
            # Agent의 persona, 행동지침 정의
            SystemMessagePromptTemplate.from_template(
                """
                당신은 친절한 Hello World 에이전트입니다.
                사용자와 간단한 대화를 나누고, 인사와 기본적인 질문에 답변합니다. 
                당신의 목표는 사용자에게 친근하고 도움이 되는 경험을 제공하는 것입니다.
                """
            ),
            HumanMessagePromptTemplate.from_template("{message}")
        ])

    async def invoke(self, user_message: str) -> str:
        """② 유저 메시지를 처리하고 응답을 생성합니다."""
        chain = self.prompt | self.chat
        response = await chain.ainvoke({"message": user_message})
        return response.content


class HelloAgentExecutor(AgentExecutor):
    """③ 간단한 Hello World 에이전트의 Executor
    1. AgentExecutor 상속 → A2A Protocol과 HelloAgent를 연결하는 Adapter 역할
    2. A2A server와의 통신을 처리, HelloAgent의 기능을 A2A protocol에 맞게 wrapping
    3. 생성자에서 HelloAgent Instance를 생성하여 내부적 관리
    """

    def __init__(self):
        self.agent = HelloAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        """④ 요청을 처리하고 응답을 생성합니다."""
        # 유저 메시지를 추출
        message = context.message
        # Text type의 part만 추출(∵ A2A protocol이 multi-modal msg 지원)
        for part in message.parts:
            # print(f'part: {part}\n') # root=TextPart(kind='text', metadata=None, text='안녕하세요')
            if part.root.kind == "text":
                user_message = part.root.text

        # 에이전트 실행
        result = await self.agent.invoke(user_message)

        # ⑤ 응답 메시지를 생성하고 이벤트 큐에 추가
        await event_queue.enqueue_event( # 비동기적으로 client에게 event를 전달 (streaming, Multi-Res(다중 응답) 지원)
            new_agent_text_message(result) # Res Msg → A2A protocol Msg 변환
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        """요청을 취소"""
        # 취소 기능은 지원하지 않음
        error_msg = "취소 기능은 지원되지 않습니다. Hello 에이전트는 즉시 응답합니다."
        error_message = Message(role="agent", parts=[{"type": "text", "text": error_msg}], message_id="cancel_error", )
        event_queue.enqueue_event(error_message)