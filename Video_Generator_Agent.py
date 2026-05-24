

# ### (3) import문 모음
import os, re, textwrap, subprocess, json, base64, mimetypes, shlex
from dotenv import load_dotenv
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, TypedDict, Any
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from openai import OpenAI

from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from typing import Annotated

from langgraph.graph import StateGraph, START, END

load_dotenv()

# ### (4) 상수 모음

# 모델
LLM_MODEL = "gpt-4o-mini"
TTS_MODEL = "gpt-4o-mini-tts"

llm = ChatOpenAI(model=LLM_MODEL, temperature=0.3)


 ## 2. 기본 함수들
# * 공백 제거 함수
def clean_text(s):
    return re.sub(r"\s+", " ", s).strip()

# * 긴 문자열을 문장 단위로 나누는 문장 분리기
def split_sents(t: str) -> List[str]:
    parts = re.split(r'([\.?!])', t)
    merged = []
    for i in range(0, len(parts)-1, 2):
        sent = (parts[i] + parts[i+1]).strip()
        if sent: merged.append(sent)
    if len(parts) % 2 == 1 and parts[-1].strip():
        merged.append(parts[-1].strip())
    return [s for s in merged if s]

# * 오디오 길이 계산
def ffprobe_duration(path: str) -> float:
    out = subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1", path]).decode().strip()
    return float(out)

# * 이미지를 base64로 변환
def img_to_data_url(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

# * 배경 이미지와 오디오 합쳐서 MP4 영상 만들기
def render_mp4(image_path: str, audio_path: str, out_mp4: str,
               width=1920, height=1080, ):

    dur = ffprobe_duration(audio_path)

    vf = (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
          f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"  )

    # FFmpeg 명령
    cmd = ["ffmpeg", "-y",
            "-loop", "1", "-i", image_path,   # 정지 이미지 입력
            "-i", audio_path,                 # 오디오 입력
            "-t", str(dur),                   # 길이 = 오디오 길이
            "-vf", vf,                        # 비디오 필터
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",        # 웹/브라우저 재생 친화
            out_mp4]
    subprocess.check_call(cmd)  # 외부 프로그램(FFmpeg)을 파이썬 프로세스에서 실행하고, 성공했는지 확인

# * ppt 슬라이드를 배경 이미지로 저장
# ppt를 pdf로 변환한 뒤 다시 이미지로 변환 (LibreOffice + Poppler 필요)
import tempfile

def export_slide_as_png(state: dict, dpi: int = 220) -> dict:
    work_dir = Path(state["work_dir"]).expanduser().resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    pptx = Path(state["pptx_path"]).expanduser().resolve()
    if not pptx.exists():
        raise FileNotFoundError(f"PPTX 없음: {pptx}")

    idx = int(state.get("slide_index", 0))  # 0-based
    page_no = idx + 1
    out_prefix = work_dir / "slide_img"

    # LibreOffice 프로필 충돌 방지용 임시 디렉토리
    lo_profile_dir = Path(tempfile.mkdtemp(prefix="lo_profile_"))
    lo_profile = lo_profile_dir.as_uri()

    def run_lo_convert(convert_to: str):
        cmd = [
            "soffice", "--headless", "--nologo", "--nofirststartwizard", "--norestore",
            f"-env:UserInstallation={lo_profile}",
            "--convert-to", convert_to,
            "--outdir", str(work_dir),
            str(pptx),
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    # --- A) PPTX → PNG ---
    before_png = set(work_dir.glob("*.png"))
    run_lo_convert("png:impress_png_Export")

    created_png = [p for p in work_dir.glob("*.png") if p not in before_png]
    candidate = None

    exact = [p for p in created_png if p.stem.endswith(f"-{page_no}")]
    if exact:
        candidate = max(exact, key=lambda p: p.stat().st_mtime)
    elif created_png:
        candidate = max(created_png, key=lambda p: p.stat().st_mtime)

    if candidate and candidate.exists():
        state["slide_image"] = str(candidate)
        return state

    # --- B) 폴백: PPTX → PDF → PNG ---
    before_pdf = set(work_dir.glob("*.pdf"))
    res_pdf = run_lo_convert("pdf:impress_pdf_Export")

    target_pdf = work_dir / f"{pptx.stem}.pdf"
    created_pdf = [p for p in work_dir.glob("*.pdf") if p not in before_pdf]

    if target_pdf.exists():
        pdf_path = target_pdf
    elif created_pdf:
        pdf_path = max(created_pdf, key=lambda p: p.stat().st_mtime)
    else:
        print("LibreOffice PPTX→PDF 변환 실패")
        print("stdout:", res_pdf.stdout)
        print("stderr:", res_pdf.stderr)
        raise RuntimeError("PPTX → PDF 변환 실패")

    ppm_cmd = [
        "pdftoppm",
        "-f", str(page_no), "-l", str(page_no),
        "-png", "-r", str(dpi),
        str(pdf_path),
        str(out_prefix)
    ]
    res2 = subprocess.run(ppm_cmd, capture_output=True, text=True)

    # pdftoppm은 Windows에서 6자리 zero-padding 사용 (예: slide_img-000001.png)
    png_path = Path(f"{out_prefix}-{page_no:06d}.png")
    if not png_path.exists():
        png_path = Path(f"{out_prefix}-{page_no}.png")
    if not png_path.exists():
        print("pdftoppm 변환 실패")
        print("stdout:", res2.stdout)
        print("stderr:", res2.stderr)
        raise RuntimeError("PDF → PNG 변환 실패")

    state["slide_image"] = str(png_path)
    return state

# * 영상 합치기 : 여러 영상 경로를 리스트로 입력 받아 합치기
def concat_videos_ffmpeg(video_paths: List[str], out_path: str, reencode: bool=False):
    list_path = out_path + ".txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for v in video_paths:
            f.write(f"file '{os.path.abspath(v)}'\n")
    if reencode:
        cmd = [
            "ffmpeg","-y","-safe","0","-f","concat","-i",list_path,
            "-vf","format=yuv420p",
            "-c:v","libx264","-preset","veryfast",
            "-c:a","aac","-b:a","192k",
            out_path
        ]
    else:
        cmd = ["ffmpeg","-y","-safe","0","-f","concat","-i",list_path,"-c","copy",out_path]
    subprocess.check_call(cmd)

# -----

 ## ** 3. LangGraph 노드 함수들 **

# State 정의 및 초기화
class State(TypedDict, total=False): # total=False는 TypedDict에서 모든 키를 선택(optional)으로 취급
    # 입력/기본
    pptx_path: str
    work_dir: str
    prompt: Dict

    # ppt 슬라이드 데이터
    slides: List[Dict[str, Any]] # [{index, title, texts, tables, images, snap, script}] 저장
    n_slides: int                # 전체 슬라이드 개수
    slide_index: int             # 현재 슬라이드 index

    #임시 (반복 내부 사용)
    cur_search_context: str
    cur_page_content: str
    cur_script: str
    cur_audio: str
    cur_video: str
    cur_video_subtitled: str

    # video 산출물
    video_paths: List[str] # 개별 영상 리스트
    final_video : str      # 합체된 최종 영상 주소

    # <<tavily ToolNode는 내부적으로 state['messages'] 를 읽고 씀. 검색 기능 추가용 message 저장 list>
    messages: Annotated[list, add_messages]


def node_parse_all(state: State) -> State:

    print('1. ppt 내용 전체 파싱')
    '반복문으로 모든 슬라이드 텍스트/표/이미지 + 스냅샷 수집 → state["slides"] 적재'

    # 기본 사항 초기화
    pres = Presentation(state["pptx_path"])
    work_dir = state["work_dir"]
    media_dir = os.path.join(work_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    slides_out: List[Dict[str, Any]] = []

    # 반복문으로 각 슬라이드 마다 텍스트/표/이미지 추출
    for idx, slide in enumerate(pres.slides, start=1):

        # 1. 제목 추출
        title_shape = slide.shapes.title
        title = title_shape.text if title_shape else "제목 없음"

        # 2. 텍스트/표/이미지 추출
        texts, tables, images = [],[],[]

        for i, sh in enumerate(slide.shapes):
            if sh.has_text_frame:
                txt = "\n".join(p.text for p in sh.text_frame.paragraphs)
                texts.append(txt)
            if sh.shape_type == MSO_SHAPE_TYPE.TABLE:
                tbl = [[clean_text(c.text) for c in r.cells] for r in sh.table.rows]
                tables.append(tbl)
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                ext = sh.image.ext
                media_dir = os.path.join(state["work_dir"], "media")
                path = os.path.join(media_dir, f"{os.path.splitext(os.path.basename(state['pptx_path']))[0]}_slide{idx}_{i}.{ext}")
                images.append(path)
                try:
                    with open(path, "wb") as f: f.write(sh.image.blob)
                    print(f"path 위치: {path}")
                except Exception as e:
                    print(f"ppt 정보 분해 중 오류 발생: {e}")

        # 3. 스냅샷 추출(export_slide_as_png 사용)
        tmp_state = {"pptx_path": state["pptx_path"], "work_dir": work_dir, "slide_index": idx-1}
        snap_state = export_slide_as_png(tmp_state)
        snap = snap_state["slide_image"]

        # 4. 결과물 취합
        slides_out.append({
            "index": idx,
            "title": title,
            "texts": texts,
            "tables": tables,
            "images": images,
            "snap": snap,
            'script' : ''
        })

    # ppt parsing 결과물 저장
    state["slides"] = slides_out
    state["n_slides"] = len(slides_out)
    state['slide_index'] = 0

    # 그 외 모든 변수 초기화
    state['cur_search_context'], state['cur_page_content'], state['cur_script'], state['cur_audio'], state['cur_video'], state['cur_video_subtitled'] = '','','','','',''
    state['video_paths'], state['final_video'] = [],  ''
    state['messages'] = []

    return state

def node_generate_text(state : State)->State:

    print('2. parsing 데이터 텍스트 정제')
    'slides의 slide_index 번째 dictionary 가져와 그 안의 title, texts, tables, images, snap 사용go 전체 설명문 작성'

    # 현재 처리중인 slide_index의 파싱 결과 가져오기
    cur_index = state['slide_index']
    slide = state['slides'][cur_index]

    # 현재 slide 파싱 결과의 요소들 (제목, 텍스트, 테이블, 이미지, 스냅 이미지) 가져오기
    title = slide.get('title', '')
    texts = slide.get('texts', [])
    tables = slide.get("tables", [])
    table_snip = ""
    if tables:
      try:
          table_snip = "\n".join([" | ".join(map(str, r)) for r in tables[0][:6]])
      except Exception:
          table_snip = str(tables[0][:6])

    images = list(slide.get("images", []) or [])

    slide_img = slide.get("snap")
    if slide_img:
      if isinstance(slide_img, list):
          if slide_img and slide_img[0] not in images:
              images.insert(0, slide_img[0])
      else:
          if slide_img not in images:
                images.insert(0, slide_img)

    # system message, user message 구성
    sys_msg = f'''
    # 역할
    당신은 PPT 내용 정리 전문가입니다.
    아래는 PPT로부터 추출한 전체 객체들입니다. 입력된 객체 내용을 사용해 전체 내용을 작성해주세요.

    # 규칙
    1. 모든 내용을 단 하나도 빠트리지 말고 전부 사용할 것.
    2. 왜곡, 과장하거나 상상해서 적지 말 것.
    3. 있는 그대로 모든 것을 작성할 것.
    4. 고유명사를 임의로 다른 단어로 변경해 작성하지 말 것.
    5. ppt 내용 외의 출력은 제한할 것.
    6. 입력된 이미지를 충분히 설명할 것..
    '''

    user_text = []
    user_text.append(f"[제목]\n{title if title else '[제목 없음]'}")
    user_text.append(f"[텍스트]\n{texts if texts else '[없음]'}")
    user_text.append(f"[표]\n{table_snip if table_snip else '[없음]'}")
    user_text = "\n\n".join(user_text)
    human_msg = [{"type":"text","text":user_text}]

    # message에 image 추가
    for image in images:
        try:
              data_url = img_to_data_url(image)
              human_msg.append({"type": "image_url", "image_url": {"url": data_url}})
        except Exception:
          pass

    # LLM 호출 후 결과 저장
    result = llm.invoke([
      SystemMessage(content = sys_msg),
      HumanMessage(content = human_msg)
    ])

    state['cur_page_content'] = result.content

    state['messages'] = [AIMessage(content = f"[정제 text]\n{result.content}\n[Tool검색]")]

    return state


from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import tool
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode
import arxiv


tavily_tool = TavilySearch(max_results=3)
                          # description = "최신 뉴스, 실무 적용 사례, 구현 예시, 현장 트러블슈팅을 찾을 때 사용")

@tool
def arxiv_tool(query: str) -> str:
    """학술 논문, 연구 결과, 알고리즘의 이론적 근거를 찾을 때 사용"""
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=1)

    results = []
    for paper in client.results(search):
        results.append(
            f"제목: {paper.title}\n"
            f"연도: {paper.published.year}\n"
            f"요약: {paper.summary}\n"
            f"URL: {paper.entry_id}"
        )
    result_text = "\n\n".join(results) if results else "결과 없음"
    print('paper_info : ', result_text)
    return result_text

wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=2000),)
                            #  description = "기술 용어 정의, 개념 배경지식, 역사적 맥락을 찾을 때 사용")

tool_list = [tavily_tool, arxiv_tool, wiki_tool]
tool_node = ToolNode(tool_list, handle_tool_errors=True)

tool_llm = ChatOpenAI(model='gpt-5.5', temperature=0.3)
llm_with_tools = tool_llm.bind_tools(tool_list)

def tool_search(state : State):

    print('3. Tool 사용 여부 검색 & 실행')
    '정제 텍스트로부터 보완점 Tavily Search Tool Node 사용해 보완'
    '특정 node에서 tool 실행 후 다시 돌아와 특성 node를 다시 실행하는 함수 작동 테스트는 단일 함수로는 안되고 Graph를 만들어 테스트해야 함.'

    # 프롬프트 작성
    sys_msg = """
    #역할
    당신은 검색 전문가입니다. 입력은 현재 PPT 슬라이드의 전체 내용을 빠짐없이 적은 것입니다.
    이를 읽고 도구 선택 기준에 맞으면 도구를 사용해 검색해주세요.
    사용할 수 있는 도구는 다음과 같습니다. : tavily_search, arxiv_search
    구체적인 내용 없이 전체 내용이 짧은 경우 표지, 목차, 섹션 구분 등에 해당합니다.

    # 도구 선택 기준
    1. tavily_search : 특정 서비스와 제품에 대한 정보가 필요할 때
    특정 제품/서비스가 명시되어 있고 그에 대한 구체적인 정보(기능, 성능, 비교 등) 내용을 담은 슬라이드일 때 해당 제품에 대한 최신 정보와 동향을 검색.

    - tavily 쿼리 지침
    쿼리는 핵심 키워드만 사용해 간결하게 작성하세요.
    슬라이드에 나와 있는 핵심 제품 한 가지에 대해서만 검색하세요.
    검색어는 3~5단어면 충분합니다.

    검색 필요 예시)
    MAAL (Multilingual Adaptive Augmentation Language-model) 한국어에 강한 언어 생성 모델 MAAL을 기반으로 On-premise LLM 솔루션을 제공합니다. 다양한 파라미터 수의 모델(8B-70B)을 기반으로 고객의 니즈에 맞는 모델을 지원합니다... On-premise용으로는 성능이 뛰어나며 범용적으로 사용하기 좋은 MAAL-albatross(70B)를 권장하고 있습니다. -> MAAL 관련 검색
    Agados UI, Flow Design & Visibility Technologies Structure of this presentation Application을 위한 Architecture - SW Package를 위한 Smart Architecture - Hybrid Architecture Overview - 타 시스템과의 Interface... -> Agados 관련 검색

    2. arxiv_search : 연구에 대한 구체적인 성능 내용이 필요할 때
    연구, 성능 그래프, 성능 표, 논문 인용 표기 등이 명시되어 있을 때 그와 관련한 논문 검색.

    - arxiv 쿼리 지침
    슬라이드에 나와 있는 핵심적인 것 단 한가지에 대해서만 검색하세요.

    검색 필요 예시)
    - "REPLUG: Retrieval-Augmented Black-Box Language Models, NAACL24'", "Dense Passage Retrieval for Open-Domain Question Answering, EMNLP20'" -> 논문 검색
    - 마크다운 형식으로 전환된 그래프의 성능, 메트릭 표 -> 논문 검색
    - 특정 모델의 벤치마크 점수가 수치로 제시된 경우 예) "MAAL 70B: 9.06 / GPT-4o: 9.59" 처럼 모델별 점수 비교표가 포함된 슬라이드 -> 논문 검색
    - LogicKor, KoBEST, MMLU 등 평가 지표명이 명시된 경우

    3. 검색이 필요 없는 경우
    그 외 아래의 경우에 해당할 경우 '검색 필요 없음'과 그 이유를 출력하세요
    - 형식적 내용 : 표지, 개요, 목차, 섹션 구분, 마지막 페이지(Q&A, 감사합니다) 등의 슬라이드로 판단되는 경우
    - 소개 : 학습 목표, 강사 소개, 참고문헌 목록, 레퍼런스 목록 등을 소개하는 내용인 경우.
    - 그 외 어떠한 도구 선택 기준의 경우에도 해당하지 않는 경우.

    검색 불필요 예시)
    - 제목: 제목 없음\n- Chapter 2. 오픈소스 컨설팅의 On-premise LLM 솔루션\n- MAAL (Multilingual Adaptive Augmentation Language-model) MAAL 기반 On-premise 패키지\n  - 챗봇\n  - Chatplay\n  - LLM Task UI\n- 표: 없음 -> 목차 슬라이드
    Biz. Application을 위한 디자이너/재조정기\n‘아가도스’는 귀사의 SW Application내에서 Configure Tool의 역할 수행\n19\nⒸ 2014 agados All rights reserved. -> 섹션 구분
    제목: Jamcracker 소개 시작\n\nCloud Management Platform & Cloud Service Brokerage\n\n- CLOUD SERVICES BROKERAGE\n- CLOUD GOVERNANCE\n- MICROSOFT CSP ENABLEMENT\n- HYBRID CLOUD MANAGEMENT\n- Microsoft Cloud Solution Provider\n- OSC ASIA GROUP LIMITED\n- @ OSC Korea & OSC Asia Group jerry@osckorea.com jerry@oscasia.net +82 10 9196 1416 -> 목차 슬라이드

    # 규칙
    - 검색 시 하나의 도구만 사용하세요.
    - 대화 로그를 보았을 때 이미 검색을 진행했다면 추가 검색을 하지 말고 검색 결과를 전체 정리해주세요.
    - 검색 결과 정리시 핵심 내용을 정리해 작성해주세요.
    - 검색 결과 요약 시 검색 결과를 제외한 다른 어떠한 출력도 하지 마세요.
    """

    # human_msg = "[슬라이드 내용]" + "\n\n".join([message.content for message in state['messages']])
    human_msg = "[슬라이드 내용]\n" + state.get("cur_page_content", "") + "\n[대화 로그]"+ "\n\n".join([message.content for message in state['messages']])

    # LLM 호출
    result = llm_with_tools.invoke([SystemMessage(content = sys_msg), HumanMessage(content = human_msg)])

    return {'cur_search_context' : result.content,
          'messages' : [result]}

# 툴 사용 확인용 conditional edge 함수
def is_tool_needed(state : State):
  if state['messages'][-1].tool_calls:
    return 'tool_call'
  return 'no_tool_call'



def node_generate_script(state: State) -> State:

    print('4. 스크립트 생성')
    '정제 텍스트와 검색결과 사용해 스크립트 생성/저장'

    # 1. 정보 불러오기
    # 기본 정보
    work_dir = state.get("work_dir", "./")
    prompt = state.get("prompt", "")
    style_prompt = prompt.get('style', '예시와 핵심 요점 중심')

    # 정제 텍스트, 검색 결과
    cur_page_content = state.get("cur_page_content", "검색 결과 없음")
    cur_search_context = state.get('cur_search_context', '슬라이드 컨텐츠 없음')

    slide_index = state.get('slide_index')
    n_slides = state.get('n_slides')


    # 2. 프롬프트 구성

    # 인사말 : 첫 번째와 마지막 슬라이드에만 인사말 추가하고 그 외에는 금지.
    introduction = "# 인사말\n인사말을 추가하지 마세요. '오늘은~' 이나 '이번 시간에는'와 같은 시작 말도 추가하지 말고 바로 본론으로 들어가세요."

    if slide_index == 0:
      titles = ', '.join([s.get('title') for s in state['slides']])
      introduction = f"# 인사말\n현재 슬라이드는 첫 번째 슬라이드입니다. 무엇을 배울 것인지를 주제를 설명하는 인사말을 추가해주세요. 전체 슬라이드 제목은 다음과 같습니다 : {titles}"

    if slide_index + 1 == n_slides:
      titles = ', '.join([s.get('title') for s in state['slides']])
      introduction = f"# 아웃트로\n현재 슬라이드는 마지막 슬라이드입니다. 지금까지 배운 것을 정리하는 마무리 멘트를 추가해주세요. 전체 슬라이드 제목은 다음과 같습니다 : {titles}"

    # 이전 스크립트 : 현재 스크립트 생성 시 이전 스크립트에 이미 설명한 내용 제외용
    prev_slides = state['slides'][max(0, slide_index-2):slide_index]
    if prev_slides:
      prev_scripts = "\n".join([s.get('script', '') for s in prev_slides])
    else:
      prev_scripts = "이전 스크립트 없음"

    # 프롬프트
    sys_msg = f"""
# 역할
당신은 전문 발표 대본 작성 에이전트입니다.
제공된 현재 슬라이드 컨텐츠 내용을 바탕으로 20초 분량의 자연스러운 발표 스크립트를 작성해 주세요.
제공된 슬라이드 컨텐츠에는 제목, 텍스트, 표, 이미지 데이터가 포함되어 있습니다. 포함된 내용을 연관지어 작성해주세요.
단, 이전 스크립트에서 설명한 내용은 제외하세요.

# 검색 결과
스크립트 마지막에는 검색 결과에 대한 내용을 2 문장 추가해주세요.
단, 검색 결과라는 것을 명시하지 말고 스크립트에 자연스럽게 추가해주세요.

# 규칙
1. 불필요한 추측이나 과장 금지.
2. 스크립트 외의 설명과 출력 금지.
3. ppt 디자인, 스타일 등 주제와 무관한 내용 언급 금지.
4. 발표 스크립트의 마지막 부분에는 항상 검색결과에 대한 내용을 2 문장으로 추가.
5. 이전 스크립트에서 설명한 내용 포함 금지

{introduction}

"""

    human_msg = f"""
# 현재 슬라이드 컨텐츠
{cur_page_content}

# 이전 스크립트
{prev_scripts}

# 검색결과
{cur_search_context}

# 스타일
{style_prompt}
"""

    result = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=human_msg)])

    # 3. 결과 저장

    # State에 저장
    state["cur_script"] = result.content                       # 현재 분기 처리용 cur_script
    state['slides'][slide_index]['script'] = result.content    # 스크립트 생성 시 맥락 파악용 영구 저장 slides dictionary

    # 파일에 저장
    file_path = os.path.join(work_dir, f"script_{slide_index+1}.txt")

    try:
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(state["cur_script"])
        print(f"스크립트 저장 완료: {file_path}")
    except UnicodeEncodeError:
        print(f"경고: {file_path} 인코딩 중 일부 문자가 치환되었습니다.")
        with open(file_path, "w", encoding="utf-8", errors="replace") as f: # 실패 시 에러 문자를 대체하여 강제 저장
            f.write(state["cur_script"])
    except Exception as e:
        print(f"스크립트 파일 저장 중 오류 발생: {e}")


    return state

def node_tts(state: State) -> State:

    print('5. 오디오 생성')
    '스크립트를 기반으로 tts 모델 사용해 오디오 생성'

    client = OpenAI()

    # 1. 정보 불러오기
    script = state.get("cur_script", "")
    prompt = state.get("prompt", {})
    voice_prompt = prompt.get("voice", "alloy")
    tone_prompt = prompt.get('tone', '친절하고 명료한 강의 톤')

    work_dir = state.get("work_dir",'./')
    slide_index = state.get('slide_index')

    # 2. 오디오 생성
    resp = client.audio.speech.create(
        model=TTS_MODEL,
        voice=voice_prompt,
        instructions = tone_prompt,
        input=script
    )

    # 3. 파일 저장
    mp3_path = os.path.join(work_dir, f"narration_{slide_index+1}.mp3")

    try:
        with open(mp3_path, "wb") as f:
            f.write(resp.content)
        print(f"파일 저장 완료: {mp3_path}")
        try:
            duration = ffprobe_duration(mp3_path)
            print(f"음성 변환 파일 길이: MP3 길이({duration} sec)")
        except Exception as e:
            print(f"음성 변환 길이 측정 중 오류 발생: {e}")
    except Exception as e:
        print(f"음성 변환 파일 저장 중 오류 발생: {e}")

    return {'cur_audio' : mp3_path}

def node_make_video(state: State) -> State:

    print('6. 비디오 생성')
    '슬라이드 이미지와 음성을 합쳐 mp4 영상 생성'

    # 1. 정보 불러오기
    work_dir = state.get("work_dir", "./")

    #현재 슬라이드
    slide_index = state['slide_index']
    slide = state['slides'][slide_index]

    #현재 슬라이드의 snap image, audio
    in_png = slide.get("snap", '')
    in_mp3 = state.get("cur_audio")

    # 2. 저장 경로 설정
    file_name = f"slide{slide_index+1}_lecture.mp4"
    out_mp4 = os.path.join(work_dir, file_name)

    # 3. 렌더링
    try:
        render_mp4(in_png, in_mp3, out_mp4)
        print(f"영상 제작 완료: {out_mp4}")
    except Exception as e:
        print(f"비디오 렌더링 중 오류 발생: {e}")
        return state

    # 4. 저장
    state["cur_video"] = out_mp4

    return state

# ### (3) 자막 제작 & 적용
# #### 함수 준비
def srt_time(seconds: float) -> str:
    """초 단위 시간을 SRT 시간 형식으로 변환합니다. 예) 12.345 -> 00:00:12,345"""
    if seconds < 0:
        seconds = 0

    ms = int(round((seconds - int(seconds)) * 1000))
    total = int(seconds)

    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60

    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def make_srt_from_script(script: str, srt_path: str, duration: float):
    """강의 스크립트를 문장 단위로 나누고, 전체 영상 길이에 맞춰 SRT 자막 파일을 생성합니다."""

    # 1. 스크립트 전처리
    script = clean_text(script)

    # 2. 스크립트 문장 단위로 분리
    sentences = split_sents(script)
    if not sentences:
        sentences = [script]
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        raise ValueError("자막으로 만들 스크립트가 비어 있습니다.")


    # 3. 각 문장 별 자막 길이 계산해 완성된 자막 파일 생성하기
    # 변수 초기화
    cur = 0.0
    lines = []

    # 전체 문장 길이 계산
    total_chars = sum(len(s) for s in sentences)

    for i, sent in enumerate(sentences, start=1):

        # 각 문장 길이 / 전체 문장 길이 계산
        seg_dur = duration * (len(sent) / total_chars)
        seg_dur = max(seg_dur, 1.2)

        # 자막의 시작, 끝 계산
        start = cur
        end = min(cur + seg_dur, duration)

        if i == len(sentences):
            end = duration

        # 지정한 너비 width에 맞게 줄 바꿈 하기 (textwrap : python 표준 라이브러리)
        wrapped = "\n".join(
            textwrap.wrap(
                sent,
                width=42,
                break_long_words=False,
                break_on_hyphens=False
            )
        )

        # 저장
        """ 예시
        5
        00:00:22,686 --> 00:00:30,437
        주요 리스크로는 데이터 드리프트, 데이터 품질 문제, 적대적 공격, 그리고
        모델 오류 전파가 있습니다.
        """
        lines.append(str(i))
        lines.append(f"{srt_time(start)} --> {srt_time(end)}")
        lines.append(wrapped)
        lines.append("")

        cur = end

        if cur >= duration:
            break

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def apply_subtitle(in_mp4: str, srt_path: str, out_mp4: str):
  """영상과 자막 파일을 입력받아 burn-in 방식으로 자막을 적용합니다"""

  srt_path_fwd = srt_path.replace("\\", "/")
  vf = (
      f"subtitles={srt_path_fwd}:"
      "force_style='"
      "FontName=Noto Sans CJK KR,"
      "FontSize=18,"
      "PrimaryColour=&H00FFFFFF,"           # 글자색
      "OutlineColour=&H50000000,"           # 배경색 : 반투명 검정
      "BorderStyle=3,"                      # BoarderStyle=3 : 배경 박스
      "Outline=1,Shadow=0,"
      "Alignment=2,MarginV=30"
      "'"
  )
  cmd = ["ffmpeg", "-y", "-i", in_mp4, "-vf", vf,
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
          "-c:a", "copy", "-pix_fmt", "yuv420p", out_mp4]
  subprocess.check_call(cmd)


def node_subtitle(state : State) -> State:
  print('7. 자막 생성 & 적용')

  # 1. 정보 불러오기
  slide_index = state.get('slide_index')
  work_dir = state.get('work_dir') or './'

  srt_path = os.path.join(work_dir, f"slide{slide_index+1}_subtitle.srt")
  out_mp4 = os.path.join(work_dir, f"slide{slide_index+1}_lecture_subtitled.mp4")

  cur_script = state.get('cur_script') or 'no script'
  cur_video = state.get('cur_video') or 'no video'

  duration = ffprobe_duration(cur_video)            # 비디오 전체 길이

  # 2. 자막 만들기
  make_srt_from_script(cur_script, srt_path, duration)

  # 3. 자막 적용하기
  # burn in이 아닌 soft subtitle 방식으로 처리 속도 증가.
  apply_subtitle(cur_video, srt_path, out_mp4)

  return {'cur_video_subtitled' : out_mp4}


def acc_step(state : State):

  print('7. 반복 & 종료 분기 node')
  '전체 과정을 반복할지 종료하고 마지막 영상 만들지 확인하는 분기 node'

  # 1. 전체 video list에 현재 video 추가
  state['video_paths'].append(state['cur_video_subtitled'])

  # 2. 처리할 slide index 증가
  state['slide_index'] = state['slide_index'] + 1

  return state

def acc_step_func(state : State):

  print('8. 반복 & 종료 결정')

  slide_index = state['slide_index']
  n_slides = state['n_slides']

  if slide_index < n_slides:
    return 'CONTINUE'
  return 'END'

# * 영상 합치기
#     * concat_videos_ffmpeg 사용
def concat_videos(state : State):

    print('9. 최종 영상 제작')
    '영상 합치기 - concat_videos_ffmpeg 사용'

    work_dir = state['work_dir']
    out_path = os.path.join(work_dir, 'final.mp4')

    video_paths = state['video_paths']

    concat_videos_ffmpeg(video_paths, out_path)

    return {'final_video' : out_path}

 ### * Agent 만들기 : 그래프로 엮기


builder = StateGraph(State)

builder.add_node('parse_all', node_parse_all)
builder.add_node('gen_page', node_generate_text)
builder.add_node('tool_search', tool_search)
builder.add_node('tool_node', tool_node)
builder.add_node('gen_script_ctx', node_generate_script)
builder.add_node('tts', node_tts)
builder.add_node('make_video', node_make_video)
builder.add_node('acc_step', acc_step)
builder.add_node('concat_videos', concat_videos)
builder.add_node('add_subtitle', node_subtitle)

builder.add_edge(START, 'parse_all')
builder.add_edge('parse_all', 'gen_page')
builder.add_edge('gen_page', 'tool_search')
builder.add_conditional_edges('tool_search', is_tool_needed,
                              {'tool_call' : 'tool_node', 'no_tool_call' : 'gen_script_ctx'})
builder.add_edge('tool_node', 'tool_search')
builder.add_edge('gen_script_ctx', 'tts')
builder.add_edge('tts', 'make_video')
builder.add_edge('make_video', 'add_subtitle')
builder.add_edge('add_subtitle', 'acc_step')

builder.add_conditional_edges('acc_step', acc_step_func,
                              {'CONTINUE' : 'gen_page', 'END' : 'concat_videos'})
builder.add_edge('concat_videos', END)

graph = builder.compile()

# 외부 실행용 함수
def run(pptx_path: str, prompt: dict = None):
    ppt_name = Path(pptx_path).stem
    ppt_name = re.sub(r'[^\w\-]', '_', ppt_name)  # 공백·쉼표 등 특수문자 → _
    work_dir = f"./video_outputs/{ppt_name}"
    media_dir = f"{work_dir}/media"

    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)

    if prompt is None:
        prompt = {
            "voice": "alloy",
            "tone": "친절하고 명료한 강의 톤",
            "style": "예시와 핵심 요점 중심"
        }

    result = graph.invoke({
        "pptx_path": pptx_path,
        "work_dir": work_dir,
        "prompt": prompt,
    })

    return result

# 현재 .py 직접 실행시에만 동작
if __name__ == "__main__":
    PPTX_PATH = "./input.pptx"  # 실행할 PPT 파일 경로
    result = run(pptx_path=PPTX_PATH)
    print("완료:", result.get("final_video"))
