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

# Page configuration
st.set_page_config(page_title="Prognosis Marker", page_icon="🔬", layout="wide")

# Custom CSS - simple neutral theme
st.markdown(
    """
<style>
    :root {
        --pm-bg: #f5f7fb;
        --pm-surface: #ffffff;
        --pm-border: #d9e0eb;
        --pm-text: #1f2937;
        --pm-muted: #6b7280;
        --pm-primary: #2563eb;
        --pm-primary-dark: #1d4ed8;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: var(--pm-bg);
        color: var(--pm-text);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2.5rem;
        max-width: 1100px;
    }

    h1, h2, h3 {
        color: var(--pm-text);
        font-weight: 600;
    }

    .page-title {
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .page-subtitle {
        text-align: center;
        color: var(--pm-muted);
        margin-bottom: 2.5rem;
        font-size: 0.95rem;
    }

    .section-card {
        background: var(--pm-surface);
        border: 1px solid var(--pm-border);
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }

    .section-card h2 {
        font-size: 1.15rem;
        margin-bottom: 1rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--pm-border);
    }

    .section-card h3 {
        font-size: 1.05rem;
        margin-top: 1.2rem;
        margin-bottom: 0.75rem;
        color: var(--pm-text);
    }

    .stButton>button,
    [data-testid="baseButton-primary"],
    [data-testid="baseButton-primaryFormSubmit"] {
        background: var(--pm-primary) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600;
        padding: 0.65rem 1.4rem;
        transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.18);
    }

    .stButton>button:hover,
    [data-testid="baseButton-primary"]:hover,
    [data-testid="baseButton-primaryFormSubmit"]:hover {
        background: var(--pm-primary-dark) !important;
        transform: translateY(-1px);
    }

    .stButton>button:disabled {
        background: #d1d5db !important;
        color: #4b5563 !important;
        box-shadow: none !important;
    }

    .stDownloadButton>button {
        border: 1px solid var(--pm-primary) !important;
        color: var(--pm-primary) !important;
        background: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
    }

    .stDownloadButton>button:hover {
        background: var(--pm-primary) !important;
        color: #ffffff !important;
    }

    .stTextInput>div>div>input,
    .stSelectbox>div>div>div,
    .stSelectbox>div>div>div>input,
    .stNumberInput>div>div>input,
    .stNumberInput>div>div,
    .stTextArea>div>div>textarea {
        border-radius: 8px !important;
        border: 1px solid var(--pm-border) !important;
        background: #ffffff !important;
        color: var(--pm-text) !important;
        box-shadow: none !important;
    }

    .stNumberInput>div>div {
        border-radius: 8px !important;
    }

    .stNumberInput button {
        border-left: 1px solid var(--pm-border) !important;
        background: #ffffff !important;
        color: var(--pm-text) !important;
    }

    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>div:focus,
    .stNumberInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: var(--pm-primary) !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.12) !important;
    }

    [data-baseweb="select"] span {
        color: var(--pm-text) !important;
    }

    [data-baseweb="menu"] {
        background: #ffffff !important;
        border: 1px solid var(--pm-border) !important;
        border-radius: 8px !important;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12) !important;
    }

    [data-baseweb="menu"] [role="option"] {
        color: var(--pm-text) !important;
        background: transparent !important;
        border-radius: 6px;
    }

    [data-baseweb="menu"] [role="option"]:hover,
    [data-baseweb="menu"] [aria-selected="true"] {
        background: rgba(37, 99, 235, 0.15) !important;
        color: var(--pm-primary) !important;
    }

    [data-testid="stFileUploader"] {
        border-radius: 12px;
        border: 1px dashed var(--pm-border);
        padding: 1.2rem 1rem;
        background: #ffffff;
    }

    [data-testid="stFileUploaderDropzone"] {
        border: none !important;
        background: transparent !important;
    }

    .stAlert {
        border-radius: 10px;
        border: 1px solid var(--pm-border);
    }

    hr {
        border: none;
        height: 1px;
        background: var(--pm-border);
        margin: 1.5rem 0;
    }

    footer {visibility: hidden;}
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
st.markdown("<h1 class='page-title'>🔬 Prognosis Marker</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='page-subtitle'>Biostatistical Gene Signature Analysis Platform</p>",
    unsafe_allow_html=True,
)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("## 🎯 2. Analysis Type")
        analysis_type = st.radio(
            "Select analysis type",
            ["Binary Classification", "Survival Analysis"],
            horizontal=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
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
                st.markdown("<hr/>", unsafe_allow_html=True)
                st.markdown("### 🔄 Running Analysis...")

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

        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
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

    st.markdown('</div>', unsafe_allow_html=True)

# Results section
if st.session_state.analysis_complete and st.session_state.results_dir:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
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

    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0 1rem 0;'>
        <p style='font-size: 0.9rem; color: #4b5563; margin-bottom: 0.3rem;'>
            <strong>Prognosis Marker</strong> — Academic Bioinformatics Research Tool
        </p>
        <p style='font-size: 0.85rem; color: #94a3b8;'>
            Powered by R, Python & Streamlit | © 2025
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
