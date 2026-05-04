from Video_Generator_Agent import run

# ppt 경로, prompt 설정
PPTX_PATH = "./ppt_examples/sample2.pptx"  # 실행할 PPT 파일 경로
prompt={
    "voice": "alloy",
    "tone": "명확하고 연설하는 듯한 강렬한 톤",
    "style": "장황한 스타일"
}

# 실행
result = run(pptx_path=PPTX_PATH)

print("최종 영상 경로:", result.get("final_video"))