import json

from agent_framework import tool
from agent_framework import Message
from agent_framework.openai import OpenAIChatCompletionClient


_triples: set[tuple[str, str, str]] = set()
_model_client = OpenAIChatCompletionClient(
    model="qwen",
    base_url="http://localhost:4000/v1",
    api_key="placeholder",
)


def _parse_triples(response_text: str) -> list[tuple[str, str, str]]:
    content = response_text.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].removesuffix("```").strip()

    decoder = json.JSONDecoder()
    result = None
    for index, character in enumerate(content):
        if character in "[{":
            try:
                result, _ = decoder.raw_decode(content[index:])
                break
            except json.JSONDecodeError:
                continue

    if isinstance(result, list):
        extracted = result
    elif isinstance(result, dict):
        extracted = next(
            (result[key] for key in ("triples", "facts", "relations") if key in result),
            None,
        )
        if extracted is None and any(key in result for key in ("subject", "head", "source")):
            extracted = [result]
    else:
        extracted = None

    if not isinstance(extracted, list):
        raise ValueError("response does not contain a triple list")

    aliases = {
        "subject": ("subject", "head", "source", "entity1"),
        "predicate": ("predicate", "relation", "label"),
        "object": ("object", "tail", "target", "entity2"),
    }
    triples = []
    for item in extracted:
        if not isinstance(item, dict):
            raise ValueError("triple entries must be JSON objects")
        values = tuple(next((item[key] for key in names if key in item), None) for names in aliases.values())
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError("triple entries need non-empty subject, predicate, and object fields")
        triples.append(tuple(value.strip() for value in values))
    return triples


@tool
async def build_knowledge_graph(text: str) -> str:
    """Extracts explicit facts from text with the LLM and adds them to the knowledge graph."""
    if not text.strip():
        return "Provide text to extract knowledge graph triples from."

    prompt = (
        "Extract only facts explicitly stated in the source text as subject-predicate-object triples. "
        "Do not infer or add outside knowledge. Keep entities specific and predicates concise. "
        'Use exactly these keys and return JSON in this shape: {"triples":[{"subject":"...",'
        '"predicate":"...","object":"..."}]}. If there are no facts, return {"triples":[]}.\n\n'
            'Example: "Jeff is driving to the store to buy cheese." becomes '
        '{"triples":[{"subject":"Jeff","predicate":"driving to","object":"the store"},'
        '{"subject":"Jeff","predicate":"intends to buy","object":"cheese"}]}.\n\n'
        f"Source text:\n{text}"
    )
    try:
        response = await _model_client.get_response([Message(role="user", contents=[prompt])])
        normalized = _parse_triples(response.text)
    except Exception as error:
        response_text = getattr(locals().get("response"), "text", "")
        excerpt = f" Model response: {response_text[:300]}" if response_text else ""
        if isinstance(error, ValueError):
            return f"Could not parse triples: {error}.{excerpt} The graph was not changed."
        return f"Could not build the knowledge graph: {error}"

    before = len(_triples)
    _triples.update(normalized)
    added = len(_triples) - before
    return f"Extracted {len(normalized)} triples and added {added} new ones. Graph contains {len(_triples)} unique triples."


@tool
def get_knowledge_graph() -> str:
    """Returns all triples currently stored in the in-memory knowledge graph."""
    if not _triples:
        return "The knowledge graph is empty."

    triples = sorted(_triples)
    return "\n".join(f"({subject}, {predicate}, {object})" for subject, predicate, object in triples)