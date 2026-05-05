import json
from Video_Generator_Agent import run

# ppt 경로, prompt 설정
PPTX_PATH = "./ppt_examples/01ragpublish-240714071933-12313109.pptx"  # 실행할 PPT 파일 경로
prompt={
    "voice": "nova",
    "tone": "명확하고 귀여움이 넘치는 톤",
    "style": "핵심에 집중하고 예시를 포함하는 깔끔하고 명확한 스타일"
}

# 실행
result = run(pptx_path=PPTX_PATH, prompt=prompt)

print("최종 영상 경로:", result.get("final_video"))

# 최종 state 파일 저장
from pathlib import Path
ppt_name = Path(PPTX_PATH).stem
STATE_OUTPUT = f"./video_outputs/{ppt_name}/final_state.json"
with open(STATE_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print("State 저장 완료:", STATE_OUTPUT)

print(result)