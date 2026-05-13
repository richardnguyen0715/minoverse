use std::path::PathBuf;
use std::time::Duration;

/// Project root embedded at compile time by build.rs.
const PROJECT_ROOT: &str = env!("MINOVERSE_PROJECT_ROOT");

fn project_root() -> PathBuf {
    PathBuf::from(PROJECT_ROOT)
}

/// Returns ~/.minoverse, creating it if necessary.
fn minoverse_dir() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| String::from("/Users"));
    let dir = PathBuf::from(home).join(".minoverse");
    let _ = std::fs::create_dir_all(&dir);
    dir
}

/// Check if a TCP port is accepting connections (non-blocking, 400 ms timeout).
fn is_port_open(port: u16) -> bool {
    std::net::TcpStream::connect_timeout(
        &format!("127.0.0.1:{}", port).parse().unwrap(),
        Duration::from_millis(400),
    )
    .is_ok()
}

// ── Tauri commands ────────────────────────────────────────────────────────────

#[tauri::command]
fn get_system_info() -> serde_json::Value {
    serde_json::json!({
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "project_root": PROJECT_ROOT,
    })
}

#[tauri::command]
fn get_project_root() -> String {
    PROJECT_ROOT.to_string()
}

#[tauri::command]
fn check_api_health() -> bool {
    is_port_open(8000)
}

#[tauri::command]
fn check_web_health() -> bool {
    is_port_open(3000)
}

/// Returns the last non-empty line from ~/.minoverse/startup.log.
#[tauri::command]
fn get_startup_log() -> String {
    let log_path = minoverse_dir().join("startup.log");
    std::fs::read_to_string(&log_path)
        .unwrap_or_default()
        .lines()
        .rev()
        .find(|l| !l.trim().is_empty())
        .unwrap_or("Starting services…")
        .to_string()
}

/// Opens ~/.minoverse/ in Finder so the user can inspect logs.
#[tauri::command]
fn open_logs_dir() -> Result<(), String> {
    let dir = minoverse_dir();
    std::process::Command::new("open")
        .arg(&dir)
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}

/// Read AI_PROVIDER from apps/api/.env (defaults to "ollama").
#[tauri::command]
fn get_ai_provider() -> String {
    let env_path = project_root().join("apps/api/.env");
    if let Ok(content) = std::fs::read_to_string(&env_path) {
        for line in content.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with("AI_PROVIDER=") {
                return trimmed.trim_start_matches("AI_PROVIDER=").trim().to_lowercase();
            }
        }
    }
    "ollama".to_string()
}

/// Write AI_PROVIDER into apps/api/.env (upsert).
#[tauri::command]
fn set_ai_provider(provider: String) -> Result<(), String> {
    let env_path = project_root().join("apps/api/.env");
    let content = std::fs::read_to_string(&env_path).unwrap_or_default();
    let mut found = false;
    let mut lines: Vec<String> = content
        .lines()
        .map(|l| {
            if l.trim().starts_with("AI_PROVIDER=") {
                found = true;
                format!("AI_PROVIDER={}", provider)
            } else {
                l.to_string()
            }
        })
        .collect();
    if !found {
        lines.push(format!("AI_PROVIDER={}", provider));
    }
    std::fs::write(&env_path, lines.join("\n") + "\n")
        .map_err(|e| format!("Failed to write .env: {}", e))
}

/// Check if LM Studio is reachable (port 1234).
#[tauri::command]
fn check_lmstudio_health() -> bool {
    is_port_open(1234)
}

/// Read optional service toggles from ~/.minoverse/services.conf.
#[tauri::command]
fn get_service_toggles() -> serde_json::Value {
    let conf_path = minoverse_dir().join("services.conf");
    let content = std::fs::read_to_string(&conf_path).unwrap_or_default();
    let worker = !content.contains("ENABLE_WORKER=false");
    let watcher = !content.contains("ENABLE_WATCHER=false");
    serde_json::json!({ "worker": worker, "watcher": watcher })
}

/// Write optional service toggles to ~/.minoverse/services.conf.
#[tauri::command]
fn set_service_toggles(worker: bool, watcher: bool) -> Result<(), String> {
    let conf_path = minoverse_dir().join("services.conf");
    let content = format!(
        "ENABLE_WORKER={}\nENABLE_WATCHER={}\n",
        if worker { "true" } else { "false" },
        if watcher { "true" } else { "false" },
    );
    std::fs::write(&conf_path, content).map_err(|e| e.to_string())
}

#[tauri::command]
async fn navigate_to_app(window: tauri::WebviewWindow) -> Result<(), String> {
    window
        .navigate("http://localhost:3000".parse().unwrap())
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn open_vault_dir(path: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    std::process::Command::new("open")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    #[cfg(target_os = "linux")]
    std::process::Command::new("xdg-open")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    #[cfg(target_os = "windows")]
    std::process::Command::new("explorer")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn start_services() -> Result<String, String> {
    let root = project_root();
    let script = root.join("scripts/start.sh");
    std::process::Command::new("bash")
        .arg(&script)
        .current_dir(&root)
        .spawn()
        .map_err(|e| format!("Failed to launch start script: {}", e))?;
    Ok("Services starting…".to_string())
}

#[tauri::command]
async fn stop_services() -> Result<String, String> {
    let root = project_root();
    let script = root.join("scripts/stop.sh");
    let out = std::process::Command::new("bash")
        .arg(&script)
        .current_dir(&root)
        .output()
        .map_err(|e| format!("Failed to run stop script: {}", e))?;
    if out.status.success() {
        Ok("Services stopped".to_string())
    } else {
        Err(String::from_utf8_lossy(&out.stderr).to_string())
    }
}

// ── App entry point ───────────────────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|_app| {
            let root = project_root();
            let script = root.join("scripts/start.sh");

            // Build a comprehensive PATH that covers all common macOS locations.
            // This is critical when the app is launched from Finder / Dock —
            // the inherited environment has only /usr/bin:/bin:/usr/sbin:/sbin.
            let home = std::env::var("HOME").unwrap_or_else(|_| String::from("/Users"));
            let extra_path = format!(
                "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:\
                 {home}/.cargo/bin:{home}/.local/bin"
            );

            // Create ~/.minoverse/ and a fresh startup.log for this launch.
            let log_dir = PathBuf::from(&home).join(".minoverse");
            let _ = std::fs::create_dir_all(&log_dir);
            let log_path = log_dir.join("startup.log");

            // Shell command: extend PATH then exec start.sh
            let script_str = script.to_string_lossy().to_string();
            let run_cmd = format!(
                r#"export PATH="{extra_path}:$PATH"; exec bash '{script_str}'"#,
            );

            // Spawn with stdout+stderr both going to startup.log
            if let Ok(log_file) = std::fs::OpenOptions::new()
                .create(true)
                .write(true)
                .truncate(true)
                .open(&log_path)
            {
                if let Ok(log_file2) = log_file.try_clone() {
                    std::process::Command::new("bash")
                        .args(["-c", &run_cmd])
                        .current_dir(&root)
                        .stdout(log_file)
                        .stderr(log_file2)
                        .spawn()
                        .ok();
                }
            } else {
                // Fallback: spawn without log capture
                std::process::Command::new("bash")
                    .args(["-c", &run_cmd])
                    .current_dir(&root)
                    .spawn()
                    .ok();
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_system_info,
            get_project_root,
            check_api_health,
            check_web_health,
            check_lmstudio_health,
            get_startup_log,
            get_ai_provider,
            set_ai_provider,
            get_service_toggles,
            set_service_toggles,
            open_logs_dir,
            navigate_to_app,
            open_vault_dir,
            start_services,
            stop_services,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|_app, event| {
            if let tauri::RunEvent::Exit = event {
                // Stop all services when the application is closed.
                let root = project_root();
                let stop_script = root.join("scripts/stop.sh");
                let home = std::env::var("HOME").unwrap_or_else(|_| String::from("/Users"));
                let extra_path = format!(
                    "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:\
                     {home}/.cargo/bin:{home}/.local/bin"
                );
                let cmd = format!(
                    r#"export PATH="{extra_path}:$PATH"; bash '{}'"#,
                    stop_script.to_string_lossy()
                );
                // Run synchronously so services are fully stopped before process exits.
                let _ = std::process::Command::new("bash")
                    .args(["-c", &cmd])
                    .current_dir(&root)
                    .output();
            }
        });
}

