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

| 노드 | 내용 |
|------|------|
| **3. tool_search** | **입력** : 정제된 슬라이드 설명문<br>**처리** : 슬라이드 내용에 실무적 예외 상황 (Edge Case)에 대한 내용 보완이 필요한지 tool binding된 LLM으로 판단. 보완이 필요하면 Tavily 검색 Tool Call, 검색했다면 검색 내용 정리, 검색 불필요시 다음 노드로 진행.<br>**출력** : 검색 결과 정리 내용 또는 '검색 필요 없음' |

| 노드 | 내용 |
|------|------|
| **4. tool_node** | **입력** : tool binding LLM의 tool call용 검색 쿼리를 포함한 인수.<br>**처리** : LangGraph Tavily ToolNode가 웹 검색 실행 후 결과 반환.<br>**출력** : Tavily 검색 결과. |

| 노드 | 내용 |
|------|------|
| **5. gen_script_ctx** | **입력** : 정체된 슬라이드 설명문, 검색 결과 정리 내용<br>**처리** : 정제된 설명문과 검색 결과를 바탕으로 강의 스크립트 생성. 첫 슬라이드와 마지막 슬라이드에 인트로/아웃트로 추가. 이전 스크립트를 참고 맥락으로 제공해 중복 내용 제외. 각 스크립트 끝에 2문장으로 검색 결과를 자연스럽게 추가. 사용자 입력 prompt 참고해 스크립트 스타일 조정 가능.<br>**출력** : 스크립트 |

| 노드 | 내용 |
|------|------|
| **6. ttx** | **입력** : 스크립트<br>**처리** : OpenAI TTS (gpt-4o-mini-tts) 모델로 스크립트를 음성 mp3로 변환. 사용자 입력 prompt로 목소리와 톤 조정 가능.<br>**출력** : tts mp3 |

| 노드 | 내용 |
|------|------|
| **7. make_video** | **입력** : 스냅샷 이미지, tts mp3,<br>**처리** : ffmpeg로 스냅샷 이미지에 tts mp3를 오디오 트랙으로 합쳐 mp4 영상 생성.<br>**출력** : 영상 mp4 |

| 노드 | 내용 |
|------|------|
| **8. add_subtitle** | **입력** : 스크립트, 영상 mp4<br>**처리** : 스크립트를 문장 단위로 분리하고 각 문장 별 문자 수 비례로 시간을 배분해 SRT 자막 파일 생성. ffmpeg subtitles 필터로 자막을 영상에 burn-in 방식으로 추가.<br>**출력** : 자막 영상 mp4 |

<video src="./step1_output/slide1_lecture.mp4" controls autoplay loop muted width="600">
</video>

[slide1_lecture.mp4](step1_output/slide1_lecture.mp4)

| 노드 | 내용 |
|------|------|
| **9. acc_step** | **입력** : X<br>**처리** : 다음 슬라이드 준비, video 링크 저장 등 현재 분기 처리 마무리 작업 진행. 남은 슬라이드가 있는지 확인 후 다음 슬라이드 처리 진행 또는 작업 마치고 다음 노드로 진행.<br>**출력** : X |

| 노드 | 내용 |
|------|------|
| **10. concat_videos** | **입력** : 전체 자막 영상 mp4 경로 리스트<br>**처리** : ffmpeg concat demuxer로 모든 자막 영상 mp4를 재인코딩 없는 스트림 복사 방식으로 이어붙여 최종 영상 생성.<br>**출력** : 최종 영상 mp4 |





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