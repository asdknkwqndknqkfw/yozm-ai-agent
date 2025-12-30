from pathlib import Path

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

import sys
import uvicorn

# ① PYTHONPATH에 chapter8/a2a 패키지 경로 추가 (∵ 절대경로 사용)
sys.path.append(str(Path(__file__).parent.parent))

from basic_agent.agent_executor import HelloAgentExecutor

def create_agent_card() -> AgentCard:
    """
    에이전트 카드 생성 및 반환 함수
    1. AgentSkill class 객체 생성 및 반환
    2. AgentCard class 객체 생성 및 반환
    """

    # 에이전트 스킬 생성
    greeting_skill = AgentSkill(
        # AgentSkill:
        # 필수: id, name, description, tags
        # 선택: examples, input_modes, output_modes
        # 특이사항: default: str / 뒤에s: list[str]
        id="basic_greeting", # skill id(PK)
        name="Basic Greeting", # skill name
        description="간단한 인사와 기본적인 대화를 제공합니다", # client가 skill 언제 사용하는지
        tags=["greeting", "hello", "basic"],
        examples=["안녕하세요", "hello", "hi", "고마워요"],
        input_modes=["text"],
        output_modes=["text"],
    )

    # 에이전트 카드 생성
    agent_card = AgentCard( # Agent의 metadata, skill 정의
        name="Basic Hello World Agent",
        description="A2A 프로토콜을 학습하기 위한 기본적인 Hello World 에이전트입니다",
        url="http://localhost:9999/",   # 에이전트가 실제로 동작하는 서버 URL
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True), # 에이전트가 지원하는 추가 기능 (스트리밍 지원)
        skills=[greeting_skill], # 에이전트가 가진 스킬 목록을 정의
        supports_authenticated_extended_card=False, # 확장 카드(Extended Card)를 인증된 방식으로 지원하는지 여부
    )

    return agent_card

def main():
    # ② 에이전트 카드 생성
    agent_card = create_agent_card()

    port = 9999
    host = "0.0.0.0"

    print("Hello World 에이전트 서버 시작 중...")
    print(f"서버 구동 :  http://{host}:{port}")
    print(f"Agent Card: http://{host}:{port}/.well-known/agent.json")
    print("이것은 A2A 프로토콜 학습을 위한 기본 예제입니다")

    # ③ 기본 요청 핸들러 생성
    request_handler = DefaultRequestHandler( # 중간 계층 역할: HTTP Req → HelloAgentExecutor 전달
        agent_executor=HelloAgentExecutor(),
        task_store=InMemoryTaskStore(), # 비동기 작업들을 메모리에서 관리하는 저장소 (요청의 상태 추적, 취소 기능 지원)
    )

    # ④ A2A FastAPI 애플리케이션 생성
    # A2A Protocol의 표준 endpoint 자동 생성 → 직접 Routing 구현 필요 X
    server = A2AFastAPIApplication( # A2A Protocol에 필요한 모든 endpoint 자동 설정 (FastAPI 기반)
        agent_card=agent_card, # agent 정보 노출
        http_handler=request_handler, # 실제 요청 처리 로직 연결
    )

    # ⑤ 서버 빌드 및 실행
    app = server.build()
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()