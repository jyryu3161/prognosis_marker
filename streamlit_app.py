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

# Custom CSS - Bioinformatics Clean White Design
st.markdown(
    """
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@500;600;700&display=swap');
    
    /* Global Settings */
    * {
        font-family: 'Inter', 'Helvetica', sans-serif;
    }
    
    /* Main App Background - Pure White */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Main Container Padding */
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Headers - Poppins Font */
    .main-header {
        font-family: 'Poppins', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #1976d2;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: #1e1e1e;
        font-weight: 600;
    }
    
    h2 {
        font-size: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.5rem;
    }
    
    /* Primary Button Style */
    .stButton>button {
        width: 100%;
        background-color: #1976d2;
        color: white;
        font-weight: 500;
        font-size: 0.95rem;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
        transition: all 0.2s ease;
        text-transform: none;
    }
    
    .stButton>button:hover {
        background-color: #1565c0;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
        transform: translateY(-1px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Form Container - Card Style */
    .stForm {
        background: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    }
    
    /* File Uploader - Force White Background */
    .stFileUploader {
        background: #ffffff !important;
        padding: 2rem;
        border-radius: 12px;
        border: 2px dashed #1976d2;
        transition: border-color 0.2s ease;
    }
    
    .stFileUploader:hover {
        border-color: #43a047;
    }
    
    /* Force all file uploader children to white background and black text */
    .stFileUploader > div,
    .stFileUploader section,
    .stFileUploader [data-testid="stFileUploadDropzone"],
    .stFileUploader [data-testid="stFileUploader"],
    section[data-testid="stFileUploadDropzone"] {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
    }
    
    /* File uploader text */
    .stFileUploader label,
    .stFileUploader p,
    .stFileUploader span,
    section[data-testid="stFileUploadDropzone"] p,
    section[data-testid="stFileUploadDropzone"] span {
        color: #1e1e1e !important;
        font-weight: 500;
    }
    
    .stFileUploader small {
        color: #5f6368 !important;
    }
    
    /* Drag and drop zone */
    div[data-testid="stFileUploadDropzone"] > div {
        background-color: #ffffff !important;
    }
    
    div[data-testid="stFileUploadDropzone"] button {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
        border: 1px solid #1976d2 !important;
        border-radius: 8px;
        font-weight: 600;
    }

    /* Ensure visibility of dropzone helper texts */
    .stFileUploader [data-testid="stFileUploadDropzone"] * {
        color: #1e1e1e !important;
        opacity: 1 !important;
        filter: none !important;
    }
    
    /* Info/Alert Boxes */
    .stAlert {
        background: #ffffff;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 1rem;
    }
    
    div[data-baseweb="notification"] {
        border-radius: 8px;
    }
    
    /* Success Message */
    .stSuccess {
        background-color: #e8f5e9;
        border-left: 4px solid #43a047;
        color: #1e1e1e;
    }
    
    /* Info Message */
    .stInfo {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        color: #1e1e1e;
    }
    
    /* Expander - Clean Card Style */
    .streamlit-expanderHeader {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        font-weight: 500;
        color: #1e1e1e;
        transition: background-color 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #f5f5f5;
    }
    
    details[open] > .streamlit-expanderHeader {
        border-bottom: 1px solid #e0e0e0;
        border-radius: 8px 8px 0 0;
    }
    
    /* Metrics - Academic Style */
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 600;
        color: #1976d2;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 500;
        color: #5f6368;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sidebar - Professional White */
    section[data-testid="stSidebar"] {
        background-color: #fafafa;
        border-right: 1px solid #e0e0e0;
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>div,
    .stNumberInput>div>div>input {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.6rem;
        font-size: 0.95rem;
        color: #1e1e1e;
        background-color: #ffffff;
        transition: border-color 0.2s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>div:focus,
    .stNumberInput>div>div>input:focus {
        border-color: #1976d2;
        box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.1);
    }
    
    /* Slider */
    .stSlider>div>div>div>div {
        background-color: #1976d2;
    }
    
    /* Radio Buttons */
    .stRadio > label {
        font-weight: 500;
        color: #1e1e1e;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background-color: #e0e0e0;
        margin: 2rem 0;
    }
    
    /* Dataframe */
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: #1976d2;
    }
    
    /* Download Button */
    .stDownloadButton>button {
        background-color: #43a047;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton>button:hover {
        background-color: #388e3c;
        box-shadow: 0 2px 8px rgba(67, 160, 71, 0.3);
    }
    
    /* Tooltips */
    [data-testid="stTooltipIcon"] {
        color: #1976d2;
    }
    
    /* Code Blocks */
    code {
        background-color: #f5f5f5;
        color: #1976d2;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 0.9em;
    }
    
    /* Cards Effect for Containers */
    .element-container {
        transition: transform 0.2s ease;
    }
    
    /* Clean Professional Look */
    p, li, span {
        color: #1e1e1e;
        line-height: 1.6;
    }
    
    /* Subtle Shadows for Depth */
    .stForm, .stFileUploader, [data-testid="stExpander"] {
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
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
            st.dataframe(df.head(10), use_container_width=True)

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
