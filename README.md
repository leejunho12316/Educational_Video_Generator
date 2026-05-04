# Educational_Video_Generator
교육 영상 제작 Tool Calling Multi Agent System


# 추가할 내용
1. 디테일한 개요 - B2B 관점 아이데이션
2. FE/BE 붙여 스크린샷
3. 성능 고도화, LLM Judge 등 정량적 측정 2개
4. 최종 결과 YouTube Link

# Cloud 적용 시 

1. AWS S3 - 저장소 구성

ppt 입력용, 최종 mp4 출력용 S3 저장소 구성
사용자가 엔드포인트에서 ppt 업로드하면 S3 Bucket에 업로드. Video Generator 코드 실행 시 Bucket 주소로부터 ppt 가져오고 영상 생성. 최종 영상 생성되면 S3 Bucket에 업로드 하고 사용자가 엔드포인트에서 그 Bucket 업로드 된 영샹을 다운받을 수 있도록 설계.
(중간 과정 부산물들은 임시 local에 그냥 저장.)

2. AWS ECR - 컨테이너 레지스트리

Project 코드 전체 Docker 컨테이너화 -> AWS ECR에 push

3. AWS SQS - 작업 큐

영상 생성 요청을 AWS SQS를 통해 큐에 적재해 차례대로 생성.

4. AWS ECS Fargate - 워커 컴퓨팅

ECS를 통해 ECR에 저장되어 있는 Docker Image pull 하고 실행. SQS를 통해 작업 요청을 차례대로 받아들이며 영상 생성 진행.
(Fargate : 서버리스. Fargate X : EC2위에서 돌리기)
(워커 컴퓨팅 : 작업을 받아서 처리하는 데 특화된 컴퓨팅 방식)

5. AWS API Gateway + Lamgda - API 엔드포인트

사용자 ppt 파일 전송 -> API Gateway -> Lambda -> S3에 PPT 저장, SQS에 작업 등록

6. AWS Secrets Manager - API 키 관리

OpenAI, Tavily API 키를 코드에 하드코딩하지 않고 Secrets Manager에서 주입

7. 웹 UI (선택)
  - Gradio나 FastAPI를 ECS에 같이 올리거나
  - 슬라이드 수에 따라 처리 시간이 달라지므로 타임아웃 여유있게 설정 필요













# LangGraph Graph

<img src="./README_resources/LangGraph_Graph.png" width="250">

<br><br><br>

# State Specifications

```
{'pptx_path': 'sample2 (1).pptx',
 'work_dir': './step1_output',
 'prompt': {'voice': 'alloy',
  'tone': '친절하고 명료한 강의 톤',
  'style': '예시와 핵심 요점 중심'},
 'slides': [{'index': 1,
   'title': '모델 성능 모니터링',
   'texts': ['모델 모니터링\n프로덕션 환경에서 ML 모델의 성능 및 동작을 지속적으로 추적, 분석, 평가하는 프로세스\n필요성 : 모델은 배포 후에도 품질 저하, 데이터 문제, 사용 환경 변화 등의 위험에 노출됨\n주요 리스크\n데이터/컨셉 드리프트\n데이터 품질 문제\n적대적 공격(예: prompt injection)\n연결된 앞 단계의 모델 오류 전파\n모니터링 목표\n문제 조기 탐지\n근본 원인 분석\n모델 동작 이해 및 투명한 문서화',
    '모델 성능 모니터링',
    '1'],
   'tables': [],
   'images': ['./step1_output/media/sample2 (1)_slide1_2.png'],
   'snap': '/content/step1_output/sample2 (1).png'},
  {'index': 2,
   'title': 'ML 모델에 영향을 줄 수 있는 요인',
   'texts': ['최초 정의한 문제의 컨셉 변화(Concept Drift)\n시간 경과에 따라 데이터 변수 또는 패턴 간의 관계가 지속적으로 변할 수 있음.\n모델 환경에 갑작스럽고 예상치 못한 변화가 발생하여 성능에 상당한 영향을 미칠 수 있는 상황\x0b(예 : COVID-19)',
    'ML 모델에 영향을 줄 수 있는 요인',
    '2'],
   'tables': [],
   'images': ['./step1_output/media/sample2 (1)_slide2_2.png'],
   'snap': '/content/step1_output/slide_img-2.png'},
  {'index': 3,
   'title': '모델 모니터링 아키텍처',
   'texts': ['두 가지 접근 방식\n배치(Batch) 모니터링 : 정해진 주기(일간, 주간 등)나 특정 이벤트 발생 시 모니터링\n실시간(Streaming) 모니터링 : ML 예측 서비스에서 발생한 데이터를 모니터링 시스템에 실시간으로 전송, 지속적으로 품질 지표를 계산 및 업데이트',
    '모델 모니터링 아키텍처',
    '3'],
   'tables': [[['항목', '배치 모니터링', '실시간 모니터링'],
     ['데이터 흐름', '정해진 시간마다', '스트리밍(실시간)'],
     ['적합한 환경', '일반 ML 서비스, 배치 처리', '실시간 예측 서비스'],
     ['속도', '느림 (지연 있음)', '빠름 (즉시 감지 가능)'],
     ['운영 비용', '낮음', '높음 (복잡한 인프라)'],
     ['한계', 'Abnormal 에 대한 지연된 탐지', 'Ground Truth 데이터 확인 지연 시 적용에 한계']]],
   'images': [],
   'snap': '/content/step1_output/slide_img-3.png'}],
 'n_slides': 3,
 'slide_index': 3,
 'cur_search_context': '모델 성능 모니터링은 머신러닝 모델의 성능과 동작을 지속적으로 추적하고 분석하는 과정으로, 데이터 과학자에게 모델의 가시성을 제공합니다. 이 과정은 모델이 변동성이 큰 데이터 세트에서 실행될 때 특히 중요하며, 자동화된 알림을 통해 이상치를 실시간으로 감지하여 문제 발생 전에 대응할 수 있게 합니다. 또한, 강력한 모니터링과 자동 교정 기능을 결합하면 문제 해결 시간을 단축하고 비즈니스 가치를 극대화할 수 있습니다.',
 'cur_page_content': '## 모델 모니터링 아키텍처\n\n### 두 가지 접근 방식\n1. **배치(Batch) 모니터링**: \n   - 정해진 주기(일간, 주간 등)나 특정 이벤트 발생 시 모니터링\n2. **실시간(Streaming) 모니터링**: \n   - ML 예측 서비스에서 발생한 데이터를 모니터링 시스템에 실시간으로 전송하여 지속적으로 품질 지표를 계산 및 업데이트\n\n### 비교 표\n\n| 항목         | 배치 모니터링          | 실시간 모니터링      |\n|--------------|------------------------|----------------------|\n| 데이터 흐름  | 정해진 시간마다        | 스트리밍(실시간)     |\n| 적합한 환경   | 일반 ML 서비스, 배치 처리 | 실시간 예측 서비스    |\n| 속도         | 느림 (지연 있음)      | 빠름 (즉시 감지 가능) |\n| 운영 비용     | 낮음                   | 높음 (복잡한 인프라) |\n| 한계         | Abnormal에 대한 지연된 탐지 | Ground Truth 데이터 확인 지연 시 적용에 한계 |\n\n이 아키텍처는 모델의 성능과 품질을 지속적으로 모니터링하기 위한 두 가지 접근 방식을 설명하며, 각 방식의 특징과 장단점을 비교합니다.',
 'cur_script': '안녕하세요, 오늘은 모델 모니터링 아키텍처에 대해 말씀드리겠습니다. 이 아키텍처는 두 가지 접근 방식인 배치 모니터링과 실시간 모니터링을 통해 모델의 성능과 품질을 지속적으로 관리하는 방법을 제시합니다. 배치 모니터링은 정해진 주기나 이벤트에 따라 데이터를 분석하는 반면, 실시간 모니터링은 ML 예측 서비스에서 발생한 데이터를 즉시 전송하여 품질 지표를 지속적으로 업데이트합니다.\n\n비교 표를 통해 각 방식의 특징을 살펴보면, 배치 모니터링은 운영 비용이 낮지만 데이터 흐름이 느리고, 실시간 모니터링은 빠른 속도로 이상을 감지할 수 있지만 복잡한 인프라가 필요하다는 점이 있습니다. \n\n모델 성능 모니터링은 머신러닝 모델의 가시성을 높이고, 변동성이 큰 데이터에서의 실행을 지원합니다. 또한, 자동화된 알림을 통해 문제를 사전에 감지할 수 있어 비즈니스 가치를 극대화하는 데 기여합니다. 마지막으로, 강력한 모니터링과 자동 교정 기능의 결합은 문제 해결 시간을 단축시킵니다. 감사합니다.',
 'cur_audio': './step1_output/narration_3.mp3',
 'cur_video': './step1_output/slide3_lecture.mp4',
 'video_paths': ['./step1_output/slide1_lecture.mp4',
  './step1_output/slide2_lecture.mp4',
  './step1_output/slide3_lecture.mp4'],
 'final_video': './step1_output/final.mp4',
 'messages': [AIMessage(content='[정제 text]\n### 모델 성능 모니터링\n\n#### 1. 모델 모니터링\n- **정의**: 프로덕션 환경에서 머신러닝(ML) 모델의 성능 및 동작을 지속적으로 추적, 분석, 평가하는 프로세스.\n- **필요성**: 모델은 배포 후에도 품질 저하, 데이터 문제, 사용 환경 변화 등의 위험에 노출됨.\n\n#### 2. 주요 리스크\n- **데이터/컨셉 드리프트**: 시간이 지남에 따라 데이터의 분포가 변화하는 현상.\n- **데이터 품질 문제**: 입력 데이터의 품질 저하로 인한 문제.\n- **적대적 공격**: 예를 들어, 프롬프트 인젝션과 같은 공격.\n- **모델 오류 전파**: 연결된 앞 단계의 모델에서 발생한 오류가 후속 모델에 영향을 미침.\n\n#### 3. 모니터링 목표\n- **문제 조기 탐지**: 성능 저하나 오류를 신속하게 발견.\n- **근본 원인 분석**: 문제의 근본적인 원인을 파악.\n- **모델 동작 이해 및 투명한 문서화**: 모델의 작동 방식을 이해하고 이를 문서화하여 투명성을 높임.\n\n#### 4. 성능 지표\n- **예측 수**: 1820회 예측.\n- **이상 탐지 수**: 22회 이상 탐지.\n\n#### 5. 시각화\n- **예측 vs 실제**: 예측 값과 실제 값의 비교 그래프 제공. \n\n이 내용은 모델 성능 모니터링의 중요성과 그 과정에서 고려해야 할 요소들을 종합적으로 설명합니다.\n[Tool검색]', additional_kwargs={}, response_metadata={}, id='9993c53a-096f-446d-a2ae-1b6e8c823739', tool_calls=[], invalid_tool_calls=[]),
  AIMessage(content='', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 30, 'prompt_tokens': 1618, 'total_tokens': 1648, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_3084892da3', 'id': 'chatcmpl-Db3gsKd3uj3fpHl4VYG24ckJdJ1u2', 'service_tier': 'default', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019de8a6-1c64-7002-85cf-c4b557e8d059-0', tool_calls=[{'name': 'tavily_search', 'args': {'query': '모델 성능 모니터링 중요성', 'search_depth': 'advanced'}, 'id': 'call_WRILNRHGwdhfzrS8JE6iMngJ', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 1618, 'output_tokens': 30, 'total_tokens': 1648, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),
  ToolMessage(content='{"query": "모델 성능 모니터링 중요성", "follow_up_questions": null, "answer": null, "images": [], "results": [{"url": "https://www.samsungsds.com/kr/insights/ml_model_monitoring.html", "title": "ML 모델, 모니터링이 중요한 이유 | 인사이트리포트 | 삼성SDS", "content": "애플리케이션의 성능, 안정성, 오류 조건을 모니터링하는 것과 마찬가지로, 머신러닝 모델 모니터링은 데이터 과학자에게 모델 성능에 관한 가시성을 제공한다. 모니터링은 모델이 예측에 사용되거나 해당 ML이 변동성 높은 데이터 세트에서 실행될 때 특히 중요하다.  \\n  \\n이터레이티브(Iterative)의 공동설립자 겸 CEO 드미트리 페트로프에 따르면 “ML 팀이 모델을 개선하고 모든 것이 의도한 대로 실행되길 원하기 때문에 모델 모니터링은 성능 및 문제 해결에 목표를 둔다.”  \\n  \\n무브웍스(Moveworks)의 수석 제품 관리자 라훌 카얄라는 “ML 모델 모니터링은 기업이 ‘AI 예측의 이점’과 ‘예측 가능한 결과에 대한 니즈’ 간의 균형을 맞추는 데 도움을 줄 수 있다”라며, “자동화된 알림을 통해 ML 운영팀이 이상치를 실시간 감지하여 피해 발생 전에 대응할 시간을 확보할 수 있다”라고 설명했다.  \\n  \\n모델옵(ModelOp)의 공동설립자 스튜 베일리는 “강력한 모니터링과 자동 교정 기능을 결합하면 문제 해결 시간을 단축할 수 있다. 이는 비즈니스 가치를 극대화하고 위험을 줄이는 데 있어 핵심이다”라고 언급했다. [...] ## ML 모니터링 베스트 프랙티스\\n\\n‘모델옵스, ML 모니터링, 모델 성능 관리’는 머신러닝 모델이 예상대로 작동하고, 신뢰할 수 있는 예측을 제공하도록 하는 관행 및 도구에 대한 용어다. 그렇다면 데이터 과학 및 데브옵스 팀은 이를 구축할 때 어떤 관행을 고려해야 할까?   \\n  \\n도미노 데이터 랩(Domino Data Lab)의 수석 필드 데이터 과학자 조쉬 포두스카는 “모델 모니터링은 중요하고 지속적인 프로세스다. 드리프트된 모델의 정확도를 개선하려면 ‘ground truth(모델이 예측해 주길 바라는 답)’ 라벨과 함께 최신 데이터로 다시 학습시켜야 한다”라고 전했다.  \\n  \\n아노도트(Anodot)의 공동설립자 겸 수석 데이터 과학자 아이라 코헨은 “ML 모델 모니터링에 중요한 점이 있다. 입력 변화가 문제를 일으킬 수 있기 때문에 모델의 출력 및 입력을 모니터링해야 한다”라면서, 모델 성능을 직접 또는 충분히 빠르게 측정할 수 없을 때 프록시 측정법을 사용하라고 권장했다.\\n\\n삼성SDS 브라이틱스 머신러닝 - 다양한 분석 자동화 기능을 통해 누구나 쉽고 빠르게 AI 분석 서비스를 개발하고 활용\\n\\n이어 “데이터 과학자는 모델 모니터링을 위한 도구가 필요하다. 모델을 수동으로 모니터링하는 것은 확장성이 없으며, (대시보드와 보고서가) 많은 AI 모델이 배포될 때 생성되는 모니터링 데이터의 복잡성과 볼륨을 처리할 수 없다”라고 말했다.", "score": 0.9997981, "raw_content": null}], "response_time": 2.44, "request_id": "79d1785c-9de5-4577-9543-97e9790550f8"}', name='tavily_search', id='a01f68d0-e4aa-40cc-b889-a70d8e1df278', tool_call_id='call_WRILNRHGwdhfzrS8JE6iMngJ'),
  AIMessage(content='모델 성능 모니터링은 머신러닝 모델의 성능과 동작을 지속적으로 추적하고 분석하는 과정으로, 데이터 과학자에게 모델의 가시성을 제공합니다. 이 과정은 모델이 변동성이 큰 데이터 세트에서 실행될 때 특히 중요하며, 자동화된 알림을 통해 이상치를 실시간으로 감지하여 문제 발생 전에 대응할 수 있게 합니다. 또한, 강력한 모니터링과 자동 교정 기능을 결합하면 문제 해결 시간을 단축하고 비즈니스 가치를 극대화할 수 있습니다.', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 123, 'prompt_tokens': 2497, 'total_tokens': 2620, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 1536}}, 'model_provider': 'openai', 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_3084892da3', 'id': 'chatcmpl-Db3gvqg80E6tm99fevro0J1cwIfDM', 'service_tier': 'default', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--019de8a6-2a57-7033-8b11-213ea40213b8-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 2497, 'output_tokens': 123, 'total_tokens': 2620, 'input_token_details': {'audio': 0, 'cache_read': 1536}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),
  AIMessage(content='[정제 text]\n### ML 모델에 영향을 줄 수 있는 요인\n\n#### 1. 최초 정의한 문제의 컨셉 변화 (Concept Drift)\n- **정의**: 시간 경과에 따라 데이터 변수 또는 패턴 간의 관계가 지속적으로 변할 수 있는 현상.\n- **영향**: 모델 환경에 갑작스럽고 예상치 못한 변화가 발생하여 성능에 상당한 영향을 미칠 수 있는 상황.\n  - **예시**: COVID-19와 같은 사건이 발생했을 때.\n\n#### 2. 시각적 자료\n- **그래프 설명**: \n  - **X축**: 시간\n  - **Y축**: 라운지웨어 판매량\n  - **실제 판매량 (actual)**: 빨간 선으로 표시.\n  - **예측 판매량 (predicted)**: 점선으로 표시.\n  - **주요 사건**: "national lockdown announced"라는 레이블이 있는 지점에서 판매량의 급격한 변화가 나타남.\n\n이 내용은 ML 모델의 성능에 영향을 줄 수 있는 중요한 요소인 컨셉 드리프트를 설명하고 있습니다.\n[Tool검색]', additional_kwargs={}, response_metadata={}, id='a6abe26c-0d49-4c73-9896-dfa325575cbf', tool_calls=[], invalid_tool_calls=[]),
  AIMessage(content='', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 30, 'prompt_tokens': 2870, 'total_tokens': 2900, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 1920}}, 'model_provider': 'openai', 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_3084892da3', 'id': 'chatcmpl-Db3hw4epw8UsgPR9NfmW4pawGjRMA', 'service_tier': 'default', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019de8a7-217a-7461-9501-eb7088792d4b-0', tool_calls=[{'name': 'tavily_search', 'args': {'query': '컨셉 드리프트 개념과 영향', 'search_depth': 'advanced'}, 'id': 'call_hYKcFOqsDKy9lMJHkxcX3G8d', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 2870, 'output_tokens': 30, 'total_tokens': 2900, 'input_token_details': {'audio': 0, 'cache_read': 1920}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),
  ToolMessage(content='{"query": "컨셉 드리프트 개념과 영향", "follow_up_questions": null, "answer": null, "images": [], "results": [{"url": "https://ahha.ai/2024/12/09/model-drift/", "title": "[AIOps] AI 도입 성공 여부 가르는 모델 드리프트란? - AHHA Labs", "content": "### (2) 컨셉 드리프트\\n\\n컨셉 드리프트는 모델의 입력과 출력 간의 변화입니다. 모델이 예측하려는 목표 변수가 시간이 지남에 따라 변하는 경우에 발생하죠. 아래 예시로 보다 쉽게 설명드릴게요.\\n\\n예시: 품질 관리 기준 변화\\n\\n– 상황: 특정 제조 공장에서 AI 모델을 활용하여 제품의 결함 여부를 판별하고 있다고 가정해보죠. 초기에는 제품 표면의 미세한 긁힘이 결함으로 간주되지 않았지만, 시간이 지나면서 고객의 품질 요구가 강화되어 이제는 이러한 긁힘도 결함으로 간주합니다. 이 경우 입력 데이터 분포는 변화 없이 그대로지만, 입력과 출력(불량 판별) 간의 관계가 변했습니다.\\n\\n– 영향: AI 모델은 기존 데이터에 기반해 긁힘이 없는 제품만 결함이 아니라고 판단했기 때문에, 변화된 기준을 충족하지 못합니다. 결과적으로 모델이 결함을 올바르게 예측하지 못하게 됩니다.\\n\\n– 결과: 제조 공정에서 결함률을 잘못 판단하거나 잘못된 품질 관리 결정을 내리게 되어, 고객 만족도와 수익에 부정적인 영향을 미칠 수 있습니다.\\n\\n[참고] 데이터 드리프트 vs. 컨셉 드리프트 [...] ### (2) 컨셉 드리프트\\n\\n컨셉 드리프트는 모델의 입력과 출력 간의 변화입니다. 모델이 예측하려는 목표 변수가 시간이 지남에 따라 변하는 경우에 발생하죠. 아래 예시로 보다 쉽게 설명드릴게요.\\n\\n예시: 품질 관리 기준 변화\\n\\n– 상황: 특정 제조 공장에서 AI 모델을 활용하여 제품의 결함 여부를 판별하고 있다고 가정해보죠. 초기에는 제품 표면의 미세한 긁힘이 결함으로 간주되지 않았지만, 시간이 지나면서 고객의 품질 요구가 강화되어 이제는 이러한 긁힘도 결함으로 간주합니다. 이 경우 입력 데이터 분포는 변화 없이 그대로지만, 입력과 출력(불량 판별) 간의 관계가 변했습니다.\\n\\n– 영향: AI 모델은 기존 데이터에 기반해 긁힘이 없는 제품만 결함이 아니라고 판단했기 때문에, 변화된 기준을 충족하지 못합니다. 결과적으로 모델이 결함을 올바르게 예측하지 못하게 됩니다.\\n\\n– 결과: 제조 공정에서 결함률을 잘못 판단하거나 잘못된 품질 관리 결정을 내리게 되어, 고객 만족도와 수익에 부정적인 영향을 미칠 수 있습니다.\\n\\n[참고] 데이터 드리프트 vs. 컨셉 드리프트 [...] ### (2) 컨셉 드리프트\\n\\n컨셉 드리프트는 모델의 입력과 출력 간의 변화입니다. 모델이 예측하려는 목표 변수가 시간이 지남에 따라 변하는 경우에 발생하죠. 아래 예시로 보다 쉽게 설명드릴게요.\\n\\n예시: 품질 관리 기준 변화\\n\\n– 상황: 특정 제조 공장에서 AI 모델을 활용하여 제품의 결함 여부를 판별하고 있다고 가정해보죠. 초기에는 제품 표면의 미세한 긁힘이 결함으로 간주되지 않았지만, 시간이 지나면서 고객의 품질 요구가 강화되어 이제는 이러한 긁힘도 결함으로 간주합니다. 이 경우 입력 데이터 분포는 변화 없이 그대로지만, 입력과 출력(불량 판별) 간의 관계가 변했습니다.\\n\\n– 영향: AI 모델은 기존 데이터에 기반해 긁힘이 없는 제품만 결함이 아니라고 판단했기 때문에, 변화된 기준을 충족하지 못합니다. 결과적으로 모델이 결함을 올바르게 예측하지 못하게 됩니다.\\n\\n– 결과: 제조 공정에서 결함률을 잘못 판단하거나 잘못된 품질 관리 결정을 내리게 되어, 고객 만족도와 수익에 부정적인 영향을 미칠 수 있습니다.\\n\\n[참고] 데이터 드리프트 vs. 컨셉 드리프트", "score": 0.9993881, "raw_content": null}], "response_time": 1.64, "request_id": "8828a341-bc1d-4841-9d53-d47caea497c9"}', name='tavily_search', id='17a3963b-5488-4b4b-9a14-71c681234a26', tool_call_id='call_hYKcFOqsDKy9lMJHkxcX3G8d'),
  AIMessage(content='모델 성능 모니터링은 머신러닝 모델의 성능과 동작을 지속적으로 추적하고 분석하는 과정으로, 데이터 과학자에게 모델의 가시성을 제공합니다. 이 과정은 모델이 변동성이 큰 데이터 세트에서 실행될 때 특히 중요하며, 자동화된 알림을 통해 이상치를 실시간으로 감지하여 문제 발생 전에 대응할 수 있게 합니다. 또한, 강력한 모니터링과 자동 교정 기능을 결합하면 문제 해결 시간을 단축하고 비즈니스 가치를 극대화할 수 있습니다.', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 123, 'prompt_tokens': 3908, 'total_tokens': 4031, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 2816}}, 'model_provider': 'openai', 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_3084892da3', 'id': 'chatcmpl-Db3hzePltk2KSi0Jfwh1ZGyl3RDNb', 'service_tier': 'default', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--019de8a7-2bf8-7d62-8ca0-062a06abb02e-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 3908, 'output_tokens': 123, 'total_tokens': 4031, 'input_token_details': {'audio': 0, 'cache_read': 2816}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),
  AIMessage(content='[정제 text]\n## 모델 모니터링 아키텍처\n\n### 두 가지 접근 방식\n1. **배치(Batch) 모니터링**: \n   - 정해진 주기(일간, 주간 등)나 특정 이벤트 발생 시 모니터링\n2. **실시간(Streaming) 모니터링**: \n   - ML 예측 서비스에서 발생한 데이터를 모니터링 시스템에 실시간으로 전송하여 지속적으로 품질 지표를 계산 및 업데이트\n\n### 비교 표\n\n| 항목         | 배치 모니터링          | 실시간 모니터링      |\n|--------------|------------------------|----------------------|\n| 데이터 흐름  | 정해진 시간마다        | 스트리밍(실시간)     |\n| 적합한 환경   | 일반 ML 서비스, 배치 처리 | 실시간 예측 서비스    |\n| 속도         | 느림 (지연 있음)      | 빠름 (즉시 감지 가능) |\n| 운영 비용     | 낮음                   | 높음 (복잡한 인프라) |\n| 한계         | Abnormal에 대한 지연된 탐지 | Ground Truth 데이터 확인 지연 시 적용에 한계 |\n\n이 아키텍처는 모델의 성능과 품질을 지속적으로 모니터링하기 위한 두 가지 접근 방식을 설명하며, 각 방식의 특징과 장단점을 비교합니다.\n[Tool검색]', additional_kwargs={}, response_metadata={}, id='7e4ea512-7311-4716-a63d-bfe79b416bfc', tool_calls=[], invalid_tool_calls=[]),
  AIMessage(content='', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 80, 'prompt_tokens': 4335, 'total_tokens': 4415, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 3840}}, 'model_provider': 'openai', 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_3084892da3', 'id': 'chatcmpl-Db3kWm8eKrsdAkZPwIyW9leBTrOEM', 'service_tier': 'default', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019de8a9-9087-70a1-a3c1-ee476e7574fa-0', tool_calls=[{'name': 'tavily_search', 'args': {'query': '모델 모니터링 아키텍처', 'search_depth': 'basic'}, 'id': 'call_04K4blMUgeSLZf4w38TVHJpf', 'type': 'tool_call'}, {'name': 'tavily_search', 'args': {'query': '배치 모니터링과 실시간 모니터링 비교', 'search_depth': 'basic'}, 'id': 'call_ALcIDk5h03s11gjizAI75G1B', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 4335, 'output_tokens': 80, 'total_tokens': 4415, 'input_token_details': {'audio': 0, 'cache_read': 3840}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),
  ToolMessage(content='{"query": "모델 모니터링 아키텍처", "follow_up_questions": null, "answer": null, "images": [], "results": [{"url": "https://docs.mlrun.org/en/latest/model-monitoring/index.html", "title": "Model monitoring architecture", "content": "Take a deeper dive into model monitoring functionality, including its APIs, model and model monitoring endpoints, multi-port predictions, batch inputs, and more. * Model and model monitoring endpoints. * application controller function: handles the monitoring processing and the triggers the apps that trigger the writer. * writer function: writes the results and the metrics that output from the model monitoring applications to the databases, and outputs alerts according to the user configuration. The model monitoring process flow starts with collecting operational data from a function in the model serving pod. The model monitoring stream pod forwards data to a Parquet database. Each model monitoring application is a separate nuclio real-time function. * `disable_model_monitoring()` — Disables the model monitoring application controller, writer, stream, histogram data drift application and the user\'s applications functions, according to the given parameters. For each model that is served in a model serving function, there is a model endpoint.", "score": 0.7913865, "raw_content": null}], "response_time": 0.93, "request_id": "936d64a1-db4b-43df-807c-e2fb15076027"}', name='tavily_search', id='609d64d3-1873-47c0-baee-1947d4ecc08b', tool_call_id='call_04K4blMUgeSLZf4w38TVHJpf'),
  ToolMessage(content='{"query": "배치 모니터링과 실시간 모니터링 비교", "follow_up_questions": null, "answer": null, "images": [], "results": [{"url": "https://jjeongil.tistory.com/2716", "title": "배치 처리 vs. 스트림 처리: 왜 스트리밍이 대세이고 배치는 사라지고 ...", "content": "실시간 모니터링의 어려움: 배치 처리에서는 데이터가 한꺼번에 처리되기 때문에, 개별 트랜잭션의 상태를 실시간으로 확인하기 어렵습니다. 이로", "score": 0.74385756, "raw_content": null}], "response_time": 0.77, "request_id": "aac96be9-8f50-4116-800d-7e9fddf40c8c"}', name='tavily_search', id='4073c440-d5f2-4525-945d-a2c5d57565d6', tool_call_id='call_ALcIDk5h03s11gjizAI75G1B'),
  AIMessage(content='모델 성능 모니터링은 머신러닝 모델의 성능과 동작을 지속적으로 추적하고 분석하는 과정으로, 데이터 과학자에게 모델의 가시성을 제공합니다. 이 과정은 모델이 변동성이 큰 데이터 세트에서 실행될 때 특히 중요하며, 자동화된 알림을 통해 이상치를 실시간으로 감지하여 문제 발생 전에 대응할 수 있게 합니다. 또한, 강력한 모니터링과 자동 교정 기능을 결합하면 문제 해결 시간을 단축하고 비즈니스 가치를 극대화할 수 있습니다.', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 123, 'prompt_tokens': 4825, 'total_tokens': 4948, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 4224}}, 'model_provider': 'openai', 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_3084892da3', 'id': 'chatcmpl-Db3kYvfWBhizW6JsF9iMQLWLvXQ4y', 'service_tier': 'default', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--019de8a9-9a93-77c0-9b41-cd88806eedd8-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 4825, 'output_tokens': 123, 'total_tokens': 4948, 'input_token_details': {'audio': 0, 'cache_read': 4224}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}

```

<br><br><br>

# Node Specifications

| 노드 | 내용 |
|------|------|
| **1.parse_all** | **입력** : PPT 파일 경로<br>**처리** : PPT 파일을 슬라이드 단위로 제목, 텍스트, 표, 이미지 파싱. LibreOffice, poppler pdftoppm을 사용해 PPT를 PNG로 변환.<br>**출력** : PPT 전체 슬라이드 파싱 데이터, 각종 변수 초기화 |

```
state 중 ... 
{
   'index': 3,
   'title': '모델 모니터링 아키텍처',
   'texts': ['두 가지 접근 방식\n배치(Batch) 모니터링 : 정해진 주기(일간, 주간 등)나 특정 이벤트 발생 시 모니터링\n실시간(Streaming) 모니터링 : ML 예측 서비스에서 발생한 데이터를 모니터링 시스템에 실시간으로 전송, 지속적으로 품질 지표를 계산 및 업데이트',
    '모델 모니터링 아키텍처', '3'],
   'tables': [[['항목', '배치 모니터링', '실시간 모니터링'],
     ['데이터 흐름', '정해진 시간마다', '스트리밍(실시간)'],
     ['적합한 환경', '일반 ML 서비스, 배치 처리', '실시간 예측 서비스'],
     ['속도', '느림 (지연 있음)', '빠름 (즉시 감지 가능)'],
     ['운영 비용', '낮음', '높음 (복잡한 인프라)'],
     ['한계', 'Abnormal 에 대한 지연된 탐지', 'Ground Truth 데이터 확인 지연 시 적용에 한계']]],
   'images': [],
   'snap': '/content/step1_output/slide_img-3.png'
}

...
```

<br><br>

| 노드 | 내용 |
|------|------|
| **2.gen_page** | **입력** : 현재 슬라이드 파싱 데이터<br>**처리** : 각 슬라이드의 제목, 텍스트, 표, 이미지, 스냅샷을 LLM(gpt-4o-mini)에 전달해 전체 내용을 왜곡 없이 정제한 설명문 생성.<br>**출력** : 정제된 슬라이드 설명문. |

```
[정제 text]
### 모델 성능 모니터링

#### 모델 모니터링
- **정의**: 프로덕션 환경에서 ML 모델의 성능 및 동작을 지속적으로 추적, 분석, 평가하는 프로세스.
- **필요성**: 모델은 배포 후에도 품질 저하, 데이터 문제, 사용 환경 변화 등의 위험에 노출됨.

#### 주요 리스크
- **데이터/컨셉 드리프트**: 시간이 지남에 따라 데이터의 분포가 변화하는 현상.
- **데이터 품질 문제**: 입력 데이터의 품질 저하로 인한 성능 저하.
- **적대적 공격**: 예를 들어, prompt injection과 같은 공격.
- **연결된 앞 단계의 모델 오류 전파**: 이전 단계에서 발생한 오류가 후속 모델에 영향을 미칠 수 있음.

#### 모니터링 목표
- **문제 조기 탐지**: 성능 저하나 오류를 신속하게 발견.
- **근본 원인 분석**: 문제의 원인을 파악하고 해결책을 모색.
- **모델 동작 이해 및 투명한 문서화**: 모델의 작동 방식을 명확히 하고 문서화하여 이해도를 높임.

#### 성과 지표
- **예측 수**: 1820개의 예측이 이루어짐.
- **이상 탐지 수**: 22개의 이상이 감지됨.

#### 시각화
- **예측 vs 실제**: 예측된 값과 실제 값의 비교 그래프 제공. 

이 내용은 모델 성능 모니터링의 중요성과 그 과정에서 고려해야 할 리스크 및 목표를 설명합니다.
```

<br><br>

| 노드 | 내용 |
|------|------|
| **3. tool_search** | **입력** : 정제된 슬라이드 설명문<br>**처리** : 슬라이드 내용에 실무적 예외 상황 (Edge Case)에 대한 내용 보완이 필요한지 tool binding된 LLM으로 판단. 보완이 필요하면 Tavily 검색 Tool Call, 검색했다면 검색 내용 정리, 검색 불필요시 다음 노드로 진행.<br>**출력** : 검색 결과 정리 내용 또는 '검색 필요 없음' |
| **4. tool_node** | **입력** : tool binding LLM의 tool call용 검색 쿼리를 포함한 인수.<br>**처리** : LangGraph Tavily ToolNode가 웹 검색 실행 후 결과 반환.<br>**출력** : Tavily 검색 결과. |


```
================================== Ai Message ==================================
Tool Calls:
  tavily_search (call_EaoAKTg4jRylIXmrcnfATblp)
 Call ID: call_EaoAKTg4jRylIXmrcnfATblp
  Args:
    query: 모델 성능 모니터링
    search_depth: advanced
================================= Tool Message =================================
Name: tavily_search

{
   "query": "모델 성능 모니터링", "follow_up_questions": null, "answer": null, "images": [],
   "results": [{"url": "https://docs.newrelic.com/kr/docs/mlops/get-started/intro-mlops/", 
      "title": "모델 성능 모니터링(MLOps) 소개 | New Relic Documentation", 
      "content": "여기에서 시작하기\n\n데이터 모니터링\n\n데이터 인사이트\n\n보안\n\n제품 업데이트\n\n관리 및 데이터\n\n# 모델 성능 모니터링(MLOps) 소개\n\n머신 러닝 작업은 품질을 높이고 관리 프로세스를 간소화하며 대규모 운영 환경에서 머신 러닝 모델의 배포를 자동화하도록 설계된 일련의 관행으로 구성됩니다.\n\n인공 지능과 머신 러닝에 투자하는 기업이 늘어나면서, 머신 러닝 모델을 개발하는 데이터 과학 팀과 이 모델을 지원하는 애플리케이션을 운영하는 데브옵스 팀 사이에 이해의 격차가 존재하게 되었습니다. 현재 기업의 15%만이 전체 활동에 AI를 구현합니다. 게다가 배포, 모니터링, 관리 및 거버넌스의 문제로 인해 운영에서 머신 러닝 모델의 75%가 전혀 사용되지 않고 있습니다. 궁극적으로 모델 작업을 하는 엔지니어와 데이터 과학자의 막대한 시간이 낭비되고, 투자에 대한 막대한 순손실이 발생하며, 머신 러닝 모델이 정량화 가능한 성장을 지원하는 경우 전반적인 신뢰 부족을 야기합니다.\n\n모델 성능 모니터링은 운영 중인 모델의 행동과 효과를 모니터링하여 데이터 과학자와 MLOP 실무자에게 머신 러닝 애플리케이션에 대한 가시성을 제공합니다. 이를 통해 데이터 팀은 지속적인 개발, 테스트 및 운영 모니터링 프로세스를 생성하는 데브옵스 팀과 직접적으로 협업할 수 있습니다.\n\n## 머신 러닝 모델을 모니터링하는 방법\n\n다음과 같은 몇 가지 옵션을 통해, 뉴렐릭 알림에서 모델 성능 모델링을 사용할 수 있습니다. [...] 다음과 같은 몇 가지 옵션을 통해, 뉴렐릭 알림에서 모델 성능 모델링을 사용할 수 있습니다.\n\nBring your own data (BYOD): 뉴렐릭이 권장하는 접근 방식입니다. 뉴렐릭의 ML 모델 성능 모니터링은 ML 모델이 운영에서 작동하는 방식에 대한 심층적인 옵저버빌리티를 제공합니다. BYOD(자체 데이터 사용)는 모든 환경(Python 스크립트, 컨테이너, Lambda 함수, SageMaker 등)에서 사용될 수 있으며, 모든 머신 러닝 프레임워크(Scikit-learn, Keras, Pytorch, Tensorflow, Jax 등)와 쉽게 통합될 수 있습니다. 자체 데이터를 사용하면 자체적인 ML 모델 텔레메트리를 뉴렐릭으로 가져와 ML 모델 데이터에서 가치를 실현할 수 있습니다. 단 몇 분 만에 모니터링하려는 다른 커스텀 메트릭과 함께 기능 분포, 통계 데이터 및 예측 분포를 확보할 수 있습니다. 뉴렐릭 문서에서 BYOD를 사용하는 방법을 자세히 알아보십시오.\n\nIntegrations: 뉴렐릭은 또한 Amazon SageMaker와 협력해, SageMaker에서 뉴렐릭으로 성능 메트릭 뷰를 제공하며 ML 엔지니어 및 데이터 과학 팀의 옵저버빌리티에 대한 액세스를 확장해줍니다. Amazon SageMaker 통합에 대해 자세히 알아보십시오.",
      "score": 0.91306627, "raw_content": null}], 
   "response_time": 1.16, "request_id": "be6b4c36-7e65-40b9-8d57-075417d53ca2"
}
================================== Ai Message ==================================

모델 성능 모니터링은 머신 러닝 모델의 성능과 동작을 지속적으로 추적하고 분석하는 과정으로, 데이터 품질 저하나 환경 변화 등의 리스크를 관리하는 데 중요합니다. 이를 통해 성능 저하를 조기에 발견하고, 문제의 근본 원인을 분석하여 해결책을 모색할 수 있습니다. New Relic의 문서에 따르면, 머신 러닝 모델의 운영을 지원하기 위해 데이터 과학자와 DevOps 팀 간의 협업이 필요하며, 다양한 통합 옵션을 통해 모델 성능을 효과적으로 모니터링할 수 있습니다.
```

<br><br>

| 노드 | 내용 |
|------|------|
| **5. gen_script_ctx** | **입력** : 정체된 슬라이드 설명문, 검색 결과 정리 내용<br>**처리** : 정제된 설명문과 검색 결과를 바탕으로 강의 스크립트 생성. 첫 슬라이드와 마지막 슬라이드에 인트로/아웃트로 추가. 이전 스크립트를 참고 맥락으로 제공해 중복 내용 제외. 각 스크립트 끝에 2문장으로 검색 결과를 자연스럽게 추가. 사용자 입력 prompt 참고해 스크립트 스타일 조정 가능.<br>**출력** : 스크립트 |

```
안녕하세요, 오늘은 모델 성능 모니터링에 대해 알아보겠습니다. 모델 모니터링은 프로덕션 환경에서 머신러닝 모델의 성능을 지속적으로 추적하고 평가하는 중요한 프로세스입니다. 모델은 배포 후에도 품질 저하와 데이터 문제 등 다양한 위험에 노출되기 때문에, 이를 관리하는 것이 필수적입니다. 

주요 리스크로는 데이터 드리프트, 데이터 품질 문제, 적대적 공격 등이 있으며, 이러한 문제를 조기에 탐지하고 근본 원인을 분석하는 것이 모니터링의 목표입니다. 예를 들어, 예측 수가 1820개인 상황에서 22개의 이상 탐지가 발생했다면, 이를 통해 모델의 동작을 이해하고 문서화할 수 있습니다. 

모델 성능 모니터링에 대한 슬라이드 내용은 이론적인 측면에 집중되어 있으며, 실제 구현 시 발생할 수 있는 예외 상황에 대한 설명이 부족합니다. 또한, 데이터 과학자들이 비효율적인 모니터링 솔루션을 개발하는 경향이 있어, 일관된 모니터링 시스템을 구축하는 것이 필요하다는 점도 강조됩니다.
```

<br><br>

| 노드        | 내용 |
|-----------|------|
| **6.tts** | **입력** : 스크립트<br>**처리** : OpenAI TTS (gpt-4o-mini-tts) 모델로 스크립트를 음성 mp3로 변환. 사용자 입력 prompt로 목소리와 톤 조정 가능.<br>**출력** : tts mp3 |


**mp3 link** : [![SoundCloud](https://img.shields.io/badge/SoundCloud-FF3300?style=for-the-badge&logo=soundcloud&logoColor=white)](https://soundcloud.com/pydlfit2hjqg/narration_1-mp3)

<br><br><br>

| 노드 | 내용 |
|------|------|
| **7.make_video** | **입력** : 스냅샷 이미지, tts mp3,<br>**처리** : ffmpeg로 스냅샷 이미지에 tts mp3를 오디오 트랙으로 합쳐 mp4 영상 생성.<br>**출력** : 영상 mp4 |

[![영상](https://img.youtube.com/vi/0SWb5iNzfkc/maxresdefault.jpg)](https://youtu.be/0SWb5iNzfkc)

<br><br>

| 노드 | 내용 |
|------|------|
| **8.add_subtitle** | **입력** : 스크립트, 영상 mp4<br>**처리** : 스크립트를 문장 단위로 분리하고 각 문장 별 문자 수 비례로 시간을 배분해 SRT 자막 파일 생성. ffmpeg subtitles 필터로 자막을 영상에 burn-in 방식으로 추가.<br>**출력** : 자막 영상 mp4 |

- 자막 예시
```
1
00:00:00,000 --> 00:00:04,631
안녕하세요, 오늘은 모델 성능 모니터링에 대해 알아보겠습니다.

2
00:00:04,631 --> 00:00:12,804
모델 모니터링은 프로덕션 환경에서 머신러닝 모델의 성능을 지속적으로 추적하고
평가하는 중요한 프로세스입니다.

3
00:00:12,804 --> 00:00:21,386
모델은 배포 후에도 품질 저하와 데이터 문제 등 다양한 위험에 노출되기
때문에, 이를 관리하는 것이 필수적입니다.

...
```

- 자막 적용된 영상

[![영상 제목](https://img.youtube.com/vi/xbdGqKdn39E/maxresdefault.jpg)](https://www.youtube.com/watch?v=xbdGqKdn39E)

| 노드 | 내용 |
|------|------|
| **9.acc_step** | **입력** : X<br>**처리** : 다음 슬라이드 준비, video 링크 저장 등 현재 분기 처리 마무리 작업 진행. 남은 슬라이드가 있는지 확인 후 다음 슬라이드 처리 진행 또는 작업 마치고 다음 노드로 진행.<br>**출력** : X |

<br><br>

| 노드 | 내용 |
|------|------|
| **10.concat_videos** | **입력** : 전체 자막 영상 mp4 경로 리스트<br>**처리** : ffmpeg concat demuxer로 모든 자막 영상 mp4를 재인코딩 없는 스트림 복사 방식으로 이어붙여 최종 영상 생성.<br>**출력** : 최종 영상 mp4 |

- 최종 영상

[![최종 영상](https://img.youtube.com/vi/JMil_iIqT28/maxresdefault.jpg)](https://youtu.be/JMil_iIqT28)






















<br><br><br>


# Special Requirements

1. 필요한 라이브러리 설치
``` python
pip install langchain-openai langchain-community python-pptx pillow gradio langchain-tavily tavily-python python-dotenv -q
```

2. 사전 설치 (Windows)
* ffmpeg      : https://www.gyan.dev/ffmpeg/builds/ 에서 "ffmpeg-release-essentials.zip" 다운로드 후 압축 해제, bin 폴더를 PATH에 추가
                 또는 터미널에서 ```winget install ffmpeg```
* LibreOffice : https://ko.libreoffice.org/download/libreoffice-stable/ 에서 Windows용 설치 파일 다운로드
                 "C:\Program Files\LibreOffice\program" PATH에 추가
* Poppler     : https://github.com/oschwartz10612/poppler-windows/releases 에서 최신 zip 다운로드 후 압축 해제, Library\bin 폴더를 PATH에 추가
* Noto Sans CJK KR (자막 폰트) : https://fonts.google.com/noto/specimen/Noto+Sans+KR 에서 폰트 다운로드 후 설치

(PATH 추가 방법 : 시스템 속성 → 환경 변수 → Path → 새로 만들기 → 해당 폴더 경로 입력)



# notes

함수 설명
1. split_sents()
스크립트 문장 단위로 분리
2. srt_time()
초 -> SRT 형식 시간으로 변환
3. convert_bullets_to_bold()
불릿 형식 -> SRT Bold 태그 형식
4. make_srt_from_script()
srt 파일 생성
5. generate_srt()
make_srt_from_script의 단순 버전.
문장 분리 없이 script 생성.
6. node_subtitle_video()
최종 자막 영상 생성기

문자 수에 비례해서 시간을 배분하는게 tts와 시간이 완벽히 맞아떨어지는가?
-> 살짝씩 밀려 안 맞아떨어짐

자막 burn-in : 자막이 영상과 한 몸이 된 상태
soft subtitle : 자막 트랙을 별도로 삽입해 켜고 끌 수 있는 방식.