fn main() {
    // Embed the project root (3 levels up from src-tauri/) at compile time.
    // This lets the packaged .app know where to find scripts/start.sh at runtime.
    let manifest = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let project_root = manifest
        .parent()
        .unwrap() // apps/desktop
        .parent()
        .unwrap() // apps
        .parent()
        .unwrap(); // repo root
    println!(
        "cargo:rustc-env=MINOVERSE_PROJECT_ROOT={}",
        project_root.display()
    );
    tauri_build::build()
}
