from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FreebuffModel:
    id: str
    agent_id: str
    owned_by: str = "freebuff"


FREEBUFF_MODELS: tuple[FreebuffModel, ...] = (
    FreebuffModel("deepseek/deepseek-v4-flash", "base2-free-deepseek-flash"),
    FreebuffModel("deepseek/deepseek-v4-pro", "base2-free-deepseek"),
    FreebuffModel("moonshotai/kimi-k2.6", "base2-free-kimi"),
    FreebuffModel("minimax/minimax-m2.7", "base2-free"),
    FreebuffModel("z-ai/glm-5.1", "base2-free"),
)

DEFAULT_MODEL = FREEBUFF_MODELS[0]
CONTEXT_PRUNER_AGENT_ID = "context-pruner"


def resolve_model(requested: str | None) -> FreebuffModel:
    if not requested:
        return DEFAULT_MODEL
    for model in FREEBUFF_MODELS:
        if model.id == requested:
            return model
    raise ValueError(f"Unsupported Freebuff model: {requested}")


def models_response() -> dict[str, object]:
    return {
        "object": "list",
        "data": [
            {
                "id": model.id,
                "object": "model",
                "created": 0,
                "owned_by": model.owned_by,
            }
            for model in FREEBUFF_MODELS
        ],
    }


def agent_validation_payload() -> dict[str, object]:
    unique_agents = []
    seen_agent_ids: set[str] = set()
    for model in FREEBUFF_MODELS:
        if model.agent_id in seen_agent_ids:
            continue
        seen_agent_ids.add(model.agent_id)
        unique_agents.append(model)

    definitions = [
        _agent_definition(
            agent_id=model.agent_id,
            model_id=model.id,
            display_name=f"Freebuff {model.id}",
            spawnable_agents=[CONTEXT_PRUNER_AGENT_ID],
        )
        for model in unique_agents
    ]
    definitions.append(
        _agent_definition(
            agent_id=CONTEXT_PRUNER_AGENT_ID,
            model_id=DEFAULT_MODEL.id,
            display_name="Context Pruner",
            spawnable_agents=[],
        )
    )

    return {"agentDefinitions": definitions}


def _agent_definition(
    *,
    agent_id: str,
    model_id: str,
    display_name: str,
    spawnable_agents: list[str],
) -> dict[str, object]:
    return {
        "id": agent_id,
        "publisher": "codebuff",
        "model": model_id,
        "displayName": display_name,
        "spawnerPrompt": "Freebuff OpenAI-compatible orchestrator",
        "inputSchema": {
            "prompt": {
                "type": "string",
                "description": "A coding task to complete",
            },
            "params": {"type": "object", "properties": {}, "required": []},
        },
        "outputMode": "last_message",
        "includeMessageHistory": True,
        "toolNames": ["spawn_agents"] if spawnable_agents else [],
        "spawnableAgents": spawnable_agents,
        "systemPrompt": "Act as a helpful coding assistant.",
    }
