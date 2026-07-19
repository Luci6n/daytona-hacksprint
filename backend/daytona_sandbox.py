"""Smoke-test, deploy, or delete the DaddyFix Daytona sandbox."""

import argparse
from collections.abc import Sequence
from urllib.parse import urlsplit

from daytona import (
    CreateSandboxFromImageParams,
    Daytona,
    DaytonaConfig,
    SessionExecuteRequest,
)

from backend.config import Settings


SANDBOX_ENV_FIELDS = {
    "APP_ENV": "app_env",
    "DEMO_MODE": "demo_mode",
    "KIMI_BASE_URL": "kimi_base_url",
    "KIMI_MODEL": "kimi_model",
    "NOSANA_BASE_URL": "nosana_base_url",
    "NOSANA_TTS_URL": "nosana_tts_url",
    "NOSANA_TTS_BEARER_TOKEN": "nosana_tts_bearer_token",
    "TTS_MODEL": "tts_model",
    "TTS_LANGUAGE": "tts_language",
    "TTS_VOICE_DESCRIPTION": "tts_voice_description",
    "TTS_TIMEOUT_SECONDS": "tts_timeout_seconds",
    "OXYLABS_USERNAME": "oxylabs_username",
    "OXYLABS_PASSWORD": "oxylabs_password",
    "OXYLABS_MODE": "oxylabs_mode",
    "OXYLABS_REALTIME_URL": "oxylabs_realtime_url",
    "OXYLABS_PROXY_URL": "oxylabs_proxy_url",
    "OXYLABS_PROXY_COUNTRY": "oxylabs_proxy_country",
    "DOUBLEWORD_API_KEY": "doubleword_api_key",
    "DOUBLEWORD_BASE_URL": "doubleword_base_url",
    "DOUBLEWORD_MODEL": "doubleword_model",
    "AIAND_API_KEY": "aiand_api_key",
    "AIAND_BASE_URL": "aiand_base_url",
    "AIAND_MODEL": "aiand_model",
}

SANDBOX_PROVIDER_URL_FIELDS = (
    "oxylabs_realtime_url",
    "doubleword_base_url",
    "aiand_base_url",
    "nosana_tts_url",
)


def sandbox_environment(settings: Settings) -> dict[str, str]:
    environment: dict[str, str] = {}
    for env_name, field_name in SANDBOX_ENV_FIELDS.items():
        value = getattr(settings, field_name)
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            environment[env_name] = str(value).lower()
        else:
            environment[env_name] = str(value)
    return environment


def sandbox_domain_allow_list(settings: Settings) -> str:
    domains: list[str] = []
    for field_name in SANDBOX_PROVIDER_URL_FIELDS:
        provider_url = getattr(settings, field_name)
        if not provider_url:
            continue
        hostname = urlsplit(provider_url).hostname
        if hostname:
            normalized_hostname = hostname.lower().rstrip(".")
            if normalized_hostname not in domains:
                domains.append(normalized_hostname)
    return ",".join(domains)


def build_daytona(settings: Settings) -> Daytona:
    if not settings.daytona_api_key:
        raise RuntimeError("DAYTONA_API_KEY is required.")
    return Daytona(
        DaytonaConfig(
            api_key=settings.daytona_api_key,
            api_url=settings.daytona_api_url,
            target=settings.daytona_target,
        )
    )


def smoke_check(daytona: Daytona) -> None:
    sandbox = daytona.create(
        CreateSandboxFromImageParams(
            image="python:3.12-slim",
            ephemeral=True,
            labels={"app": "daddyfix", "purpose": "smoke-check"},
        )
    )
    try:
        response = sandbox.process.exec("python --version")
        if response.exit_code:
            raise RuntimeError(response.result)
        print(response.result.strip())
        print("Daytona sandbox execution is ready.")
    finally:
        daytona.delete(sandbox, wait=True)
        print("Smoke-check sandbox deleted.")


def deploy(
    daytona: Daytona,
    settings: Settings,
    repo_url: str,
    branch: str,
    ttl_minutes: int,
    preview_expiry_seconds: int,
) -> None:
    sandbox = daytona.create(
        CreateSandboxFromImageParams(
            name="daddyfix-api",
            image="python:3.12-slim",
            env_vars=sandbox_environment(settings),
            domain_allow_list=sandbox_domain_allow_list(settings),
            public=False,
            ttl_minutes=ttl_minutes,
            auto_delete_interval=ttl_minutes,
            labels={"app": "daddyfix", "purpose": "api"},
        )
    )
    try:
        sandbox.git.clone(repo_url, "daddyfix", branch=branch, depth=1)
        install = sandbox.process.exec(
            "python -m pip install --no-cache-dir -r backend/requirements.txt",
            cwd="daddyfix",
            timeout=600,
        )
        if install.exit_code:
            raise RuntimeError(f"Dependency installation failed:\n{install.result}")

        session_id = "daddyfix-api"
        sandbox.process.create_session(session_id)
        sandbox.process.execute_session_command(
            session_id,
            SessionExecuteRequest(
                command=(
                    "cd daddyfix && python -m uvicorn backend.main:app "
                    "--host 0.0.0.0 --port 8000"
                ),
                run_async=True,
            ),
            timeout=30,
        )
        preview = sandbox.create_signed_preview_url(
            8000,
            expires_in_seconds=preview_expiry_seconds,
        )
        print(f"Sandbox ID: {sandbox.id}")
        print(f"DaddyFix API: {preview.url}")
        print("Run the delete command when the demo is finished.")
    except Exception:
        daytona.delete(sandbox, wait=True)
        raise


def delete(daytona: Daytona, sandbox_id: str) -> None:
    sandbox = daytona.get(sandbox_id)
    daytona.delete(sandbox, wait=True)
    print(f"Deleted Daytona sandbox {sandbox_id}.")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("smoke", help="Create, test, and delete an ephemeral sandbox.")

    deploy_parser = subparsers.add_parser(
        "deploy", help="Deploy a pushed DaddyFix branch and print its preview URL."
    )
    deploy_parser.add_argument("--repo-url", required=True)
    deploy_parser.add_argument("--branch", default="feature/lucian-backend")
    deploy_parser.add_argument("--ttl-minutes", type=int, default=360)
    deploy_parser.add_argument("--preview-expiry-seconds", type=int, default=21_600)

    delete_parser = subparsers.add_parser("delete", help="Delete a deployed sandbox.")
    delete_parser.add_argument("sandbox_id")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    settings = Settings()
    daytona = build_daytona(settings)
    if args.command == "smoke":
        smoke_check(daytona)
    elif args.command == "deploy":
        deploy(
            daytona=daytona,
            settings=settings,
            repo_url=args.repo_url,
            branch=args.branch,
            ttl_minutes=args.ttl_minutes,
            preview_expiry_seconds=args.preview_expiry_seconds,
        )
    else:
        delete(daytona, args.sandbox_id)


if __name__ == "__main__":
    main()
