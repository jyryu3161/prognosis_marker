"""
Prognosis Marker - Simple Analysis Interface
데이터 업로드하고 분석 실행하는 간단한 웹 인터페이스
"""

import streamlit as st
import pandas as pd
import subprocess
import tempfile
import yaml
from pathlib import Path
import time
import os

# Page configuration
st.set_page_config(page_title="Prognosis Marker", page_icon="🔬", layout="wide")

# Custom CSS - refreshed accessible theme
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@500;600;700&display=swap');

    :root {
        --pm-primary: #1b4e9b;
        --pm-primary-dark: #143b75;
        --pm-accent: #1aa27a;
        --pm-surface: #ffffff;
        --pm-surface-muted: #f3f6fb;
        --pm-text: #1f2a37;
        --pm-text-muted: #5b6b7f;
        --pm-border: #d7deea;
    }

    * {
        font-family: 'Inter', 'Helvetica', sans-serif;
        color: var(--pm-text);
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: var(--pm-surface-muted);
        color: var(--pm-text);
    }

    [data-testid="stHeader"] {
        background: linear-gradient(90deg, rgba(255,255,255,0.95), rgba(243,246,251,0.9));
        border-bottom: 1px solid var(--pm-border);
    }

    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    .main-header {
        font-family: 'Poppins', sans-serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: var(--pm-primary);
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }

    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: var(--pm-text);
        font-weight: 600;
    }

    h2 {
        font-size: 1.45rem;
        margin-top: 1.75rem;
        margin-bottom: 1.1rem;
        border-bottom: 2px solid var(--pm-border);
        padding-bottom: 0.6rem;
    }

    p, li, span {
        line-height: 1.65;
        color: var(--pm-text);
    }

    .stButton>button {
        width: 100%;
        background: #ffffff;
        color: var(--pm-primary) !important;
        font-weight: 600;
        font-size: 0.98rem;
        padding: 0.8rem 1.5rem;
        border-radius: 10px;
        border: 1px solid var(--pm-primary);
        box-shadow: 0 2px 10px rgba(27, 78, 155, 0.10);
        transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, color 0.2s ease;
    }
 
    .stButton>button:hover {
        transform: translateY(-1px);
        background: var(--pm-primary);
        color: #ffffff !important;
        box-shadow: 0 8px 20px rgba(27, 78, 155, 0.22);
    }

    .stButton>button:focus {
        outline: 3px solid rgba(27, 78, 155, 0.35);
        outline-offset: 2px;
    }

    .stButton>button:disabled {
        background: var(--pm-border);
        color: var(--pm-text-muted) !important;
        box-shadow: none;
    }

    .stDownloadButton>button {
        background: #ffffff;
        color: var(--pm-accent) !important;
        border-radius: 10px;
        border: 1px solid var(--pm-accent);
        font-weight: 600;
        padding: 0.75rem 1.25rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, color 0.2s ease;
    }

    .stDownloadButton>button:hover {
        transform: translateY(-1px);
        background: var(--pm-accent);
        color: #ffffff !important;
        box-shadow: 0 10px 24px rgba(26, 162, 122, 0.28);
    }

    .stForm, [data-testid="stExpander"], .stFileUploader {
        background: var(--pm-surface);
        border-radius: 14px;
        border: 1px solid var(--pm-border);
        box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
    }

    .stForm {
        padding: 2rem;
    }

    [data-testid="stExpander"] > summary {
        background: linear-gradient(180deg, #ffffff 0%, #f7f9fc 100%);
        border-radius: 14px;
        font-weight: 600;
        color: var(--pm-text);
        padding: 0.9rem 1.1rem;
    }

    .streamlit-expanderHeader:hover {
        background-color: #eef2f8;
    }

    [data-testid="stExpander"] > div[role="group"] {
        border-top: 1px solid var(--pm-border);
        padding: 1.25rem 1.1rem 1.4rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.97) 0%, rgba(243,246,251,0.9) 100%);
        border-right: 1px solid var(--pm-border);
    }

    [data-testid="stSidebar"] > div {
        padding-top: 2.2rem;
    }

    .stTextInput>div>div>input,
    .stSelectbox>div>div>div,
    .stSelectbox [data-baseweb="select"] > div,
    .stNumberInput>div,
    .stNumberInput>div>div>input,
    .stNumberInput input,
    .stTextArea>div>div>textarea {
        border: 1px solid var(--pm-border);
        border-radius: 10px;
        padding: 0.7rem 0.85rem;
        font-size: 0.98rem;
        color: var(--pm-text);
        background-color: var(--pm-surface) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    /* Number input container and steppers */
    .stNumberInput > div {
        background: var(--pm-surface) !important;
        color: var(--pm-text) !important;
        overflow: hidden;
        border-radius: 10px !important;
    }
    .stNumberInput [data-baseweb="input"],
    .stNumberInput [data-testid="baseButton-secondary"],
    .stNumberInput [data-testid="baseButton-secondaryFormSubmit"],
    .stNumberInput input {
        background: var(--pm-surface) !important;
        color: var(--pm-text) !important;
        border: none !important;
        box-shadow: none !important;
    }
    .stNumberInput button,
    .stNumberInput [role="spinbutton"] button {
        background: var(--pm-surface) !important;
        color: var(--pm-text) !important;
        border-left: 1px solid var(--pm-border) !important;
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
    }

    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>div:focus,
    .stNumberInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: var(--pm-primary);
        box-shadow: 0 0 0 3px rgba(27, 78, 155, 0.18);
    }

    .stRadio > label {
        font-weight: 600;
        color: var(--pm-text);
    }

    .stSlider>div>div>div>div {
        background-color: var(--pm-primary);
    }

    .stFileUploader {
        padding: 2rem 1.75rem;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: var(--pm-surface);
        border: 2px dashed var(--pm-primary);
        border-radius: 14px;
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: var(--pm-primary-dark);
        background: #f0f4ff;
    }

    [data-testid="stFileUploaderDropzone"] * {
        color: var(--pm-text) !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: #ffffff;
        color: var(--pm-primary) !important;
        border-radius: 8px;
        border: 1px solid var(--pm-primary);
        font-weight: 600;
        padding: 0.45rem 1rem;
        box-shadow: none;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background: var(--pm-primary);
        color: #ffffff !important;
    }

    /* Selectbox dropdown menu and options */
    [data-baseweb="select"] div {
        background: var(--pm-surface) !important;
        color: var(--pm-text) !important;
        border-color: var(--pm-border) !important;
    }
    [data-baseweb="menu"],
    [data-baseweb="popover"],
    [data-baseweb="menu"] div,
    [data-baseweb="menu"] ul,
    [data-baseweb="popover"] div {
        background: var(--pm-surface) !important;
        color: var(--pm-text) !important;
        border: none !important;
        box-shadow: 0 20px 48px rgba(15, 23, 42, 0.12);
        padding: 0.5rem 0.25rem;
    }
    [data-baseweb="menu"] [role="option"] {
        background: transparent !important;
        color: var(--pm-text) !important;
        border: none !important;
        border-radius: 8px !important;
        margin: 0.15rem 0.5rem;
        padding: 0.55rem 0.65rem;
    }
    [data-baseweb="menu"] [role="option"] > div {
        border: none !important;
    }
    [data-baseweb="menu"] [role="option"]:hover,
    [data-baseweb="menu"] [aria-selected="true"],
    [data-baseweb="menu"] [aria-selected="true"] > div {
        background: #eef2f8 !important;
        color: var(--pm-primary) !important;
    }
    [data-baseweb="menu"] [role="option"]:active {
        background: rgba(26, 162, 122, 0.08) !important;
    }

    [data-testid="stForm"] button,
    [data-testid="baseButton-primary"],
    [data-testid="baseButton-primaryFormSubmit"] {
        width: 100%;
        background: #ffffff !important;
        color: var(--pm-primary) !important;
        font-weight: 600;
        font-size: 0.98rem;
        padding: 0.8rem 1.5rem;
        border-radius: 10px;
        border: 1px solid var(--pm-primary);
        box-shadow: 0 2px 10px rgba(27, 78, 155, 0.10);
        transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, color 0.2s ease;
    }
    [data-testid="stForm"] button:hover,
    [data-testid="baseButton-primary"]:hover,
    [data-testid="baseButton-primaryFormSubmit"]:hover {
        transform: translateY(-1px);
        background: var(--pm-primary) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 20px rgba(27, 78, 155, 0.22);
    }
    [data-testid="stForm"] button:focus,
    [data-testid="baseButton-primary"]:focus,
    [data-testid="baseButton-primaryFormSubmit"]:focus {
        outline: 3px solid rgba(27, 78, 155, 0.35);
        outline-offset: 2px;
    }

    .stAlert {
        border-radius: 12px;
        border: 1px solid var(--pm-border);
        padding: 1.1rem 1.3rem;
        background: linear-gradient(180deg, #ffffff 0%, #f7f9fc 100%);
    }

    .stSuccess {
        border-left: 4px solid var(--pm-accent);
    }

    .stInfo {
        border-left: 4px solid var(--pm-primary);
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--pm-primary);
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.92rem;
        font-weight: 500;
        color: var(--pm-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .stDataFrame {
        border: 1px solid var(--pm-border);
        border-radius: 12px;
        overflow: hidden;
        background: var(--pm-surface) !important;
    }
    .stDataFrame *,
    .stDataFrame table,
    .stDataFrame th,
    .stDataFrame td,
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] div,
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] td {
        background: var(--pm-surface) !important;
        color: var(--pm-text) !important;
        border-color: var(--pm-border) !important;
    }

    .stProgress > div > div > div > div {
        background: var(--pm-primary);
    }

    hr {
        border: none;
        height: 1px;
        background-color: var(--pm-border);
        margin: 2.2rem 0;
    }

    code {
        background-color: rgba(27, 78, 155, 0.1);
        color: var(--pm-primary);
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.92em;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "results_dir" not in st.session_state:
    st.session_state.results_dir = None

# Header
st.markdown('<h1 class="main-header">🔬 Prognosis Marker</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="font-size: 1.1rem; color: #5f6368; margin-bottom: 2rem;">Biostatistical Gene Signature Analysis Platform</p>',
    unsafe_allow_html=True,
)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Step 1: Upload data
    st.markdown("## 📁 1. Data Upload")

    # Example data load button
    col_upload, col_example = st.columns([3, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload your CSV file",
            type=["csv"],
            help="Upload the dataset for analysis",
        )

    with col_example:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("📊 Load Example Data", key="load_example"):
            # Load example data
            example_path = Path("Example_data.csv")
            if example_path.exists():
                st.session_state.example_loaded = True
                st.rerun()
            else:
                st.error("Example_data.csv file not found")

    # Handle example data
    if "example_loaded" in st.session_state and st.session_state.example_loaded:
        example_path = Path("Example_data.csv")
        if example_path.exists():
            uploaded_file = example_path
            st.info("✓ Example data loaded successfully")

    if uploaded_file:
        # Preview data
        df = pd.read_csv(uploaded_file)
        file_name = (
            uploaded_file.name if hasattr(uploaded_file, "name") else str(uploaded_file)
        )
        st.success(f"✓ File loaded: {file_name}")

        with st.expander("📊 Data Preview"):
            preview_df = df.head(10)
            try:
                styled = preview_df.style.set_properties(
                    **{
                        "background-color": "#ffffff",
                        "color": "#1f2a37",
                        "border-color": "#d7deea",
                    }
                )
                st.dataframe(styled, use_container_width=True, hide_index=True)
            except Exception:
                st.dataframe(preview_df, use_container_width=True, hide_index=True)

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Rows", df.shape[0])
            with col_b:
                st.metric("Columns", df.shape[1])
            with col_c:
                # Handle file size for both uploaded and example files
                if hasattr(uploaded_file, "size"):
                    file_size = uploaded_file.size / 1024
                else:
                    file_size = Path(uploaded_file).stat().st_size / 1024
                st.metric("Size", f"{file_size:.1f} KB")

        st.markdown("---")

        # Step 2: Analysis type
        st.markdown("## 🎯 2. Analysis Type")
        analysis_type = st.radio(
            "Select analysis type",
            ["Binary Classification", "Survival Analysis"],
            horizontal=True,
        )

        st.markdown("---")

        # Step 3: Configuration
        st.markdown("## ⚙️ 3. Configuration")

        columns = df.columns.tolist()

        with st.form("analysis_config"):
            col_left, col_right = st.columns(2)

            with col_left:
                sample_id = st.selectbox(
                    "Sample ID Column", columns, index=0 if "sample" in columns else 0
                )

                if analysis_type == "Binary Classification":
                    outcome = st.selectbox("Outcome Column", columns)
                    time_var = st.selectbox(
                        "Time Column (Optional)", ["None"] + columns
                    )
                else:
                    time_var = st.selectbox("Time Column", columns)
                    outcome = st.selectbox("Event Column", columns)
                    horizon = st.number_input(
                        "Horizon (years)", value=5, min_value=1, max_value=20
                    )

            with col_right:
                split_prop = st.slider("Train/Test Split Ratio", 0.5, 0.9, 0.7, 0.05)
                num_seed = st.number_input(
                    "Number of Iterations",
                    value=100,
                    min_value=10,
                    max_value=1000,
                    step=10,
                )
                output_dir = st.text_input(
                    "Output Directory",
                    value=f"results/{analysis_type.lower().split()[0]}",
                )

            submitted = st.form_submit_button("🚀 Start Analysis")

            if submitted:
                # Save uploaded file temporarily
                temp_dir = tempfile.mkdtemp()
                data_path = Path(temp_dir) / uploaded_file.name
                df.to_csv(data_path, index=False)

                # Create config
                config = {"workdir": ".", "data_file": str(data_path)}

                if analysis_type == "Binary Classification":
                    config["binary"] = {
                        "data_file": str(data_path),
                        "sample_id": sample_id,
                        "outcome": outcome,
                        "time_variable": None if time_var == "None" else time_var,
                        "split_prop": split_prop,
                        "num_seed": num_seed,
                        "output_dir": output_dir,
                    }
                else:
                    config["survival"] = {
                        "data_file": str(data_path),
                        "sample_id": sample_id,
                        "time_variable": time_var,
                        "event": outcome,
                        "horizon": horizon,
                        "split_prop": split_prop,
                        "num_seed": num_seed,
                        "output_dir": output_dir,
                    }

                # Save config
                config_path = Path(temp_dir) / "config.yaml"
                with open(config_path, "w") as f:
                    yaml.dump(config, f)

                # Run analysis
                st.markdown("---")
                st.markdown("## 🔄 Running Analysis...")

                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    # Determine which script to run
                    script_type = (
                        "binary"
                        if analysis_type == "Binary Classification"
                        else "survival"
                    )

                    status_text.text(
                        f"Running R script... (up to {num_seed} iterations)"
                    )
                    progress_bar.progress(30)

                    # Run pixi command
                    result = subprocess.run(
                        [
                            "pixi",
                            "run",
                            script_type,
                            "--",
                            "--config",
                            str(config_path),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=600,  # 10 minutes timeout
                    )

                    progress_bar.progress(90)

                    if result.returncode == 0:
                        progress_bar.progress(100)
                        status_text.text("✓ Analysis completed!")

                        st.session_state.analysis_complete = True
                        st.session_state.results_dir = output_dir

                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Error occurred during analysis")
                        st.code(result.stderr, language="text")

                except subprocess.TimeoutExpired:
                    st.error("❌ Analysis timeout (10 minute limit)")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with col2:
    st.markdown("## 💡 Help")

    st.info(
        """
    **🚀 Quick Start**
    
    1. Click **📊 Load Example Data** for a demo
    2. Or **upload your CSV file**
    3. Select analysis type
    4. Configure column names
    5. Start analysis!
    
    **📋 Data Format**
    
    **Binary Analysis:**
    - Sample ID (identifier)
    - Outcome (0/1: result)
    - Time (optional)
    - Additional feature columns
    
    **Survival Analysis:**
    - Sample ID (identifier)
    - Time (in years)
    - Event (0/1: event occurred)
    - Additional feature columns
    """
    )

    with st.expander("⚙️ Parameter Details"):
        st.markdown(
            """
        **Split Ratio**
        - Proportion for training set (0.7 = 70%)
        - Higher ratio = more training data
        
        **Number of Iterations**
        - Train/test split repetitions
        - More iterations = more stable, but longer runtime
        
        **Horizon (Survival only)**
        - Evaluation timepoint for survival analysis (years)
        - Example: 5-year survival rate
        """
        )

    with st.expander("📊 Example Data Info"):
        st.markdown(
            """
        **Example_data.csv**
        
        Sample dataset ready for immediate analysis.
        
        - Supports both Binary & Survival analysis
        - 145 samples
        - Multiple gene markers included
        """
        )

# Results section
if st.session_state.analysis_complete and st.session_state.results_dir:
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")

    results_dir = Path(st.session_state.results_dir)

    if results_dir.exists():
        # Display results
        col1, col2 = st.columns(2)

        with col1:
            # ROC Curve
            roc_png = results_dir / "ROCcurve.png"
            if roc_png.exists():
                st.image(str(roc_png), caption="ROC Curve", use_container_width=True)

        with col2:
            # Variable Importance
            var_imp_png = results_dir / "Variable_Importance.png"
            if var_imp_png.exists():
                st.image(
                    str(var_imp_png),
                    caption="Variable Importance",
                    use_container_width=True,
                )

        # AUC results
        auc_csv = results_dir / "auc_iterations.csv"
        if auc_csv.exists():
            st.markdown("### 📈 AUC Results")
            auc_df = pd.read_csv(auc_csv)
            st.dataframe(auc_df, use_container_width=True, hide_index=True)

        # Download section
        st.markdown("### 📥 Download Results")

        download_col1, download_col2, download_col3 = st.columns(3)

        with download_col1:
            if roc_png.exists():
                with open(roc_png, "rb") as f:
                    st.download_button(
                        "📊 ROC Curve (PNG)",
                        f,
                        file_name="ROCcurve.png",
                        mime="image/png",
                    )

        with download_col2:
            if var_imp_png.exists():
                with open(var_imp_png, "rb") as f:
                    st.download_button(
                        "📊 Importance (PNG)",
                        f,
                        file_name="Variable_Importance.png",
                        mime="image/png",
                    )

        with download_col3:
            if auc_csv.exists():
                with open(auc_csv, "rb") as f:
                    st.download_button(
                        "📄 AUC Results (CSV)",
                        f,
                        file_name="auc_iterations.csv",
                        mime="text/csv",
                    )

        # New analysis button
        if st.button("🔄 Start New Analysis"):
            st.session_state.analysis_complete = False
            st.session_state.results_dir = None
            if "example_loaded" in st.session_state:
                del st.session_state.example_loaded
            st.rerun()
    else:
        st.warning("Results directory not found.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0 1rem 0;'>
        <p style='font-size: 0.9rem; color: #5f6368; margin-bottom: 0.3rem;'>
            <strong>Prognosis Marker</strong> — Academic Bioinformatics Research Tool
        </p>
        <p style='font-size: 0.85rem; color: #9e9e9e;'>
            Powered by R, Python & Streamlit | © 2025
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
