# Maintainers

This project is owned and maintained by **The DevSec Blueprint**.

---

## Ownership

| | |
|---|---|
| **Owner** | The DevSec Blueprint |
| **Organization** | [github.com/devsecblueprint](https://github.com/devsecblueprint) |
| **License** | [MIT](LICENSE) |
| **Trademarks and curriculum** | Not covered by the MIT grant — see [`docs/legal/TRADEMARKS.md`](docs/legal/TRADEMARKS.md) |

The MIT license applies to this implementation — the rule catalog, skill definition,
references, examples, and scripts. **No commercial authorization is required to use,
modify, or distribute it.**

---

## Responsibilities

Maintainers:

- Review and merge contributions per [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Guard the two standing policies: curriculum-first, and commands-stay-thin
- Enforce rule ID stability — deprecate, never renumber, never reuse
- Keep the catalog aligned with DSB curriculum as it evolves
- Cut releases and maintain [`CHANGELOG.md`](CHANGELOG.md)

Maintainers do **not** decide DSB engineering methodology in this repository. That lives
in the curriculum; this repository implements it.

---

## Decision-making

| Change | Requires |
|---|---|
| Typos, formatting, broken links | One maintainer approval |
| New or corrected examples | One maintainer approval |
| Framework mapping corrections | One maintainer approval |
| New rule, or changed requirement text | Maintainer approval + linked curriculum material |
| Rule deprecation | Maintainer approval + `CHANGELOG.md` entry |
| New rule family | Maintainer consensus — taxonomy changes affect every consumer |
| License or trademark terms | DSB ownership decision, not a maintainer decision |

---

## Releases

Semantic versioning, with a Pre-1.0 caveat:

- **Pre-1.0** — the catalog's shape is still settling. Minor versions may add families,
  change enforcement defaults, and refine applicability conditions.
- **Rule IDs are stable regardless of version.** This is the compatibility guarantee that
  matters, because rule IDs travel into other organizations' pipelines and exception
  records.

Release steps:

1. Validation passes: `uv run --with pyyaml python scripts/validate_rules.py`
2. `CHANGELOG.md` updated with the version and date
3. Version bumped in `.claude-plugin/plugin.json`
4. Tag `vX.Y.Z` and publish the release

---

## Contact

- **Issues and proposals** — open an issue in this repository
- **Security concerns** — see [`SECURITY.md`](SECURITY.md)
- **Community** — the DSB Discord, linked from the
  [main DSB repository](https://github.com/devsecblueprint/devsecblueprint)
- **Trademark, branding, or curriculum licensing** — reach The DevSec Blueprint directly;
  these are outside the MIT grant
