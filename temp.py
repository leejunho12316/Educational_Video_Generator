import json
import re
import ast

with open("./step1_output/final_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

SEP_AI   = "=" * 34 + " Ai Message "   + "=" * 34
SEP_TOOL = "=" * 33 + " Tool Message " + "=" * 33

def classify(m):
    if "tool_call_id='" in m:
        return "tool_msg"
    if "tool_calls=[{" in m:
        return "ai_tool_call"
    return "other"

def get_tool_calls(m):
    match = re.search(r"tool_calls=(\[.*?\]) invalid_tool_calls", m, re.DOTALL)
    return ast.literal_eval(match.group(1)) if match else []

messages = state.get("messages", [])

for i, m in enumerate(messages):
    kind = classify(m)

    if kind == "ai_tool_call":
        print(SEP_AI)
        print("Tool Calls:")
        for tc in get_tool_calls(m):
            print(f"  {tc['name']} ({tc['id']})")
            print(f" Call ID: {tc['id']}")
            print("  Args:")
            for k, v in tc["args"].items():
                print(f"    {k}: {v}")
        print()

    elif kind == "tool_msg":
        name  = re.search(r" name='(.*?)'", m)
        content = re.search(r"content='(.*?)' name='", m, re.DOTALL)
        print(SEP_TOOL)
        print(f"Name: {name.group(1) if name else ''}")
        print()
        print(content.group(1) if content else "")
        print()

    elif i > 0 and classify(messages[i - 1]) == "tool_msg":
        content = re.search(r"content='(.*?)' additional_kwargs=", m, re.DOTALL)
        print(SEP_AI)
        print()
        print(content.group(1) if content else "")
        print()
