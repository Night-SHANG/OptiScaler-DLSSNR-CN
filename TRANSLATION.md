# Translation maintenance

## Resource model

The localization pipeline keeps two persisted source inventories and one shared Chinese store:

- `master/catalog.json`, `master/en-US.json`, `master/pending.json`: current upstream `master`.
- `stable/catalog.json`, `stable/en-US.json`, `stable/pending.json`: current latest stable tag.
- `zh-CN.json`: shared translations tied to the exact English `source_hash`.
- `translation-memory.zh-CN.json`: reviewed exact-source translations used to seed either channel.
- `glossary.json`: stable product terminology supplied to optional machine translation.

The same English source receives the same deterministic key in both channels. If upstream wording changes, the new wording receives a new key; the older stable wording and translation remain valid instead of being overwritten.

## States

A valid live Chinese entry has one of these states:

- `reviewed`: human-confirmed. Automation must never overwrite `text`.
- `machine_translated`: generated candidate accepted for runtime use but still reviewable.

Missing or stale translations use English at runtime. A reviewed entry whose upstream English changes remains preserved with its old source hash; an automatic translator may write a separate `candidate`, but it may not replace the reviewed text.

Example:

```json
{
  "ui.auto.abcd1234": {
    "text": "启用帧生成",
    "state": "reviewed",
    "source_hash": "..."
  }
}
```

## Incremental scanning

Run:

```bash
python tools/scan_ui.py --source _upstream --channel master --update --report reports/master-localization-scan.md
python tools/scan_ui.py --source _stable --channel stable --update --report reports/stable-localization-scan.md
```

Keys are immutable and derived from the exact English source. Exact existing sources retain their key. A highly similar replacement in the same UI scope is reported as a changed string, but receives a new source-derived key so master and stable can safely keep different wording at the same time. Removed catalog entries stay marked obsolete so translation history is not silently destroyed.

## Validation rules

`python tools/check_localization.py --channel all` verifies both persisted inventories:

- catalog/source hashes;
- `en-US` parity;
- allowed translation states;
- printf placeholders (`%s`, `%.2f`, etc.);
- `std::format` placeholders (`{0}`, `{name:...}`);
- exact preservation of ImGui `##hidden-id` suffixes.

A missing translation is not a build error: English fallback is required behavior. A structurally invalid translation is a build error.

## Glossary

Use the maintained terminology in `Localization/glossary.json`. Examples:

- Frame Generation → 帧生成
- Upscaling → 超分辨率
- Ray Reconstruction → 光线重建
- Balanced → 均衡
- Ultra Performance → 超级性能

Do not translate product/API/protocol/file names such as `DLSS`, `FSR`, `XeSS`, `DirectX`, `Vulkan`, DLL names or C++ identifiers. They can remain inside an otherwise translated sentence.

## Optional automatic translation

Set these GitHub Actions Secrets only if incremental machine translation is wanted:

- `TRANSLATION_API_URL`: an OpenAI-compatible Chat Completions endpoint URL.
- `TRANSLATION_API_KEY`
- `TRANSLATION_MODEL`

Then run:

```bash
python tools/translate_missing.py
```

The tool sends only current missing/changed source strings plus the glossary. It never sends the whole language pack for retranslation and never overwrites a `reviewed` translation. Secrets are read only from environment variables and are never written to the repository.

Without these secrets, the command exits successfully, keeps entries in each channel's `pending.json`, and runtime falls back to English.

## Reviewing a changed string

When a source changes, inspect the matching channel `pending.json` and any generated `candidate`. After confirming the new wording, set `text` to the approved translation, set `source_hash` to the new hash from `pending.json`, set `state` to `reviewed`, then run:

```bash
python tools/update_translation_memory.py
python tools/check_localization.py --strict
```

The first command updates only fresh `reviewed` entries in translation memory. Machine-translated entries never enter the reviewed memory automatically.

## Fork-specific UI

扫描范围包含 `OptiScaler/dlssnr/**`。普通 OptiScaler 文本复用共享中文；Dagherbou/OptiScaler_DLSSNR 新增文本只在首次发现或源文变化时进入待翻译列表。
