from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient

from tools import build_knowledge_graph, get_coordinates, get_knowledge_graph, get_weather

# 2. Configure the client to talk to the LiteLLM proxy
model_client = OpenAIChatCompletionClient(
    model="qwen",
    base_url="http://localhost:4000/v1",
    api_key="placeholder",
)

# 3. Instantiate the agent with the vLLM backend and tools
agent = Agent(
    client=model_client,
    name="vllm-agent",
    instructions="Use get_weather for weather questions and get_coordinates for latitude or longitude questions. For knowledge graph requests, pass the source text to build_knowledge_graph, then use get_knowledge_graph to show the stored graph when asked. Do not infer unstated facts. After a tool returns, answer using its result. Do not invent values or mention external weather services.",
    tools=[get_weather, get_coordinates, build_knowledge_graph, get_knowledge_graph],
    default_options={"tool_choice": "auto"},
)

# 4. Run a query through the agent
async def run_agent():
    print("Ask a question, or type 'quit' to exit.")
    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if prompt.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break
        if not prompt:
            continue

        print("Assistant: ", end="", flush=True)
        lowered_prompt = prompt.lower()
        if any(term in lowered_prompt for term in ("knowledge graph", "triple", "triples", "extract facts")):
            result = await build_knowledge_graph.func(prompt)
            print(result)
            if result.startswith("Extracted "):
                print("Knowledge graph:")
                print(get_knowledge_graph.func())
            continue

        async for chunk in agent.run(prompt, stream=True):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()


# Execute the async loop
import asyncio
asyncio.run(run_agent())

