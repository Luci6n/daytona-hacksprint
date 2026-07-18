from backend.config import Settings
from backend.daytona_sandbox import build_daytona, parse_args, sandbox_environment


def test_sandbox_environment_excludes_daytona_control_credentials() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        demo_mode=False,
        daytona_api_key="control-plane-secret",
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


def test_deploy_cli_defaults_to_feature_branch_and_six_hour_ttl() -> None:
    args = parse_args(["deploy", "--repo-url", "https://example.com/repo.git"])

    assert args.branch == "feature/lucian-backend"
    assert args.ttl_minutes == 360
    assert args.preview_expiry_seconds == 21_600


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
