from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage


@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


model = init_chat_model(
    "llama3.2",
    model_provider="ollama"
)

model_with_tools = model.bind_tools([
    add,
    multiply
])


def run_tool_call(question):
    response = model_with_tools.invoke(question)

    print("\nQuestion:")
    print(question)

    print("\nTool Calls:")
    print(response.tool_calls)

    if not response.tool_calls:
        print("\nModel answered without using a tool:")
        print(response.content)
        return

    messages = [
        HumanMessage(content=question),
        response
    ]

    for tool_call in response.tool_calls:

        if tool_call["name"] == "add":
            result = add.invoke(tool_call["args"])

        elif tool_call["name"] == "multiply":
            result = multiply.invoke(tool_call["args"])

        else:
            raise ValueError(
                f"Unknown tool: {tool_call['name']}"
            )

        print("\nTool Result:")
        print(result)

        messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
        )

    final_response = model_with_tools.invoke(messages)

    print("\nFinal Answer:")
    print(final_response.content)


run_tool_call("What is 25 plus 15?")

run_tool_call("What is 25 multiplied by 15?")