# Codebook for pre-commit

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![pre-commit](https://img.shields.io/badge/pre--commit-FAB040?style=flat-square&logo=precommit&logoColor=white)

Run the official [Codebook](https://github.com/blopker/codebook) executable without a
global installation or a Rust compiler. Python 3.10 or newer is required.

```yaml
repos:
  - repo: https://github.com/themakunga/codebook-pre-commit
    rev: v0.3.42.post1
    hooks:
      - id: codebook
        args: [--suggest]
        types: [markdown]
```

The first run downloads the official binary for macOS, Linux or Windows on x86_64
or ARM64, checks its pinned SHA-256, and caches it inside the isolated pre-commit
Python environment. Subsequent runs reuse that binary. No Python runtime
dependencies are needed.

Codebook reads `codebook.toml` or `.codebook.toml` from your project and preserves
its lint exit status. The first run also needs network access for Codebook's
dictionaries. Updates require a new adapter revision with updated checksums.

To report spelling errors without blocking commits, set
`args: [--allow-failure, --suggest]` and `verbose: true`. Download, integrity and
execution errors still fail the hook. The default remains strict.

The executable comes from upstream releases and remains subject to Codebook's
license. This repository is an independent adapter.

Run the adapter tests with `python -m unittest discover -s tests`.

## Repository reference

| Path                                               | Purpose                     |
| -------------------------------------------------- | --------------------------- |
| [`codebook_pre_commit.py`](codebook_pre_commit.py) | Project reference           |
| [`pyproject.toml`](pyproject.toml)                 | Python project metadata     |
| [`tests/`](tests/)                                 | Tests and regression checks |
| [`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml) | Project configuration       |

The default branch is `main`. Use the tracked manifests and scripts above
when preparing changes; keep local credentials and generated files out of commits.
