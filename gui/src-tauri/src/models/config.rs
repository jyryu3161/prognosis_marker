use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum AnalysisConfig {
    Binary(BinaryConfig),
    Survival(SurvivalConfig),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BinaryConfig {
    pub data_file: String,
    pub sample_id: String,
    pub outcome: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub time_variable: Option<String>,
    pub split_prop: f64,
    pub num_seed: u32,
    pub output_dir: String,
    pub freq: u32,
    #[serde(default)]
    pub exclude: Vec<String>,
    #[serde(default)]
    pub include: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_candidates_per_step: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub prescreen_seeds: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub top_k: Option<u32>,
    #[serde(default = "default_p_adjust")]
    pub p_adjust_method: String,
    #[serde(default = "default_p_threshold")]
    pub p_threshold: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub evidence: Option<EvidenceConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SurvivalConfig {
    pub data_file: String,
    pub sample_id: String,
    pub event: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub time_variable: Option<String>,
    pub horizon: f64,
    pub split_prop: f64,
    pub num_seed: u32,
    pub output_dir: String,
    pub freq: u32,
    #[serde(default)]
    pub exclude: Vec<String>,
    #[serde(default)]
    pub include: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_candidates_per_step: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub prescreen_seeds: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub top_k: Option<u32>,
    #[serde(default = "default_p_adjust")]
    pub p_adjust_method: String,
    #[serde(default = "default_p_threshold")]
    pub p_threshold: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub evidence: Option<EvidenceConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EvidenceConfig {
    pub gene_file: String,
    pub score_threshold: f64,
    #[serde(default)]
    pub source: String,
    #[serde(default)]
    pub disease_name: String,
    #[serde(default)]
    pub efo_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DataFileInfo {
    pub path: String,
    pub row_count: usize,
    pub columns: Vec<String>,
    pub preview: std::collections::HashMap<String, Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TcgaPreset {
    pub id: String,
    pub label: String,
    pub config_path: String,
    pub has_evidence: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeInfo {
    pub r_path: Option<String>,
    pub pixi_path: Option<String>,
    pub r_version: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProgressEvent {
    pub event_type: String,
    pub current: u32,
    pub total: u32,
    pub message: String,
}

fn default_p_adjust() -> String {
    "fdr".to_string()
}

fn default_p_threshold() -> f64 {
    0.05
}
