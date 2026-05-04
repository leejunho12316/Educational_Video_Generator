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

<img src="./README_resources/LangGraph_Graph.png" width="300">

## 노드별 주요 기능

| 노드 | 내용 |
|------|------|
| **1. parse_all** | **입력** : PPT 파일 경로<br>**처리** : PPT 파일을 슬라이드 단위로 제목, 텍스트, 표, 이미지 파싱. LibreOffice, poppler pdftoppm을 사용해 PPT를 PNG로 변환.<br>**출력** : PPT 전체 슬라이드 파싱 데이터, 각종 변수 초기화 |

| 노드 | 내용 |
|------|------|
| **2. gen_page** | **입력** : 현재 슬라이드 파싱 데이터<br>**처리** : 각 슬라이드의 제목, 텍스트, 표, 이미지, 스냅샷을 LLM(gpt-4o-mini)에 전달해 전체 내용을 왜곡 없이 정제한 설명문 생성.<br>**출력** : 정제된 슬라이드 설명문. |

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

{"query": "모델 성능 모니터링", "follow_up_questions": null, "answer": null, "images": [], "results": [{"url": "https://docs.newrelic.com/kr/docs/mlops/get-started/intro-mlops/", "title": "모델 성능 모니터링(MLOps) 소개 | New Relic Documentation", "content": "여기에서 시작하기\n\n데이터 모니터링\n\n데이터 인사이트\n\n보안\n\n제품 업데이트\n\n관리 및 데이터\n\n# 모델 성능 모니터링(MLOps) 소개\n\n머신 러닝 작업은 품질을 높이고 관리 프로세스를 간소화하며 대규모 운영 환경에서 머신 러닝 모델의 배포를 자동화하도록 설계된 일련의 관행으로 구성됩니다.\n\n인공 지능과 머신 러닝에 투자하는 기업이 늘어나면서, 머신 러닝 모델을 개발하는 데이터 과학 팀과 이 모델을 지원하는 애플리케이션을 운영하는 데브옵스 팀 사이에 이해의 격차가 존재하게 되었습니다. 현재 기업의 15%만이 전체 활동에 AI를 구현합니다. 게다가 배포, 모니터링, 관리 및 거버넌스의 문제로 인해 운영에서 머신 러닝 모델의 75%가 전혀 사용되지 않고 있습니다. 궁극적으로 모델 작업을 하는 엔지니어와 데이터 과학자의 막대한 시간이 낭비되고, 투자에 대한 막대한 순손실이 발생하며, 머신 러닝 모델이 정량화 가능한 성장을 지원하는 경우 전반적인 신뢰 부족을 야기합니다.\n\n모델 성능 모니터링은 운영 중인 모델의 행동과 효과를 모니터링하여 데이터 과학자와 MLOP 실무자에게 머신 러닝 애플리케이션에 대한 가시성을 제공합니다. 이를 통해 데이터 팀은 지속적인 개발, 테스트 및 운영 모니터링 프로세스를 생성하는 데브옵스 팀과 직접적으로 협업할 수 있습니다.\n\n## 머신 러닝 모델을 모니터링하는 방법\n\n다음과 같은 몇 가지 옵션을 통해, 뉴렐릭 알림에서 모델 성능 모델링을 사용할 수 있습니다. [...] 다음과 같은 몇 가지 옵션을 통해, 뉴렐릭 알림에서 모델 성능 모델링을 사용할 수 있습니다.\n\nBring your own data (BYOD): 뉴렐릭이 권장하는 접근 방식입니다. 뉴렐릭의 ML 모델 성능 모니터링은 ML 모델이 운영에서 작동하는 방식에 대한 심층적인 옵저버빌리티를 제공합니다. BYOD(자체 데이터 사용)는 모든 환경(Python 스크립트, 컨테이너, Lambda 함수, SageMaker 등)에서 사용될 수 있으며, 모든 머신 러닝 프레임워크(Scikit-learn, Keras, Pytorch, Tensorflow, Jax 등)와 쉽게 통합될 수 있습니다. 자체 데이터를 사용하면 자체적인 ML 모델 텔레메트리를 뉴렐릭으로 가져와 ML 모델 데이터에서 가치를 실현할 수 있습니다. 단 몇 분 만에 모니터링하려는 다른 커스텀 메트릭과 함께 기능 분포, 통계 데이터 및 예측 분포를 확보할 수 있습니다. 뉴렐릭 문서에서 BYOD를 사용하는 방법을 자세히 알아보십시오.\n\nIntegrations: 뉴렐릭은 또한 Amazon SageMaker와 협력해, SageMaker에서 뉴렐릭으로 성능 메트릭 뷰를 제공하며 ML 엔지니어 및 데이터 과학 팀의 옵저버빌리티에 대한 액세스를 확장해줍니다. Amazon SageMaker 통합에 대해 자세히 알아보십시오.", "score": 0.91306627, "raw_content": null}], "response_time": 1.16, "request_id": "be6b4c36-7e65-40b9-8d57-075417d53ca2"}
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

| 노드         | 내용 |
|------------|------|
| **6. tts** | **입력** : 스크립트<br>**처리** : OpenAI TTS (gpt-4o-mini-tts) 모델로 스크립트를 음성 mp3로 변환. 사용자 입력 prompt로 목소리와 톤 조정 가능.<br>**출력** : tts mp3 |


- tts mp3

[![SoundCloud](https://img.shields.io/badge/SoundCloud-FF3300?style=for-the-badge&logo=soundcloud&logoColor=white)](https://soundcloud.com/pydlfit2hjqg/narration_1-mp3)

<br><br><br>

| 노드 | 내용 |
|------|------|
| **7. make_video** | **입력** : 스냅샷 이미지, tts mp3,<br>**처리** : ffmpeg로 스냅샷 이미지에 tts mp3를 오디오 트랙으로 합쳐 mp4 영상 생성.<br>**출력** : 영상 mp4 |

[![영상](https://img.youtube.com/vi/0SWb5iNzfkc/maxresdefault.jpg)](https://youtu.be/0SWb5iNzfkc)

<br><br>

| 노드 | 내용 |
|------|------|
| **8. add_subtitle** | **입력** : 스크립트, 영상 mp4<br>**처리** : 스크립트를 문장 단위로 분리하고 각 문장 별 문자 수 비례로 시간을 배분해 SRT 자막 파일 생성. ffmpeg subtitles 필터로 자막을 영상에 burn-in 방식으로 추가.<br>**출력** : 자막 영상 mp4 |

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

[![영상 제목](https://img.youtube.com/vi/0SWb5iNzfkc/maxresdefault.jpg)](https://youtu.be/0SWb5iNzfkc)

| 노드 | 내용 |
|------|------|
| **9. acc_step** | **입력** : X<br>**처리** : 다음 슬라이드 준비, video 링크 저장 등 현재 분기 처리 마무리 작업 진행. 남은 슬라이드가 있는지 확인 후 다음 슬라이드 처리 진행 또는 작업 마치고 다음 노드로 진행.<br>**출력** : X |

<br><br>

| 노드 | 내용 |
|------|------|
| **10. concat_videos** | **입력** : 전체 자막 영상 mp4 경로 리스트<br>**처리** : ffmpeg concat demuxer로 모든 자막 영상 mp4를 재인코딩 없는 스트림 복사 방식으로 이어붙여 최종 영상 생성.<br>**출력** : 최종 영상 mp4 |

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