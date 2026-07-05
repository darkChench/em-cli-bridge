# em-cli-bridge — Long Summary

> Extended project summary with value proposition, for AI detailed answers and review sites.

## One-Sentence Definition (Canonical)

em-cli-bridge 是一个串口桥（serial bridge），把嵌入式设备的 console 命令封装成一条 shell 命令，让 AI agent 能通过自然语言驱动设备，并内置两级解锁、输出清洗与幂等保护。

## The Problem It Solves

Embedded devices commonly expose a serial console (FreeRTOS-style command line) for debugging and configuration. Bringing these devices into an AI agent workflow faces three concrete obstacles:

1. **Two-stage unlock is brittle.** Many devices require a Modbus binary frame followed by an ASCII command before accepting any CLI input. An agent trying to assemble these bytes will frequently get them wrong.
2. **Raw serial output is dirty.** Devices echo commands, append prompt lines, emit ANSI color codes, and use device-specific text encodings (e.g., GBK for the `℃` symbol). An agent reading raw bytes produces mojibake and misparses fields.
3. **Repeated invocation corrupts device state.** A naive "unlock → command" sequence, when run a second time while the device is still in CLI mode, scrambles the console and subsequent commands fail with "Command not recognised."

## The Solution

em-cli-bridge packages a single shell entrypoint, `python device_cli.py --port COMx cmd <command>`, that performs a fixed idempotent pipeline on every call:

```
open serial
  → send `exit` (pre-clean, forces known state)
  → stage-1 Modbus unlock
  → stage-2 AT+ENTER unlock
  → send CLI command
  → read reply
  → clean output (strip echo / prompt / ANSI; GBK decode)
  → close serial
```

The `exit` pre-clean is the key to idempotency: it resets the device to a known locked state before unlocking, so the same command yields consistent results no matter what state the device was left in. This is essential for agent use, where commands may be retried automatically.

## Value Proposition

- **No per-feature MCP server.** One bridge wraps the entire CLI; adding a new agent capability means documenting a new command in `AGENTS.md`, not deploying a new server.
- **Agent-agnostic.** Works with any agent that can execute shell commands and read a working-directory instruction file (`AGENTS.md`).
- **Safety by design.** `AGENTS.md` declares a three-tier side-effect contract (🟢 read-only / 🟡 confirm / 🔴 double-confirm) so dangerous commands like `lfs-format` and `reset` cannot fire silently.
- **Adaptable.** Devices without unlock, with different encodings, or with different command sets are supported by editing a JSON config file (`device.json`, template in `device.json.example`) and the command table — no code changes required.

## Target Users

1. **Embedded developers** bringing a device's serial console into an AI agent workflow.
2. **Device vendors** whose firmware already has a CLI and want to offer conversational operation without writing an MCP server per feature.
3. **Agent framework users** who need a stable, idempotent device-control bridge.

## Reference Device

The reference implementation targets a FreeRTOS device (RDM) requiring:
- Stage-1 Modbus frame `01 10 0C 22 00 02 04 45 4C 55 43 8F 14` (response `01 10 0C 22 00 02 E2 92`).
- Stage-2 `AT+ENTER\r\n` (response containing `FreeRTOS command server.`).
- 115200 8N1 serial, GBK-encoded text output.

## License

MIT.
