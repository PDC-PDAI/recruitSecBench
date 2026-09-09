from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import TypeVar

from rscb_questionnaire.clients.langfuse.client import flush_langfuse
from rscb_questionnaire.schemas.experiment.schema import (
    ExperimentProfile,
    PipelineProfile,
    ResearchFront,
    validate_front_pipeline,
)
from rscb_questionnaire.services.agent_debug.service import (
    save_trajectory_files,
    scenario_trajectories,
)
from rscb_questionnaire.services.experiment.profile import load_experiment_profile
from rscb_questionnaire.services.scenario.service import ScenarioService
from rscb_questionnaire.settings import settings
from rscb_questionnaire.variants import Defense

_T = TypeVar("_T")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rscb-questionnaire",
        description="Run the RecruitSecBench questionnaire security experiment.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="Gera vaga, comandos 1:N e questionários.")
    source = run.add_mutually_exclusive_group(required=True)
    source.add_argument("--brief", help="Briefing textual da vaga.")
    source.add_argument("--brief-file", type=Path, help="Arquivo UTF-8 com o briefing.")
    run.add_argument(
        "--profile",
        type=Path,
        default=Path(__file__).parent / "profiles" / "security.yaml",
        help="Security profile; explicit flags override YAML values.",
    )
    run.add_argument(
        "--defense",
        choices=[item.value for item in Defense],
        help="baseline, baseline_r1, fides or camel; defaults to QUESTIONNAIRE_DEFENSE.",
    )
    run.add_argument("--benign", type=int, help="Quantidade de comandos benignos.")
    run.add_argument("--malicious", type=int, help="Quantidade de comandos malignos.")
    run.add_argument(
        "--benign-responses",
        type=int,
        help="Respostas benignas por questionário gerado.",
    )
    run.add_argument(
        "--malicious-responses",
        type=int,
        help="Respostas com prompt injection por questionário gerado.",
    )
    run.add_argument(
        "--questionnaire-evaluator",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Habilita ou desabilita a campanha de respostas e avaliação.",
    )
    run.add_argument("--output", type=Path, help="Arquivo JSON completo do cenário.")
    run.add_argument(
        "--jsonl",
        type=Path,
        help="Arquivo JSONL opcional com um BenchmarkRecord por trajetória.",
    )
    run.add_argument(
        "--agent-debug-jsonl",
        type=Path,
        help="Arquivo JSONL no contrato Trajectory consumido pelo AgentDebug-RH.",
    )
    run.add_argument(
        "--trajectories-dir",
        type=Path,
        help="Diretório onde será salvo um JSON por trajetória executada.",
    )

    sync = commands.add_parser("sync-prompts", help="Sincroniza os prompts locais com Langfuse.")
    sync.add_argument("--defense", choices=[item.value for item in Defense], default=None)

    validate_profile = commands.add_parser(
        "validate-profile",
        help="Valida e imprime a forma normalizada de um perfil YAML.",
    )
    validate_profile.add_argument("profile", type=Path, help="Arquivo YAML do perfil.")

    export = commands.add_parser(
        "export-trace",
        help="Exporta um trace completo do Langfuse em um único JSON.",
    )
    export.add_argument("--trace-id", required=True, help="ID hexadecimal do trace.")
    export.add_argument("--output", type=Path, help="Arquivo JSON; sem ele, imprime no stdout.")

    serve = commands.add_parser("serve", help="Inicia a API HTTP com Swagger em /docs.")
    serve.add_argument("--host", default=settings.API_HOST, help="Interface de rede da API.")
    serve.add_argument("--port", type=int, default=settings.API_PORT, help="Porta da API.")
    serve.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=settings.API_RELOAD,
        help="Recarrega a API ao alterar arquivos (apenas desenvolvimento).",
    )
    return parser


def _pick(explicit: _T | None, profile_value: _T | None, default: _T) -> _T:
    return (
        explicit
        if explicit is not None
        else (profile_value if profile_value is not None else default)
    )


def _apply_profile(args: argparse.Namespace) -> ExperimentProfile | None:
    profile = load_experiment_profile(
        args.profile or Path(__file__).parent / "profiles" / "security.yaml"
    )
    if profile and profile.front is not ResearchFront.SECURITY:
        raise ValueError("Only security profiles are supported by rscb-questionnaire.")
    pipeline = profile.pipeline if profile else None
    args.questionnaire_evaluator = _pick(
        getattr(args, "questionnaire_evaluator", None),
        pipeline.questionnaire_evaluator if pipeline else None,
        True,
    )
    args.benign = _pick(args.benign, pipeline.benign_commands if pipeline else None, 3)
    args.malicious = _pick(args.malicious, pipeline.malicious_commands if pipeline else None, 3)
    args.benign_responses = _pick(
        args.benign_responses, pipeline.benign_responses if pipeline else None, 1
    )
    args.malicious_responses = _pick(
        args.malicious_responses, pipeline.malicious_responses if pipeline else None, 1
    )
    resolved_pipeline = PipelineProfile(
        benign_commands=args.benign,
        malicious_commands=args.malicious,
        benign_responses=args.benign_responses,
        malicious_responses=args.malicious_responses,
        questionnaire_evaluator=args.questionnaire_evaluator,
    )
    validate_front_pipeline(profile.front if profile else None, resolved_pipeline)
    if profile:
        args.output = args.output or profile.artifacts.scenario_path
        args.jsonl = args.jsonl or profile.artifacts.benchmark_path
        args.agent_debug_jsonl = args.agent_debug_jsonl or profile.artifacts.agent_debug_path
        args.trajectories_dir = args.trajectories_dir or profile.artifacts.trajectory_path
    return profile


async def _run(args: argparse.Namespace) -> int:
    profile: ExperimentProfile | None = args.experiment_profile
    brief = args.brief or args.brief_file.read_text(encoding="utf-8")
    defense = getattr(args, "defense", None)
    service = ScenarioService(defense=defense) if defense is not None else ScenarioService()
    result = await service.run(
        brief,
        benign_count=args.benign,
        malicious_count=args.malicious,
        benign_response_count=args.benign_responses,
        malicious_response_count=args.malicious_responses,
        questionnaire_evaluator=args.questionnaire_evaluator,
        research_front=profile.front if profile else None,
        experiment_profile=profile.name if profile else None,
    )
    if profile:
        print(f"Perfil: {profile.name} (frente={profile.front.value})")
    rendered = result.model_dump_json(indent=2, by_alias=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Cenário salvo em {args.output}")
    else:
        print(rendered)
    if args.jsonl:
        args.jsonl.parent.mkdir(parents=True, exist_ok=True)
        lines = [record.model_dump_json(by_alias=True) for record in result.benchmark_records]
        args.jsonl.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Benchmark JSONL salvo em {args.jsonl}")
    if args.agent_debug_jsonl:
        args.agent_debug_jsonl.parent.mkdir(parents=True, exist_ok=True)
        trajectories = scenario_trajectories(result)
        lines = [trajectory.model_dump_json(exclude_none=True) for trajectory in trajectories]
        args.agent_debug_jsonl.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Trajetórias AgentDebug-RH salvas em {args.agent_debug_jsonl}")
    if args.trajectories_dir:
        trajectories = scenario_trajectories(result)
        paths = save_trajectory_files(trajectories, args.trajectories_dir)
        print(f"{len(paths)} trajetórias salvas em {args.trajectories_dir}")
    passed = sum(item.benchmark_passed for item in result.executions)
    print(f"Resultado: {passed}/{len(result.executions)} trajetórias passaram no oráculo.")
    evaluation_passed = sum(
        bool(item.oracle and item.oracle.passed) for item in result.evaluation_executions
    )
    print(
        "Avaliações: "
        f"{evaluation_passed}/{len(result.evaluation_executions)} passaram no oráculo defensivo."
    )
    flush_langfuse()
    return 0


def _export_trace(args: argparse.Namespace) -> int:
    from rscb_questionnaire.services.observability.export import fetch_trace_export  # noqa: PLC0415

    rendered = json.dumps(
        fetch_trace_export(args.trace_id),
        ensure_ascii=False,
        indent=2,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Trace salvo em {args.output}")
    else:
        print(rendered)
    return 0


def _serve(args: argparse.Namespace) -> int:
    import uvicorn  # noqa: PLC0415

    uvicorn.run(
        "rscb_questionnaire.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def _validate_profile(args: argparse.Namespace) -> int:
    profile = load_experiment_profile(args.profile)
    print(profile.model_dump_json(indent=2))
    return 0


def main() -> int:  # noqa: PLR0911 - dispatcher explícito mantém os comandos isolados
    parser = _parser()
    args = parser.parse_args()
    if args.command == "sync-prompts":
        from rscb_questionnaire.sync_prompts import sync_prompts  # noqa: PLC0415

        return sync_prompts(args.defense or settings.QUESTIONNAIRE_DEFENSE)
    if args.command == "validate-profile":
        try:
            return _validate_profile(args)
        except ValueError as exc:
            parser.error(str(exc))
    if args.command == "export-trace":
        return _export_trace(args)
    if args.command == "serve":
        return _serve(args)
    try:
        args.experiment_profile = _apply_profile(args)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        return asyncio.run(_run(args))
    finally:
        flush_langfuse()
