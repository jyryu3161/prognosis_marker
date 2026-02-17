use crate::models::error::AppError;
use std::io::{BufRead, BufReader};
use std::sync::Mutex;
use tauri::{Emitter, Manager, State};

pub struct AnalysisProcess {
    pub child: Mutex<Option<u32>>, // Store PID for cancellation
}

#[tauri::command]
pub async fn analysis_run(
    config: serde_json::Value,
    app: tauri::AppHandle,
    state: State<'_, AnalysisProcess>,
) -> Result<(), String> {
    // 1. Serialize config to temp YAML
    let yaml_str =
        serde_yaml::to_string(&config).map_err(|e| String::from(AppError::config_parse_error(&format!("YAML serialization: {}", e))))?;

    let tmp_dir = std::env::temp_dir();
    let config_path = tmp_dir.join(format!(
        "prognosis_marker_{}.yaml",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis()
    ));
    std::fs::write(&config_path, &yaml_str)
        .map_err(|e| String::from(AppError::analysis_failed(&format!("Cannot write temp config: {}", e))))?;

    // 2. Determine analysis script
    let analysis_type = config
        .get("type")
        .and_then(|v| v.as_str())
        .unwrap_or("binary");

    let script = match analysis_type {
        "survival" => "Main_Survival.R",
        _ => "Main_Binary.R",
    };

    // 3. Spawn R process with piped stdout/stderr
    let mut child = std::process::Command::new("Rscript")
        .arg(script)
        .arg(format!("--config={}", config_path.to_string_lossy()))
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .map_err(|e| String::from(AppError::runtime_not_found(&format!("Failed to start Rscript: {}", e))))?;

    // Store PID for cancellation
    let pid = child.id();
    {
        let mut guard = state.child.lock().map_err(|e| e.to_string())?;
        *guard = Some(pid);
    }

    // 4. Take ownership of stdout and stderr before moving child
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();

    // 5. Stream output in background threads
    let app_handle = app.clone();

    std::thread::spawn(move || {
        // Spawn stderr reader thread (R prints progress to stderr)
        let app_for_stderr = app_handle.clone();
        let stderr_thread = stderr.map(|stderr| {
            std::thread::spawn(move || {
                let reader = BufReader::new(stderr);
                for line in reader.lines() {
                    if let Ok(line) = line {
                        // Parse progress lines (e.g., "[1/100] Iteration ...")
                        if let Some(progress) = parse_progress_line(&line) {
                            let _ = app_for_stderr.emit(
                                "analysis://progress",
                                serde_json::json!(progress),
                            );
                        }
                        let _ = app_for_stderr.emit("analysis://log", &line);
                    }
                }
            })
        });

        // Stream stdout in this thread
        if let Some(stdout) = stdout {
            let reader = BufReader::new(stdout);
            for line in reader.lines() {
                if let Ok(line) = line {
                    let _ = app_handle.emit("analysis://log", &line);
                }
            }
        }

        // Wait for stderr thread to finish
        if let Some(handle) = stderr_thread {
            let _ = handle.join();
        }

        // Wait for the process to complete
        match child.wait() {
            Ok(status) => {
                let _ = app_handle.emit(
                    "analysis://complete",
                    serde_json::json!({
                        "success": status.success(),
                        "code": status.code()
                    }),
                );
            }
            Err(e) => {
                let _ = app_handle.emit(
                    "analysis://error",
                    serde_json::json!({
                        "message": e.to_string()
                    }),
                );
            }
        }

        // Clear PID
        let process_state = app_handle.state::<AnalysisProcess>();
        let _ = process_state.child.lock().map(|mut guard| *guard = None);
    });

    Ok(())
}

#[tauri::command]
pub async fn analysis_cancel(state: State<'_, AnalysisProcess>) -> Result<(), String> {
    let mut guard = state.child.lock().map_err(|e| e.to_string())?;
    if let Some(pid) = *guard {
        // Kill process by PID
        #[cfg(unix)]
        {
            unsafe {
                libc::kill(pid as i32, libc::SIGTERM);
            }
        }
        #[cfg(windows)]
        {
            let _ = std::process::Command::new("taskkill")
                .args(["/PID", &pid.to_string(), "/F"])
                .output();
        }
        *guard = None;
        Ok(())
    } else {
        Ok(())
    }
}

/// Parse R progress output lines like "[1/100] Iteration 1" or "Step 5/20: ..."
fn parse_progress_line(line: &str) -> Option<serde_json::Value> {
    // Pattern: [current/total] message
    if line.starts_with('[') {
        if let Some(bracket_end) = line.find(']') {
            let inner = &line[1..bracket_end];
            if let Some((current_str, total_str)) = inner.split_once('/') {
                if let (Ok(current), Ok(total)) =
                    (current_str.trim().parse::<u32>(), total_str.trim().parse::<u32>())
                {
                    let message = line[bracket_end + 1..].trim().to_string();
                    return Some(serde_json::json!({
                        "type": "iteration",
                        "current": current,
                        "total": total,
                        "message": message,
                    }));
                }
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_progress_standard() {
        let result = parse_progress_line("[1/100] Iteration 1 completed");
        assert!(result.is_some());
        let val = result.unwrap();
        assert_eq!(val["current"], 1);
        assert_eq!(val["total"], 100);
        assert_eq!(val["type"], "iteration");
        assert_eq!(val["message"], "Iteration 1 completed");
    }

    #[test]
    fn test_parse_progress_with_spaces() {
        let result = parse_progress_line("[ 5 / 20 ] Step 5 running");
        assert!(result.is_some());
        let val = result.unwrap();
        assert_eq!(val["current"], 5);
        assert_eq!(val["total"], 20);
    }

    #[test]
    fn test_parse_progress_no_bracket() {
        let result = parse_progress_line("Some regular log line");
        assert!(result.is_none());
    }

    #[test]
    fn test_parse_progress_invalid_numbers() {
        let result = parse_progress_line("[abc/def] bad data");
        assert!(result.is_none());
    }

    #[test]
    fn test_parse_progress_empty_message() {
        let result = parse_progress_line("[3/10]");
        assert!(result.is_some());
        let val = result.unwrap();
        assert_eq!(val["current"], 3);
        assert_eq!(val["total"], 10);
        assert_eq!(val["message"], "");
    }
}
