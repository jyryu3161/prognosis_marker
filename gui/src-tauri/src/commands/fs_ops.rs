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

#[tauri::command]
pub async fn fs_list_output_plots(output_dir: String) -> Result<Vec<String>, String> {
    let dir = std::path::Path::new(&output_dir);
    if !dir.exists() {
        return Ok(Vec::new());
    }

    let entries =
        fs::read_dir(dir).map_err(|e| format!("Cannot read output dir: {}", e))?;

    let mut plots = Vec::new();
    for entry in entries.flatten() {
        let path = entry.path();
        if let Some(ext) = path.extension() {
            let ext_str = ext.to_string_lossy().to_lowercase();
            if ext_str == "png" || ext_str == "tiff" || ext_str == "svg" || ext_str == "pdf" {
                if let Some(name) = path.file_name() {
                    plots.push(name.to_string_lossy().to_string());
                }
            }
        }
    }

    plots.sort();
    Ok(plots)
}
