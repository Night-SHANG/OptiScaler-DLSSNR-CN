# Contributing

Contributions are welcome for translation corrections, scanner coverage and integration fixes.

Before opening a pull request:

```bash
python -m compileall -q tools tests
python -m unittest discover -s tests -v
python tools/check_localization.py --channel all --strict
python tools/update_translation_memory.py --check
python tools/generate_cpp.py --channel master --out /tmp/Strings.master.generated.h
python tools/generate_cpp.py --channel stable --out /tmp/Strings.stable.generated.h
```

For translation changes, keep technical names unchanged, follow `Localization/glossary.json`, preserve format placeholders and preserve ImGui `##` suffixes exactly. Mark manually confirmed translations as `reviewed`, then run `python tools/update_translation_memory.py` before committing.

For upstream integration changes, do not bypass a failing anchor by replacing broad source regions or forcing a Git merge. Update the smallest deterministic adapter in `tools/localize_source.py`, add/adjust a fixture test, and verify a clean Windows Release build against the affected official OptiScaler ref.

Do not commit API keys, generated `_upstream/` source trees, local build outputs or redistributed third-party binaries to this maintenance repository.
