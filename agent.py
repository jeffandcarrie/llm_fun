from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient

from tools import build_knowledge_graph, get_coordinates, get_knowledge_graph, get_weather
from tools.knowledge_graph import set_knowledge_graph_model

MODEL_ALIASES = ("openai-gpt-4o", "qwen")

def create_agent(model_name: str) -> Agent:
    model_client = OpenAIChatCompletionClient(
        model=model_name,
        base_url="http://localhost:4000/v1",
        api_key="placeholder",
    )
    return Agent(
        client=model_client,
        name=f"{model_name}-agent",
        instructions="Use get_weather for weather questions and get_coordinates for latitude or longitude questions. For knowledge graph requests, pass the source text to build_knowledge_graph, then use get_knowledge_graph to show the stored graph when asked. Do not infer unstated facts. After a tool returns, answer using its result. Do not invent values or mention external weather services.",
        tools=[get_weather, get_coordinates, build_knowledge_graph, get_knowledge_graph],
        default_options={"tool_choice": "auto"},
    )


agents = {model_name: create_agent(model_name) for model_name in MODEL_ALIASES}

# 4. Run a query through the agent
async def run_agent():
    active_model = "openai-gpt-4o"
    print("Ask a question, use 'model: <alias>' to switch models, or type 'quit' to exit.")
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

        if prompt.lower().startswith("model:"):
            selection = prompt[len("model:"):].strip().split(maxsplit=1)
            if not selection or selection[0] not in agents:
                print(f"Available models: {', '.join(MODEL_ALIASES)}")
                continue
            active_model = selection[0]
            set_knowledge_graph_model(active_model)
            print(f"Switched to {active_model}.")
            if len(selection) == 1:
                continue
            prompt = selection[1]

        print("Assistant: ", end="", flush=True)
        lowered_prompt = prompt.lower()
        if any(term in lowered_prompt for term in ("knowledge graph", "triple", "triples", "extract facts")):
            result = await build_knowledge_graph.func(prompt)
            print(result)
            if result.startswith("Extracted "):
                print("Knowledge graph:")
                print(get_knowledge_graph.func())
            continue

        async for chunk in agents[active_model].run(prompt, stream=True):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()


# Execute the async loop
import asyncio
asyncio.run(run_agent())

