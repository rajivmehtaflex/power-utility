# CLI help versus web documentation: evidence map

Use this reference for CLI-study tasks where the installed executable must be compared with current Internet documentation.

## Probe recipe

```bash
command -v <cli>
<cli> --version
<cli> --help
for command in install remove uninstall update list config auth; do
  <cli> "$command" --help
done
```

Record the absolute binary path, version, exit codes, and the exact help text before interpreting documentation differences. If the shell has multiple package managers, verify which installation owns the binary.

## Evidence classification

| Classification | Meaning | Recommendation |
|---|---|---|
| Exact match | Local help and exact-version docs agree | Use normally |
| Local-only | The executable accepts or advertises something the prose omits | Prefer local help; note the documentation gap |
| Exact-version docs-only | The versioned docs describe something absent locally | Verify source/build provenance before recommending it |
| Latest-only | `latest`/`main` docs add a feature absent from the installed version | Treat as version drift; upgrade or avoid the flag |
| Documentation expansion | Docs explain state, security, or side effects not visible in help | Include the caveat in the report |

## Required report fields

For each top-level command, capture:

- objective;
- exact syntax and safe example;
- global versus project-local state;
- authentication/network/file/process side effects;
- trust and security implications;
- whether the behavior came from local help, exact-version documentation, current documentation, or implementation evidence.

Keep package-manager installation separate from application-level package management. For example, `bun add -g <cli-package>` installs a CLI, while a subcommand such as `<cli> install <source>` may manage extensions or resources owned by the application.

## Pi 0.84.1 example

The installed binary was `/Users/rajivmehtapy/.bun/bin/pi`, version `0.84.1`. Local help exposed package commands (`install`, `remove`, `uninstall`, `update`, `list`, `config`), authentication commands (`auth print-api-key`, `auth print-bearer-token`, `auth check`), `--session-id`, and the standard interactive/print/JSON/RPC modes.

The exact `v0.84.1` usage page matched the package commands, modes, tool controls, resource flags, trust switches, and session options, but did not enumerate `--session-id` in its prose. The `v0.84.1` changelog confirmed the authentication readiness and credential-export commands.

The current `latest` usage page additionally listed `--use-theme`, which was absent from the local `0.84.1` help and the exact `v0.84.1` usage page. Classify that as latest-only/version drift rather than assuming the installed binary accepts it. The exact local help remains the operational contract.

The official Pi package documentation adds details not visible in `--help`: global state under `~/.pi/agent`, project state under `.pi/`, package locations, pinned npm/Git references, project trust behavior, and the warning that extensions and skills execute with substantial system access.

## Representative primary sources

- [Pi usage, latest](https://pi.dev/docs/latest/usage)
- [Pi packages, latest](https://pi.dev/docs/latest/packages)
- [Pi quickstart, latest](https://pi.dev/docs/latest/quickstart)
- [Pi v0.84.1 usage](https://github.com/earendil-works/pi/blob/v0.84.1/packages/coding-agent/docs/usage.md)
- [Pi v0.84.1 changelog](https://github.com/earendil-works/pi/blob/v0.84.1/packages/coding-agent/CHANGELOG.md)
