use crate::models::config::DataFileInfo;
use crate::models::error::AppError;
use std::collections::HashMap;
use std::fs;
use std::io::{BufRead, BufReader};
use tauri_plugin_dialog::DialogExt;

#[tauri::command]
pub async fn fs_pick_file(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let file = app
        .dialog()
        .file()
        .add_filter("CSV files", &["csv"])
        .add_filter("All files", &["*"])
        .blocking_pick_file();

    Ok(file
        .and_then(|f| f.into_path().ok())
        .map(|p| p.to_string_lossy().to_string()))
}

#[tauri::command]
pub async fn fs_pick_directory(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let dir = app.dialog().file().blocking_pick_folder();
    Ok(dir
        .and_then(|d| d.into_path().ok())
        .map(|p| p.to_string_lossy().to_string()))
}

#[tauri::command]
pub async fn fs_read_csv_header(path: String) -> Result<DataFileInfo, String> {
    let file = fs::File::open(&path).map_err(|e| {
        String::from(AppError::file_not_found(&format!("{}: {}", path, e)))
    })?;
    let reader = BufReader::new(file);
    let mut lines = reader.lines();

    // Read header
    let header_line = lines
        .next()
        .ok_or_else(|| String::from(AppError::csv_parse_error("Empty CSV file")))?
        .map_err(|e| String::from(AppError::csv_parse_error(&e.to_string())))?;

    let columns: Vec<String> = header_line
        .split(',')
        .map(|s| s.trim().trim_matches('"').to_string())
        .collect();

    // Read preview (first 5 rows) and count total rows
    let mut preview: HashMap<String, Vec<String>> = HashMap::new();
    for col in &columns {
        preview.insert(col.clone(), Vec::new());
    }

    let mut row_count = 0;
    for line_result in lines {
        let line = line_result
            .map_err(|e| String::from(AppError::csv_parse_error(&e.to_string())))?;
        row_count += 1;

        if row_count <= 5 {
            let values: Vec<&str> = line.split(',').collect();
            for (i, col) in columns.iter().enumerate() {
                if let Some(val) = values.get(i) {
                    if let Some(col_preview) = preview.get_mut(col) {
                        col_preview.push(val.trim().trim_matches('"').to_string());
                    }
                }
            }
        }
    }

    Ok(DataFileInfo {
        path,
        row_count,
        columns,
        preview,
    })
}

#[tauri::command]
pub async fn fs_read_image(path: String) -> Result<String, String> {
    let bytes = fs::read(&path).map_err(|e| {
        String::from(AppError::file_not_found(&format!("{}: {}", path, e)))
    })?;
    use base64::Engine;
    Ok(base64::engine::general_purpose::STANDARD.encode(&bytes))
}

/// Save a file to user-chosen location via save dialog
#[tauri::command]
pub async fn fs_save_file(
    app: tauri::AppHandle,
    source_path: String,
    default_name: String,
) -> Result<Option<String>, String> {
    let ext = std::path::Path::new(&default_name)
        .extension()
        .map(|e| e.to_string_lossy().to_string())
        .unwrap_or_default();

    let filter_name = match ext.as_str() {
        "svg" => "SVG Image",
        "tiff" => "TIFF Image",
        "png" => "PNG Image",
        "pdf" => "PDF Document",
        "csv" => "CSV File",
        _ => "All Files",
    };

    let dest = app
        .dialog()
        .file()
        .set_file_name(&default_name)
        .add_filter(filter_name, &[&ext])
        .blocking_save_file();

    match dest.and_then(|fp| fp.into_path().ok()) {
        Some(dest_path) => {
            let dest_str = dest_path.to_string_lossy().to_string();
            fs::copy(&source_path, &dest_str).map_err(|e| {
                format!("Failed to save file: {}", e)
            })?;
            Ok(Some(dest_str))
        }
        None => Ok(None), // User cancelled
    }
}

/// Open a directory in the system file manager (Finder on macOS)
#[tauri::command]
pub async fn fs_open_directory(path: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open directory: {}", e))?;
    }
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open directory: {}", e))?;
    }
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open directory: {}", e))?;
    }
    Ok(())
}

#[tauri::command]
pub async fn fs_list_output_plots(output_dir: String) -> Result<Vec<String>, String> {
    let base = std::path::Path::new(&output_dir);
    if !base.exists() {
        return Ok(Vec::new());
    }

    let image_extensions = ["png", "tiff", "svg", "pdf"];
    let mut plots = Vec::new();

    // Search in output_dir root and common subdirectories (figures/, plots/)
    let search_dirs: Vec<std::path::PathBuf> = vec![
        base.to_path_buf(),
        base.join("figures"),
        base.join("plots"),
    ];

    for dir in &search_dirs {
        if !dir.exists() {
            continue;
        }
        let entries = match fs::read_dir(dir) {
            Ok(e) => e,
            Err(_) => continue,
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(ext) = path.extension() {
                let ext_str = ext.to_string_lossy().to_lowercase();
                if image_extensions.contains(&ext_str.as_str()) {
                    // Return path relative to output_dir
                    if let Ok(rel) = path.strip_prefix(base) {
                        plots.push(rel.to_string_lossy().to_string());
                    }
                }
            }
        }
    }

    // Sort: prefer SVG over TIFF (SVG renders in browser, TIFF doesn't)
    plots.sort_by(|a, b| {
        let a_svg = a.ends_with(".svg");
        let b_svg = b.ends_with(".svg");
        match (a_svg, b_svg) {
            (true, false) => std::cmp::Ordering::Less,
            (false, true) => std::cmp::Ordering::Greater,
            _ => a.cmp(b),
        }
    });

    Ok(plots)
}
