# Codebook for pre-commit

Run the official [Codebook](https://github.com/blopker/codebook) executable without a
global installation or a Rust compiler. Python 3.10 or newer is required.

```yaml
repos:
  - repo: https://github.com/themakunga/codebook-pre-commit
    rev: v0.3.42
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

The executable comes from upstream releases and remains subject to Codebook's
license. This repository is an independent adapter.

Run the adapter tests with `python -m unittest discover -s tests`.
