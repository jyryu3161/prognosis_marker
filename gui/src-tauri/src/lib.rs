mod commands;
mod models;

use commands::analysis::AnalysisProcess;
use std::sync::Mutex;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .manage(AnalysisProcess {
            child: Mutex::new(None), // stores PID
        })
        .invoke_handler(tauri::generate_handler![
            // Runtime
            commands::runtime::runtime_detect,
            // File system
            commands::fs_ops::fs_pick_file,
            commands::fs_ops::fs_pick_directory,
            commands::fs_ops::fs_read_csv_header,
            commands::fs_ops::fs_read_image,
            commands::fs_ops::fs_list_output_plots,
            commands::fs_ops::fs_save_file,
            commands::fs_ops::fs_open_directory,
            // Config
            commands::config::config_load_yaml,
            commands::config::config_save_yaml,
            commands::config::config_list_presets,
            commands::config::config_load_preset,
            commands::config::config_validate,
            // Analysis
            commands::analysis::analysis_run,
            commands::analysis::analysis_cancel,
            // Open Targets
            commands::opentargets::opentargets_search_diseases,
            commands::opentargets::opentargets_fetch_genes,
            commands::opentargets::opentargets_list_cached,
            commands::opentargets::opentargets_count_filtered,
            // Runtime
            commands::runtime::runtime_check_deps,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
