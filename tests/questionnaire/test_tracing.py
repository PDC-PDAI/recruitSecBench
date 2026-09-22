from __future__ import annotations

import json
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import langfuse
import pytest
from agno.run.agent import RunContentEvent, ToolCallCompletedEvent, ToolCallStartedEvent

from rscb_questionnaire.schemas.observability.schema import NodeLocus, TraceNode
from rscb_questionnaire.services.observability import export, react, service
from rscb_questionnaire.services.observability.react import ReactSpanStreamer


def _node() -> TraceNode:
    return TraceNode(
        node_id="scenario-1.questionnaire.001",
        locus=NodeLocus.SUB_GER,
        name="questionnaire-agent",
    )


def test_observation_can_start_an_isolated_trace(monkeypatch):
    span = MagicMock()
    client = MagicMock()
    client.start_as_current_observation.return_value = nullcontext(span)
    monkeypatch.setattr(service, "get_langfuse_client", lambda: client)

    with service.observation(_node(), as_type="agent", trace_id="a" * 32) as observed:
        assert observed is span

    assert client.start_as_current_observation.call_args.kwargs["trace_context"] == {
        "trace_id": "a" * 32
    }


def test_create_langfuse_trace_id_is_correlated_with_trajectory(monkeypatch):
    client = SimpleNamespace(create_trace_id=MagicMock(return_value="b" * 32))
    monkeypatch.setattr(service, "get_langfuse_client", lambda: client)

    trace_id = service.create_langfuse_trace_id(seed="trajectory-123")

    assert trace_id == "b" * 32
    client.create_trace_id.assert_called_once_with(seed="trajectory-123")


def test_create_langfuse_trace_id_is_optional(monkeypatch):
    monkeypatch.setattr(service, "get_langfuse_client", lambda: None)

    assert service.create_langfuse_trace_id(seed="trajectory-123") is None


def test_trace_attributes_group_trajectory_in_scenario_session(monkeypatch):
    propagate = MagicMock(return_value=nullcontext())
    client = MagicMock()
    monkeypatch.setattr(service, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(langfuse, "propagate_attributes", propagate)

    with service.trace_attributes(
        session_id="scenario-1",
        trace_name="questionnaire-trajectory",
        environment="development",
        tags=["questionnaire-security", "trajectory"],
        metadata={"trajectory_id": "trajectory-123"},
    ):
        pass

    propagate.assert_called_once_with(
        session_id="scenario-1",
        trace_name="questionnaire-trajectory",
        environment="development",
        tags=["questionnaire-security", "trajectory"],
        metadata={"trajectory_id": "trajectory-123"},
    )


def _tool(name: str, *, args=None, result=None, call_id="c1"):
    return SimpleNamespace(
        tool_name=name,
        tool_args=args,
        result=result,
        tool_call_id=call_id,
    )


@pytest.mark.asyncio
async def test_react_spans_are_reasoning_action_observation(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(react, "get_langfuse_client", lambda: client)
    sleep = AsyncMock()
    monkeypatch.setattr(react.asyncio, "sleep", sleep)
    streamer = ReactSpanStreamer(node_prefix="scenario.questionnaire.001")
    tool = _tool("get_info_vaga", args={"code": "job-1"}, result={"title": "Dev"})

    await streamer.handle(RunContentEvent(reasoning_content="Vou consultar a vaga."))
    await streamer.handle(ToolCallStartedEvent(tool=tool))
    await streamer.handle(ToolCallCompletedEvent(tool=tool))

    names = [call.kwargs["name"] for call in client.start_observation.call_args_list]
    assert names == ["reasoning", "action:get_info_vaga", "observation"]
    assert (
        client.start_observation.call_args_list[0]
        .kwargs["metadata"]["node_id"]
        .endswith(".reasoning.01")
    )
    assert client.start_observation.call_args_list[0].kwargs["input"] == {
        "step": 1,
        "context_node_ids": [],
        "trigger": "model_reasoning_summary",
    }
    assert client.start_observation.call_args_list[1].kwargs["metadata"]["depends_on"] == [
        "scenario.questionnaire.001.reasoning.01"
    ]
    sleep.assert_awaited_once_with(react._LANGFUSE_TIMESTAMP_TICK_SECONDS)


@pytest.mark.asyncio
async def test_second_reasoning_depends_on_previous_observation(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(react, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(react.asyncio, "sleep", AsyncMock())
    streamer = ReactSpanStreamer(node_prefix="scenario.questionnaire.001")
    first = _tool("get_info_vaga", result={"title": "Dev"}, call_id="a")
    second = _tool("salvar_formulario", result={"ok": True}, call_id="b")

    for event in (
        ToolCallStartedEvent(tool=first),
        ToolCallCompletedEvent(tool=first),
        ToolCallStartedEvent(tool=second),
        ToolCallCompletedEvent(tool=second),
    ):
        await streamer.handle(event)

    second_reasoning = client.start_observation.call_args_list[3].kwargs
    assert second_reasoning["name"] == "reasoning"
    assert second_reasoning["metadata"]["depends_on"] == [
        "scenario.questionnaire.001.observation.01"
    ]
    assert second_reasoning["input"] == {
        "step": 2,
        "context_node_ids": ["scenario.questionnaire.001.observation.01"],
        "trigger": "tool_selection",
    }
    assert streamer.terminal_dependencies == ["scenario.questionnaire.001.observation.02"]


@pytest.mark.asyncio
async def test_agent_debug_steps_are_captured_without_langfuse(monkeypatch):
    monkeypatch.setattr(react, "get_langfuse_client", lambda: None)
    streamer = ReactSpanStreamer(
        node_prefix="scenario.questionnaire.001",
        initial_input="Gere perguntas para a vaga job-1.",
    )
    tool = _tool("get_info_vaga", args={"code": "job-1"}, result={"title": "Dev"})

    await streamer.handle(RunContentEvent(reasoning_content="Preciso consultar a vaga."))
    await streamer.handle(ToolCallStartedEvent(tool=tool))
    await streamer.handle(ToolCallCompletedEvent(tool=tool))

    steps = streamer.trajectory_steps
    assert len(steps) == 1
    assert steps[0].index == 1
    assert steps[0].module_outputs["planning"] == "Preciso consultar a vaga."
    assert '"tool": "get_info_vaga"' in steps[0].module_outputs["action"]
    assert '"title": "Dev"' in steps[0].env_response
    assert steps[0].step_input == "Gere perguntas para a vaga job-1."
    raw_output = json.loads(steps[0].raw_output)
    assert raw_output["planning"] == steps[0].module_outputs["planning"]
    assert raw_output["action"] == json.loads(steps[0].module_outputs["action"])


def test_terminal_failure_becomes_analyzable_step(monkeypatch):
    monkeypatch.setattr(react, "get_langfuse_client", lambda: None)
    streamer = ReactSpanStreamer(
        node_prefix="scenario.questionnaire.001",
        initial_input="Gere um questionário.",
    )

    streamer.record_terminal_failure(
        code="MISSING_TERMINAL_TOOL_CALL",
        message="Nenhuma tool terminal foi chamada.",
        final_output="Resposta textual sem tool.",
    )

    step = streamer.trajectory_steps[0]
    assert step.index == 1
    assert "planning" in step.module_outputs
    assert "action" in step.module_outputs
    assert "MISSING_TERMINAL_TOOL_CALL" in step.env_response
    raw_output = json.loads(step.raw_output)
    assert raw_output["planning"] == step.module_outputs["planning"]
    assert raw_output["action"] == json.loads(step.module_outputs["action"])


@pytest.mark.asyncio
async def test_large_actions_keep_raw_output_as_complete_json(monkeypatch):
    monkeypatch.setattr(react, "get_langfuse_client", lambda: None)
    streamer = ReactSpanStreamer(node_prefix="scenario.questionnaire.001")
    large_value = "x" * (react._OBSERVATION_LIMIT * 2)
    tool = _tool("submit_large_payload", args={"content": large_value})

    await streamer.handle(RunContentEvent(reasoning_content="Enviar o payload completo."))
    await streamer.handle(ToolCallStartedEvent(tool=tool))
    streamer.record_terminal_failure(
        code="MISSING_TERMINAL_TOOL_CALL",
        message="Nenhuma tool terminal foi chamada.",
        final_output={"content": large_value},
    )

    for step in streamer.trajectory_steps:
        raw_output = json.loads(step.raw_output)
        assert raw_output["planning"] == step.module_outputs["planning"]
        assert raw_output["action"] == json.loads(step.module_outputs["action"])
        assert len(step.raw_output) > react._OBSERVATION_LIMIT


def test_fetch_trace_export_includes_nested_observations_and_scores(monkeypatch):
    trace = MagicMock()
    trace.model_dump.return_value = {
        "id": "trace-1",
        "input": {"brief": "Vaga backend"},
        "observations": [{"id": "obs-1", "input": {"step": 1}}],
        "scores": [{"id": "score-1", "name": "benchmark_passed", "value": 1}],
    }
    client = SimpleNamespace(
        api=SimpleNamespace(trace=SimpleNamespace(get=MagicMock(return_value=trace)))
    )
    monkeypatch.setattr(export, "get_langfuse_client", lambda: client)

    result = export.fetch_trace_export(" trace-1 ")

    client.api.trace.get.assert_called_once_with("trace-1")
    trace.model_dump.assert_called_once_with(mode="json", by_alias=True)
    assert result["observations"][0]["id"] == "obs-1"
    assert result["scores"][0]["id"] == "score-1"


def test_fetch_trace_export_requires_langfuse_configuration(monkeypatch):
    monkeypatch.setattr(export, "get_langfuse_client", lambda: None)

    with pytest.raises(RuntimeError, match="Langfuse não configurado"):
        export.fetch_trace_export("trace-1")
