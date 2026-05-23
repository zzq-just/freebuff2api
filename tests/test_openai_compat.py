import unittest

from freebuff2api.codebuff import FreebuffSession
from freebuff2api.models import (
    CONTEXT_PRUNER_AGENT_ID,
    FREEBUFF_MODELS,
    agent_validation_payload,
    models_response,
    resolve_model,
)
from freebuff2api.openai_compat import (
    CompletionAccumulator,
    build_upstream_payload,
    sanitize_stream_chunk,
)


class OpenAICompatTests(unittest.TestCase):
    def test_models_response_lists_all_freebuff_models(self) -> None:
        response = models_response()

        self.assertEqual(
            [item["id"] for item in response["data"]],
            [model.id for model in FREEBUFF_MODELS],
        )

    def test_resolve_model_maps_agent_id(self) -> None:
        model = resolve_model("moonshotai/kimi-k2.6")

        self.assertEqual(model.agent_id, "base2-free-kimi")

    def test_agent_validation_payload_defines_spawnable_agents(self) -> None:
        payload = agent_validation_payload()
        definitions = payload["agentDefinitions"]
        ids = {definition["id"] for definition in definitions}
        spawnable_ids = {
            agent_id
            for definition in definitions
            for agent_id in definition.get("spawnableAgents", [])
        }

        self.assertIn(CONTEXT_PRUNER_AGENT_ID, ids)
        self.assertLessEqual(spawnable_ids, ids)

    def test_agent_validation_payload_has_spawn_agent_tool_when_spawnable(self) -> None:
        payload = agent_validation_payload()

        for definition in payload["agentDefinitions"]:
            if definition.get("spawnableAgents"):
                self.assertIn("spawn_agents", definition["toolNames"])

    def test_build_upstream_payload_uses_explicit_client_id(self) -> None:
        payload = build_upstream_payload(
            {"model": "deepseek/deepseek-v4-pro", "messages": []},
            session=FreebuffSession(
                instance_id="instance-1",
                model="deepseek/deepseek-v4-pro",
            ),
            run_id="run-1",
            client_id="client-1",
            trace_session_id="trace-1",
        )

        self.assertTrue(payload["stream"])
        self.assertEqual(payload["model"], "deepseek/deepseek-v4-pro")
        self.assertEqual(payload["provider"], {"data_collection": "deny"})
        self.assertEqual(
            payload["codebuff_metadata"],
            {
                "freebuff_instance_id": "instance-1",
                "trace_session_id": "trace-1",
                "run_id": "run-1",
                "client_id": "client-1",
                "cost_mode": "free",
            },
        )

    def test_accumulator_keeps_reasoning_content_separate(self) -> None:
        accumulator = CompletionAccumulator("deepseek/deepseek-v4-flash")

        accumulator.add(
            {
                "id": "chunk-1",
                "created": 1,
                "model": "deepseek/deepseek-v4-flash",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": None, "reasoning_content": "hello"},
                        "finish_reason": None,
                    }
                ],
            }
        )

        response = accumulator.final_response()

        message = response["choices"][0]["message"]
        self.assertEqual(message["content"], "")
        self.assertEqual(message["reasoning_content"], "hello")

    def test_accumulator_keeps_final_answer_as_content(self) -> None:
        accumulator = CompletionAccumulator("deepseek/deepseek-v4-flash")

        accumulator.add(
            {
                "id": "chunk-1",
                "created": 1,
                "model": "deepseek/deepseek-v4-flash",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": None, "reasoning_content": "thinking"},
                        "finish_reason": None,
                    },
                    {
                        "index": 0,
                        "delta": {"content": "answer", "reasoning_content": None},
                        "finish_reason": "stop",
                    },
                ],
            }
        )

        message = accumulator.final_response()["choices"][0]["message"]

        self.assertEqual(message["content"], "answer")
        self.assertEqual(message["reasoning_content"], "thinking")

    def test_stream_chunk_keeps_reasoning_content_separate(self) -> None:
        chunk = sanitize_stream_chunk(
            {
                "id": "chunk-1",
                "created": 1,
                "model": "deepseek/deepseek-v4-flash",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": None, "reasoning_content": "hello"},
                        "finish_reason": None,
                    }
                ],
            }
        )

        delta = chunk["choices"][0]["delta"]
        self.assertNotIn("content", delta)
        self.assertEqual(delta["reasoning_content"], "hello")


if __name__ == "__main__":
    unittest.main()
