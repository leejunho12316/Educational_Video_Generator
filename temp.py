import json
from langchain_core.messages import messages_from_dict

with open("./step1_output/final_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

print(state['messages'][0])