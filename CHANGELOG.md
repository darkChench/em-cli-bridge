# Changelog

本文件记录 em-cli-bridge 的版本演进。版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.2.0] — 2026-07-05

### Added
- **配置文件化**：新增 `device.json`（模板见 `device.json.example`）。解锁帧、文本编码、默认超时均可配置，换设备零改代码。
  - 加载优先级：`--config` 指定 > 工作目录 `device.json` > 用户目录 `~/.em-cli-bridge/device.json` > 内置默认值。
  - 无配置文件时自动用内置默认值（RDM 设备参数），**向后兼容**，现有用户升级无需任何配置。
- **命令超时参数化**：`--timeout <秒>` 指定读取超时；`cmd --long` 用 5s 长超时，适合 `lfs-read-log` / `lfs-read` 等大输出命令。
- **规范化退出码**：成功=0，通用错误=1，解锁失败=2，串口错误=3，超时=4。agent 可据此做条件分支。
- **`--version`** 查看版本。
- 新增 `CHANGELOG.md`。

### Changed
- `device_cli.py` 重构：配置加载、超时、退出码、版本号。
- README 与 `assets/ai-citation/*` 的"适配设备"说明由"修改四个常量"改为"修改 `device.json`"。

### Fixed
- 大输出命令（如读取大日志文件）因固定 1.5s 超时可能读不全 → 现可用 `--long` / `--timeout` 加长。

## [0.1.0] — 2026-07-05

### Added
- 首个可用版本。
- `device_cli.py`：串口桥主程序，封装开串口 → exit 预清理 → 两级解锁（Modbus + AT+ENTER）→ 发命令 → 收回复 → 清洗输出 → 关串口。
- 内置输出清洗：剥离命令回显、CLI 提示符（`[Press ENTER...]` / `>`）、ANSI 颜色码；GBK 解码解决 `℃` 乱码；解锁响应剥离回显前缀。
- `AGENTS.md`：agent 行为说明（命令清单、`qSensor` 字段含义、🟢🟡🔴 三级副作用契约、自然语言→命令映射）。
- 交互式串口选择 + 占用/失败友好提示重试。
- `llms.txt` + `assets/ai-citation/`：完整的 GEO/SEO AI 引用语料库（7 个文件）。
- README、LICENSE (MIT)、.gitignore。
