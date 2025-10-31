import os
from dotenv import load_dotenv
import asyncio
from agents import Agent, Runner, SQLiteSession

jundev_agent = Agent(
    name="junior_developer_agent",
    model="gpt-5-mini",
    instructions="You are a junior developer. Your job is to review the code as a junior developer. Focus on providing peer-to-peer feedback, and ask questions about specific parts of the code. Ask as many questions as possible. Format your response to Markdown Style.\n",
)

sendev_agent = Agent(
    name="senior_developer_agent",
    model="gpt-5-mini",
    instructions="You are a senior developer. Your job is to review the code as a senior developer. Focus on the tech stack, and give insights as a senior developer to junior developer. Answer any questions asked by the junior. Be as critical as possible. Format your response to Markdown Style.",
)

manager_agent = Agent(
    name="manager_agent",
    model="gpt-5-mini",
    instructions=(
        "You are the manager.\n"
        "Process for ANY code review request:\n"
        "1. Call the `junior_developer_agent` tool. Ask it to review the code and list all questions it has.\n"
        "2. Then call the `senior_developer_agent` tool. Pass along the junior's questions so they can be answered.\n"
        "3. Finally, produce a single unified review for the user that:\n"
        "   - summarizes junior concerns,\n"
        "   - includes senior answers,\n"
        "   - gives next steps.\n"
        "IMPORTANT:\n"
        "You MUST NOT produce a final answer until after you have called BOTH tools.\n"
        "If you have not yet called both tools, you MUST call a tool instead of answering.\n"
        "If you believe you can answer without tools, you are still REQUIRED to call both tools first.\n"
        "Format your response to Markdown Style.\n"
    ),
    tools=[
        jundev_agent.as_tool(
            tool_name="junior_developer_agent",
            tool_description=(
                "Review the provided code as a junior developer and return:\n"
                "1. A bullet list of concerns and questions.\n"
                "2. Any unclear parts of the code.\n\n"
                "Args:\n"
                "- code (string): full source code to review.\n"
                "Return:\n"
                "- json-like text with 'questions' and 'comments'."
            ),
        ),
        sendev_agent.as_tool(
            tool_name="senior_developer_agent",
            tool_description=(
                "Given the same code and the junior_developer_agent's questions, respond as a senior dev.\n"
                "Args:\n"
                "- code (string): full source code.\n"
                "- junior_feedback (string): the junior's questions/concerns.\n"
                "Return:\n"
                "- guidance for fixes, architecture critique, answers."
            ),
        )
    ]
)

# Load OPENAI API KEY
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "Missing OPENAI_API_KEY. Create a .env file with OPENAI_API_KEY=... or export it in your shell."
    )

async def main(user_input: str, file_path: str):
    # Read the file content
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Combine user input with file content
    full_input = f"{user_input}\n\nFile to review:\n```\n{file_content}\n```"

    # Create session to make this conversation stateful
    session = SQLiteSession("code_review_debug")

    # Handle streaming output
    result = await Runner.run(
        manager_agent,
        input=full_input,
        session=session,
    )

    # store junior and senior notes to offline text
    junior_notes = list()
    senior_notes = list()
    manager_notes = list()
    planning_notes = list()

    # DEBUG: for debugging the flow of agentic system only
    # print("\n\n======== RAW new_items DUMP ========\n\n")
    # for idx, item in enumerate(result.new_items):
    #     print(f"[{idx}] type={getattr(item, 'type', None)}")
    #     print("item dir:", dir(item))
    #     print("item repr:", item)
    #     print("item.raw:", getattr(item, "raw", None))
    #     print("-----------")

    
    print("\n\n=====Manager Agent initiated=====\n\n")
    
    # Print the final output from the manager agent
    print(result)

    print("\n\n======== Debugging ========\n\n")
    used_tools = set()
    id_to_tool = {}
    for item in result.new_items:
        t = getattr(item, "type", None)
        if t == "tool_call_item":
            # tool was invoked
            tool_name = item.raw_item.name  # ex: "junior_developer_agent"
            call_id   = item.raw_item.call_id
            id_to_tool[call_id] = tool_name
            used_tools.add(tool_name)

            print("[TOOL CALL]")
            print(f"  tool: {tool_name}")
            print(f"  call_id: {item.raw_item.call_id}")
            print(f"  args: {item.raw_item.arguments}")
            print()

        elif t == "tool_call_output_item":
            # tool responded
            print("[TOOL RESULT]")
            print(f"  call_id: {item.raw_item['call_id']}")
            print(f"  tool output (truncated):\n{item.output[:500]}")
            print()
            call_id = item.raw_item["call_id"]
            tool_name = id_to_tool.get(call_id, "").lower()
            if "junior" in tool_name:
                junior_notes.append(item.output)
            elif "senior" in tool_name:
                senior_notes.append(item.output)

        elif t == "message_output_item":
            # manager's final user-facing message
            print("[FINAL MESSAGE FRAGMENT]")
            # item.raw_item.content is a list of ResponseOutputText objects
            try:
                chunks = item.raw_item.content
                text = "\n".join([c.text for c in chunks])
                manager_notes.append(text)
            except Exception:
                text = str(item.raw_item)
            print(text[:500])
            print()

        elif t == "reasoning_item":
            # internal planning; optional to print
            # skip reasoning
            planning_notes.append(str(item.raw_item))
            pass


    print("\n\n======== TOOLS USED: ========\n\n")
    print(used_tools)

    # SANITY CHECK: Does the manager use all tools?
    required = {"junior_developer_agent", "senior_developer_agent"}
    if not required.issubset(used_tools):
        print("WARNING: Manager did NOT call all required tools!")
        print(f"Expected: {required}, got: {used_tools}")

    print("\n\n======== FINAL OUTPUT ========\n\n")
    print(result.final_output)

    # OFFLINE TASK:junior_notes and senior_notes to junior_review.md and senior_review.md
    path_parts = file_path.split(os.sep)
    base = "_".join(path_parts[-3:]).replace(".", "_")  # recursive two repo names

    base = os.path.splitext(base)[0]
    review_dir = os.path.join("reviews", base)
    os.makedirs(review_dir, exist_ok=True)
    
    # define file names
    junior_fn = os.path.join(review_dir, "junior_review.md")
    senior_fn = os.path.join(review_dir, "senior_review.md")
    manager_fn = os.path.join(review_dir, "manager_review.md")
    planner_fn = os.path.join(review_dir, "planner_review.md")  # FIXME: remove for production
    
    # Write junior notes to file
    if junior_notes:
        with open(junior_fn, "w") as f:
            f.write("# Junior Developer Review\n\n")
            for note in junior_notes:
                f.write(note)
                f.write("\n\n")
        print("\n✓ Junior review saved to: junior_review.md")
    
    # Write senior notes to file
    if senior_notes:
        with open(senior_fn, "w") as f:
            f.write("# Senior Developer Review\n\n")
            for note in senior_notes:
                f.write(note)
                f.write("\n\n")
        print("✓ Senior review saved to: senior_review.md")

    # Write manger notes to fiule
    if manager_notes:
        with open(manager_fn, "w") as f:
            f.write("# Manager Notes\n\n")
            for note in manager_notes:
                f.write(note)
                f.write("\n\n")
        print("✓ Manger Notes saved to: manager_review.md")

    # Any planning stage notes - to check for sanity of this agentic flow
    if planning_notes:
        with open(planner_fn, "w") as f:
            f.write("# Planner Notes\n\n")
            for note in planning_notes:
                f.write(note)
                f.write("\n\n")
        print("✓ Planner Notes saved to: planning_steps.md")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python agent.py <input_message> <file_path>")
        print("Example: python agent.py 'Please review this code' ./mycode.py")
        sys.exit(1)
    
    user_input = sys.argv[1]
    file_path = sys.argv[2]
    
    asyncio.run(main(user_input, file_path))