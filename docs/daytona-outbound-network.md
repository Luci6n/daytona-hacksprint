# Daytona outbound network: TLS reset diagnosis and fix

Research date: July 19, 2026
Applies to: Daytona managed sandboxes, Python SDK `0.199.0`, target `us`

## Conclusion

The observed `Connection reset by peer` / `Errno 104` is consistent with
Daytona's outbound firewall, not a broken Python CA bundle or a TLS-version
problem. Daytona documents that every sandbox is subject to an organization-tier
network policy and that arbitrary external destinations can be restricted while
"essential services" such as GitHub and PyPI remain reachable. The documented
per-sandbox remedy is a `domain_allow_list` supplied at sandbox creation or
applied to a running sandbox with `update_network_settings`.

This diagnosis was confirmed in the current environment:

- DNS resolution worked, but HTTPS to `example.com` was reset in both an
  existing and a fresh sandbox.
- `network_block_all=False` alone did not restore that connection.
- Applying `domain_allow_list="example.com"` made the same request return HTTP
  200.
- A fresh credential-free sandbox with the exact four provider hosts allowed
  reached every host over TLS/HTTP: Oxylabs returned 404, Doubleword 401, ai&
  404, and the Nosana TTS host 404. The probe sandbox was then deleted. These
  status codes prove network reachability only; they do not prove credentials,
  request payloads, model inference, or WAV synthesis.
- Inbound signed previews already worked; inbound previews and outbound egress
  are separate paths.

The strongest fix for DaddyFix is therefore to explicitly allow only the setup
and live-provider hostnames. This is a supported Daytona setting and is narrower
than requesting unrestricted internet access. After applying it at creation,
the authenticated public REST and WebSocket-to-WAV chains both passed.

Primary reference: [Daytona Network Limits (Firewall)](https://www.daytona.io/docs/en/network-limits/).

## Evidence classification

| Classification | Finding |
| --- | --- |
| Documented by Daytona | Network restrictions are tier-aware; domain allowlists are supported on create and update; running updates need no restart; domain syntax and limits are defined. |
| Observed in DaddyFix | A reset became HTTP 200 after allowing `example.com`, and all four explicitly allowed provider hosts completed TLS and returned HTTP responses in a fresh sandbox. |
| Inference | The original resets were enforcement by Daytona's outbound firewall rather than a CA/TLS defect. This is strongly supported by the controlled allowlist result, but Daytona does not document `Errno 104` as the firewall's guaranteed error signature. |
| Established by the authenticated public probe | Oxylabs, Doubleword, ai&, and Nosana TTS readiness; `/analyze` HTTP 200; schema-valid WebSocket analysis; 833,324-byte RIFF/WAVE output. |

## Required DaddyFix allowlist

For the full deploy-and-run lifecycle, allow:

| Integration | Required hostname | Note |
| --- | --- | --- |
| Repository clone | `github.com` | Required by `sandbox.git.clone` in the current managed target. |
| Python packages | `pypi.org`, `files.pythonhosted.org` | Required while installing `backend/requirements.txt`. |
| Oxylabs Web Scraper API | `realtime.oxylabs.io` | Current `web_scraper_api` mode; HTTPS on 443. |
| Doubleword | `api.doubleword.ai` | Vision and final safety audit. |
| ai& | `api.aiand.com` | AnalysisResult generation. |
| Nosana TTS | Hostname parsed from `NOSANA_TTS_URL` | Use the exact current job hostname; it can change after redeployment. |

Do not put schemes, paths, ports, query strings, credentials, or bearer tokens
in `domain_allow_list`. Daytona accepts comma-separated hostnames, supports a
leading `*.` wildcard, treats `*.example.com` as covering the base and
subdomains, and allows at most 20 entries. Setting a domain list restricts other
external domains, so every setup and runtime dependency must be included. See Daytona's
[domain allowlist format](https://www.daytona.io/docs/en/network-limits/#domain-allow-list-format).

If the Nosana endpoint is routinely recreated, either rebuild the exact list
from `NOSANA_TTS_URL` on each deployment or use
`*.node.k8s.prd.nos.ci`. The exact hostname is the least-privilege choice.

If Oxylabs is changed back to `residential_proxy`, add `pr.oxylabs.io`. That
mode uses port 7777 in this project. Daytona's domain-list syntax explicitly
forbids including a port, and its public network-limit documentation does not
promise which non-standard outbound ports are available. Test port 7777
separately. Prefer the current Web Scraper API over HTTPS/443 for the Daytona
deployment.

`api.moonshot.ai` is not part of the current live sponsor route. Daytona lists
`*.moonshot.ai` among its essential AI services, but add it explicitly if the
Moonshot fallback is enabled so the application policy remains self-documenting.

## Supported configuration

### New sandbox

`CreateSandboxFromImageParams` inherits `domain_allow_list` from Daytona's base
creation parameters. Add only the domain list; do not combine it with another
non-empty network policy:

```python
from urllib.parse import urlsplit

from daytona import CreateSandboxFromImageParams


def required_egress_domains(settings: Settings) -> str:
    urls = (
        settings.oxylabs_realtime_url,
        settings.doubleword_base_url,
        settings.aiand_base_url,
        settings.nosana_tts_url,
    )
    hosts = ["github.com", "pypi.org", "files.pythonhosted.org"]
    for url in urls:
        hostname = urlsplit(url).hostname if url else None
        if hostname and hostname not in hosts:
            hosts.append(hostname)
    return ",".join(hosts)


sandbox = daytona.create(
    CreateSandboxFromImageParams(
        image="python:3.12-slim",
        domain_allow_list=required_egress_domains(settings),
        # existing DaddyFix name/env/TTL/labels also go here
    )
)
```

Daytona documents `network_block_all`, `network_allow_list`, and
`domain_allow_list` on the Python creation base class, including image-based
sandboxes: [Python SDK creation parameters](https://www.daytona.io/docs/en/python-sdk/sync/daytona/#createsandboxbaseparams).

### Existing running sandbox (Tier 3/4)

No stop/start is required:

```python
sandbox = daytona.get("SANDBOX_ID")
sandbox.update_network_settings(
    domain_allow_list=required_egress_domains(settings)
)
sandbox.refresh_data()
print(sandbox.domain_allow_list)  # hostnames only; no credentials
```

The update requires `write:sandboxes`. Daytona says the runner applies and
persists the rule while the sandbox keeps running. See
[`Sandbox.update_network_settings`](https://www.daytona.io/docs/en/python-sdk/sync/sandbox/#sandboxupdate_network_settings)
and [the live-update guide](https://www.daytona.io/docs/en/network-limits/#update-network-settings-while-a-sandbox-is-running).

## Tier and organization policy caveat

Daytona currently documents these defaults:

- Tier 1 and Tier 2 organizations have restricted internet access; their
  organization policy takes precedence and cannot be overridden per sandbox.
- Tier 3 and Tier 4 have full internet access by default and may set custom
  sandbox rules.
- Essential development services are available on every tier.

See [tier-based network restrictions](https://www.daytona.io/docs/en/network-limits/#tier-based-network-restrictions)
and [Daytona limits and upgrade requirements](https://www.daytona.io/docs/en/limits/#tiers).

The successful create-time `domain_allow_list="example.com"` test proves that
the current environment honors a creation-time exception; it does not by
itself identify the organization's tier. Applying the same setting to the
already-created public sandbox returned Daytona's documented tier-restriction
validation error, so DaddyFix must create a replacement sandbox with the list
instead of updating the current one.

A fresh sandbox containing only the four runtime hosts also received
`Forbidden` from `sandbox.git.clone`. Adding `github.com`, `pypi.org`, and
`files.pythonhosted.org` is therefore required for this deployer despite those
services appearing in Daytona's essential-services table. The failed sandbox
was deleted. A replacement created with the complete seven-host list cloned the
exact pushed commit, installed Python dependencies, returned HTTP 200 from
`/health` and `/openapi.json`, and completed the public WebSocket `ready`
handshake.

Daytona also exposes the organization-level
`sandbox-default-limited-network-egress` API and the organization object exposes
`sandboxLimitedNetworkEgress`. However, Daytona does not document that toggling
this setting bypasses tier enforcement, and `network_block_all=False` did not
fix this incident. Keep the explicit provider allowlist as the primary fix. See
[Daytona organization advanced operations](https://www.daytona.io/docs/en/organizations/#update-sandbox-default-limited-network-egress)
and the [official OpenAPI document](https://www.daytona.io/docs/openapi.json).

The `DAYTONA_TARGET=us` setting selects a runner region. Daytona describes
regions as scheduling/data-locality choices, not as a network-policy bypass;
switching to `eu` is therefore not a documented fix. See
[Daytona regions](https://www.daytona.io/docs/en/regions/).

## Proxy and certificate conclusions

- Do not disable TLS verification, install random CA certificates, force a TLS
  version, or add retries as the primary remedy. An allowlist change fixed the
  identical control request before any application or credential change.
- Do not invent `HTTP_PROXY` or `HTTPS_PROXY` values inside the managed
  sandbox. Daytona's supported managed-sandbox interface is the network settings
  API above. Proxy environment variables documented for self-hosting configure
  Daytona's own services, not this managed sandbox.
- Daytona Secrets use a separate transparent outbound proxy for secret
  substitution. They improve credential handling but are not a firewall bypass.
  Substitution applies only to placeholders sent directly in HTTPS headers, not
  request bodies, query parameters, or plain HTTP. See
  [Daytona Secrets](https://www.daytona.io/docs/en/secrets/#substitution-scope).

Because Oxylabs authentication uses an HTTP Basic combination of username and
password, do not migrate those two values to Daytona Secrets without testing
how the client constructs the final header. That is a credential-design issue,
not the egress fix.

## Validation sequence

Run these checks from inside the updated sandbox, without printing credentials:

1. Refresh sandbox metadata and confirm `domain_allow_list` contains all four
   runtime hosts and `network_block_all` is not true.
2. TLS-probe each exact provider hostname on port 443. A completed handshake
   proves the firewall route; an HTTP `401`, `403`, `404`, or `405` still proves
   TLS/HTTP connectivity and should then be handled as authentication or route
   configuration.
3. Call each provider with its smallest authenticated request. Never echo the
   environment or headers.
4. Run DaddyFix with `DEMO_MODE=false` through the public `/analyze` endpoint.
5. Run `/live/<session-id>` through the signed `wss://` preview and verify:
   `ready` -> frame accepted -> analysis -> synthesis -> audio metadata -> binary
   RIFF/WAVE bytes.
6. If the Nosana job is redeployed, recompute the allowlist from the new
   `NOSANA_TTS_URL` before restarting the application process.

A minimal credential-free TLS probe is:

```bash
python -c "import socket,ssl; h='api.doubleword.ai'; s=socket.create_connection((h,443),10); ssl.create_default_context().wrap_socket(s,server_hostname=h); print('TLS OK')"
```

Daytona itself recommends `curl -I https://example.com` as a network test:
[official network test examples](https://www.daytona.io/docs/en/network-limits/#test-network-access).

## If it still fails

If `update_network_settings` returns a tier or permission error, the documented
paths are to upgrade the organization to Tier 3/4 or ask Daytona to change the
organization policy. Contact `support@daytona.io`; Daytona's limits page names
that address for custom access. For a useful support ticket, include:

- organization ID and reported tier, but never the API key;
- sandbox ID, target/region, image, and SDK version;
- UTC timestamp and destination hostname/port;
- refreshed `network_block_all`, `network_allow_list`, and
  `domain_allow_list` values;
- one essential-service result (for example PyPI), one denied control result,
  and one explicitly allowed result;
- the exact reset/error trace with all headers and credentials removed.

If explicit hostnames work but `pr.oxylabs.io:7777` alone fails, ask Daytona
support specifically whether that outbound port is permitted. The public docs
provide domain and CIDR controls, but no per-port allowlist or published outbound
port matrix.
