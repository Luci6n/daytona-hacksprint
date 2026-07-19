from unittest.mock import Mock

from backend.config import Settings
from backend.daytona_sandbox import (
    build_daytona,
    deploy,
    parse_args,
    sandbox_environment,
)


def test_sandbox_environment_excludes_disallowed_control_plane_credentials() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        demo_mode=False,
        daytona_api_key="control-plane-secret",
        moonshot_api_key="moonshot-secret",
        nosana_api_key="nosana-control-plane-secret",
        oxylabs_username="daddyfix-user",
        oxylabs_password="provider-secret",
        aiand_api_key="reasoning-secret",
    )

    environment = sandbox_environment(settings)

    assert environment["DEMO_MODE"] == "false"
    assert environment["OXYLABS_USERNAME"] == "daddyfix-user"
    assert environment["OXYLABS_PASSWORD"] == "provider-secret"
    assert environment["AIAND_API_KEY"] == "reasoning-secret"
    assert "DAYTONA_API_KEY" not in environment
    assert "MOONSHOT_API_KEY" not in environment
    assert "NOSANA_API_KEY" not in environment


def test_deploy_cli_defaults_to_feature_branch_and_six_hour_ttl() -> None:
    args = parse_args(["deploy", "--repo-url", "https://example.com/repo.git"])

    assert args.branch == "feature/lucian-backend"
    assert args.ttl_minutes == 360
    assert args.preview_expiry_seconds == 21_600


def test_deploy_explicitly_allows_only_live_provider_domains() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        oxylabs_realtime_url=(
            "https://ox-user:ox-secret@realtime.oxylabs.test/v1/queries?token=hidden"
        ),
        doubleword_base_url="https://dw-secret@api.doubleword.test:443/v1",
        aiand_base_url="https://ai-secret@api.aiand.test/v1?key=hidden",
        nosana_tts_url="https://tts-secret@tts.nosana.test/synthesize?key=hidden",
    )
    daytona = Mock()
    sandbox = daytona.create.return_value
    sandbox.process.exec.return_value.exit_code = 0
    sandbox.create_signed_preview_url.return_value.url = "https://preview.test"

    deploy(
        daytona=daytona,
        settings=settings,
        repo_url="https://example.test/repo.git",
        branch="feature/lucian-backend",
        ttl_minutes=360,
        preview_expiry_seconds=21_600,
    )

    create_params = daytona.create.call_args.args[0]
    assert create_params.domain_allow_list == (
        "realtime.oxylabs.test,api.doubleword.test,"
        "api.aiand.test,tts.nosana.test"
    )
    assert "secret" not in create_params.domain_allow_list
    assert "hidden" not in create_params.domain_allow_list


def test_daytona_client_requires_control_plane_key() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        daytona_api_key=None,
    )

    try:
        build_daytona(settings)
    except RuntimeError as exc:
        assert str(exc) == "DAYTONA_API_KEY is required."
    else:
        raise AssertionError("Expected missing Daytona key to be rejected")
