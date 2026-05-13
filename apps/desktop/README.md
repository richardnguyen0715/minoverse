# Minoverse Desktop

Tauri v2 desktop wrapper for Minoverse web UI.

## Prerequisites

- [Rust + Cargo](https://rustup.rs/) (stable toolchain)
- [Tauri CLI v2](https://tauri.app/): `cargo install tauri-cli --version ^2.0`
- Node.js 20+

## Development

```bash
# From repo root
make desktop-install   # install npm deps
make desktop-dev       # run in dev mode (loads http://localhost:3000)
make desktop-build     # build production binary
```

## Commands (Tauri IPC)

| Command | Description |
|---|---|
| `get_system_info` | Returns OS/arch info |
| `check_api_health` | Pings localhost:8000/health |
| `open_vault_dir(path)` | Opens path in OS file manager |
