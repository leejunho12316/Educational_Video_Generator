# Educational_Video_Generator
교육 영상 제작 Tool Calling Multi Agent System


notes

1. split_sents()
스크립트 문장 단위로 분리

2. srt_time()
초 -> SRT 형식 시간으로 변환

3. convert_bullets_to_bold()
불릿 형식 -> SRT Bold 태그 형식

4. make_srt_from_script()
srt 파일 생성
-------------------------------------------------------------------------------------------------
5. generate_srt()
make_srt_from_script의 단순 버전.
문장 분리 없이 script 생성.

6. node_subtitle_video()
최종 자막 영상 생성기

문자 수에 비례해서 시간을 배분하는게 tts와 시간이 완벽히 맞아떨어지는가?
-> 안 맞아떨어짐

generate_str가 make_srt_from_script의 단순 버전이라는게 뭔 뜻인가?
generate_srt에서 만든걸 make_srt_from_script에서 만든걸로 덮어쓸거면 왜 generate_srt를 사용하는가?
-> generate_srt는 안쓰임. 확인도 안하고 복붙하면서 지랄 염병쌌나봄

node_subtitle_video에 영상을 만드는 기능을 넣어버렸는데 이미 있는 render_mp4 함수를 사용할 수는 없는가?
->
render_mp4 : 이미지+오디오 -> 영상 생성
node_subtitle_ideo : 영상+자막 -> 자막 입힌 영상

burn-in이라는 것은 영상 자체가 자막과 한 몸이 된거야 아니면 자막을 껐다 켤 수 있는 상태인거야?
-> 영상과 한 몸이 된 상태. 반대인 것은 soft subtitle로 자막 트랙을 별도로 삽입하는 방식. 자막을 켜고 끌 수 있음.
soft subtitle 방식을 적용하려면 srt를 지금과는 다르게 만들어야 하는가?  

-> subtitle node
함수로 srt 생성
soft subtitle 방식으로 자막 제공