"""
Prognosis Marker Codebase Analyzer
Modern Streamlit Dashboard for Code Analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from code_analyzer import CodeAnalyzer
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter
import os

# Page configuration
st.set_page_config(
    page_title="Prognosis Marker Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 500;
    }
    .file-tree {
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.9rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
    }
    .code-viewer {
        border-radius: 8px;
        overflow: hidden;
    }
    .highlight {
        border-radius: 8px;
        padding: 1rem;
        background: #f8f9fa;
    }
    .sidebar-info {
        padding: 1rem;
        background: #f0f2f6;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize analyzer
@st.cache_resource
def get_analyzer():
    return CodeAnalyzer(root_path=".")

analyzer = get_analyzer()

# Sidebar
with st.sidebar:
    st.markdown("### 🔬 Prognosis Marker")
    st.markdown("**Codebase Analysis Dashboard**")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📁 File Explorer", "🔍 Code Search", "🔧 Analysis Tools", "📜 Git History"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Quick stats in sidebar
    stats = analyzer.get_file_stats()
    st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
    st.markdown("**Quick Stats**")
    st.metric("Total Files", stats['total_files'])
    st.metric("Total Lines", f"{stats['total_lines']:,}")
    st.markdown('</div>', unsafe_allow_html=True)

    # About
    with st.expander("ℹ️ About"):
        st.markdown("""
        **Prognosis Marker** is a biostatistical research project
        for deriving prognostic gene signatures through reproducible
        machine learning workflows.

        **Features:**
        - Binary Classification
        - Survival Analysis
        - ROC Curve Generation
        - Feature Selection
        """)

# Main content
if page == "📊 Dashboard":
    st.markdown('<h1 class="main-header">Codebase Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Comprehensive overview of your project</p>', unsafe_allow_html=True)

    # Get statistics
    stats = analyzer.get_file_stats()

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📄 Total Files",
            value=stats['total_files'],
            delta=None
        )

    with col2:
        st.metric(
            label="📝 Total Lines",
            value=f"{stats['total_lines']:,}",
            delta=None
        )

    with col3:
        languages = len([k for k, v in stats['by_language'].items() if v > 0])
        st.metric(
            label="💬 Languages",
            value=languages,
            delta=None
        )

    with col4:
        r_files = stats['by_language'].get('R', 0)
        st.metric(
            label="📊 R Files",
            value=r_files,
            delta=None
        )

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Files by Language")
        if stats['by_language']:
            df_lang = pd.DataFrame([
                {'Language': k, 'Count': v}
                for k, v in stats['by_language'].items()
            ]).sort_values('Count', ascending=False)

            fig = px.pie(
                df_lang,
                values='Count',
                names='Language',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                showlegend=True,
                height=400,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📈 Lines of Code by Language")
        if stats['lines_by_language']:
            df_lines = pd.DataFrame([
                {'Language': k, 'Lines': v}
                for k, v in stats['lines_by_language'].items()
            ]).sort_values('Lines', ascending=False)

            fig = px.bar(
                df_lines,
                x='Language',
                y='Lines',
                color='Lines',
                color_continuous_scale='Purples'
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="",
                yaxis_title="Lines of Code"
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # File list
    st.subheader("📂 File Overview")

    if stats['file_list']:
        df_files = pd.DataFrame(stats['file_list'])
        df_files['size_kb'] = (df_files['size'] / 1024).round(2)

        # Create interactive table
        display_df = df_files[['path', 'language', 'lines', 'size_kb']].copy()
        display_df.columns = ['File Path', 'Language', 'Lines', 'Size (KB)']

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )

        # Download button
        csv = df_files.to_csv(index=False)
        st.download_button(
            label="📥 Download File List (CSV)",
            data=csv,
            file_name="file_list.csv",
            mime="text/csv"
        )

    # Project structure
    st.markdown("---")
    st.subheader("🏗️ Project Structure")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Main Components:**")
        st.markdown("""
        - `Main_Binary.R` - Binary classification
        - `Main_Survival.R` - Survival analysis
        - `Binary_TrainAUC_StepwiseSelection.R` - Binary stepwise
        - `Survival_TrainAUC_StepwiseSelection.R` - Survival stepwise
        - `Example_data.csv` - Sample dataset
        - `config/` - Configuration files
        """)

    with col2:
        st.markdown("**Key Features:**")
        st.markdown("""
        - 🎯 AUC-driven forward/backward stepwise feature selection
        - 📊 ROC curve generation and visualization
        - 🔄 Repeated train/test splits with stratified resampling
        - 📈 Publication-grade figure exports (PNG, TIFF, SVG)
        - 📝 Comprehensive CSV logging
        - ⚙️ YAML-driven configuration
        """)

elif page == "📁 File Explorer":
    st.markdown('<h1 class="main-header">File Explorer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Browse and view project files</p>', unsafe_allow_html=True)

    # Get directory structure
    structure = analyzer.get_directory_structure()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📂 Directory Tree")

        def display_tree(node, level=0):
            """Recursively display directory tree"""
            indent = "  " * level
            icon = "📁" if node['type'] == 'directory' else "📄"

            # Create expandable sections for directories
            if node['type'] == 'directory':
                with st.expander(f"{indent}{icon} {node['name']}", expanded=(level < 2)):
                    for child in node.get('children', []):
                        display_tree(child, level + 1)
            else:
                if st.button(f"{indent}{icon} {node['name']}", key=node['path']):
                    st.session_state['selected_file'] = node['path']

        display_tree(structure)

    with col2:
        st.subheader("📄 File Viewer")

        # File selection
        stats = analyzer.get_file_stats()
        file_paths = [f['path'] for f in stats['file_list']]

        selected_file = st.selectbox(
            "Select a file to view",
            [''] + file_paths,
            index=0 if 'selected_file' not in st.session_state else file_paths.index(st.session_state.get('selected_file', '')) + 1
        )

        if selected_file:
            file_path = Path(selected_file)

            # File info
            st.markdown(f"**File:** `{selected_file}`")

            try:
                file_size = file_path.stat().st_size
                st.markdown(f"**Size:** {file_size / 1024:.2f} KB")

                # Read and display file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Syntax highlighting
                try:
                    lexer = guess_lexer_for_filename(file_path, content)
                    formatter = HtmlFormatter(style='monokai', full=True, linenos=True)
                    highlighted = highlight(content, lexer, formatter)

                    st.markdown('<div class="code-viewer">', unsafe_allow_html=True)
                    st.markdown(highlighted, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                except Exception:
                    # Fallback to plain text
                    st.code(content, language=None)

                # Download button
                st.download_button(
                    label="📥 Download File",
                    data=content,
                    file_name=file_path.name,
                    mime="text/plain"
                )

                # Analyze R files
                if file_path.suffix.lower() in ['.r']:
                    st.markdown("---")
                    st.subheader("🔍 R File Analysis")

                    analysis = analyzer.analyze_r_file(str(file_path))

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Functions", analysis.get('function_count', 0))
                    with col2:
                        st.metric("Libraries", analysis.get('library_count', 0))
                    with col3:
                        st.metric("Code Lines", analysis.get('code_lines', 0))
                    with col4:
                        st.metric("Comments", analysis.get('comment_lines', 0))

                    if analysis.get('functions'):
                        st.markdown("**Functions defined:**")
                        for func in analysis['functions']:
                            st.markdown(f"- `{func}()`")

                    if analysis.get('libraries'):
                        st.markdown("**Libraries imported:**")
                        for lib in analysis['libraries']:
                            st.markdown(f"- `{lib}`")

            except Exception as e:
                st.error(f"Error reading file: {e}")

elif page == "🔍 Code Search":
    st.markdown('<h1 class="main-header">Code Search</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Search across all project files</p>', unsafe_allow_html=True)

    # Search input
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "🔍 Search pattern (regex supported)",
            placeholder="Enter search term or regex pattern..."
        )

    with col2:
        file_types = st.multiselect(
            "File types",
            ['.R', '.r', '.py', '.yaml', '.yml', '.md', '.csv'],
            default=['.R', '.r']
        )

    if search_query:
        with st.spinner("Searching..."):
            results = analyzer.search_in_files(search_query, file_types)

        st.markdown(f"**Found {len(results)} results**")

        if results:
            # Group by file
            df_results = pd.DataFrame(results)

            # Display results by file
            for file_path in df_results['file'].unique():
                file_results = df_results[df_results['file'] == file_path]

                with st.expander(f"📄 {file_path} ({len(file_results)} matches)"):
                    for _, row in file_results.iterrows():
                        st.markdown(f"**Line {row['line_number']}:**")
                        st.code(row['line'], language=row['language'].lower())

            # Download results
            csv = df_results.to_csv(index=False)
            st.download_button(
                label="📥 Download Search Results (CSV)",
                data=csv,
                file_name="search_results.csv",
                mime="text/csv"
            )
        else:
            st.info("No results found")

elif page == "🔧 Analysis Tools":
    st.markdown('<h1 class="main-header">Analysis Tools</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Deep dive into code structure and dependencies</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 R Analysis", "⚙️ Configuration", "📦 Dependencies"])

    with tab1:
        st.subheader("R File Analysis")

        r_files = [f['path'] for f in analyzer.get_file_stats()['file_list'] if f['extension'].lower() in ['.r']]

        if r_files:
            selected_r_file = st.selectbox("Select R file", r_files)

            if selected_r_file:
                analysis = analyzer.analyze_r_file(selected_r_file)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 📋 Functions")
                    if analysis.get('functions'):
                        for func in analysis['functions']:
                            st.markdown(f"- `{func}()`")
                    else:
                        st.info("No functions found")

                with col2:
                    st.markdown("### 📚 Libraries")
                    if analysis.get('libraries'):
                        for lib in analysis['libraries']:
                            st.markdown(f"- `{lib}`")
                    else:
                        st.info("No libraries imported")

                # Stats
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Lines", analysis.get('total_lines', 0))
                with col2:
                    st.metric("Code Lines", analysis.get('code_lines', 0))
                with col3:
                    st.metric("Comment Lines", analysis.get('comment_lines', 0))
                with col4:
                    comment_ratio = (analysis.get('comment_lines', 0) / max(analysis.get('total_lines', 1), 1)) * 100
                    st.metric("Comment %", f"{comment_ratio:.1f}%")

        else:
            st.info("No R files found in the project")

    with tab2:
        st.subheader("Configuration Files")

        # Check for config files
        config_files = [f['path'] for f in analyzer.get_file_stats()['file_list']
                       if f['extension'].lower() in ['.yaml', '.yml', '.toml']]

        if config_files:
            selected_config = st.selectbox("Select configuration file", config_files)

            if selected_config:
                if selected_config.endswith('.yaml') or selected_config.endswith('.yml'):
                    analysis = analyzer.analyze_yaml_file(selected_config)

                    if 'error' not in analysis:
                        st.markdown(f"**Total keys:** {analysis.get('keys', 0)}")

                        if analysis.get('top_level_keys'):
                            st.markdown("**Top-level keys:**")
                            for key in analysis['top_level_keys']:
                                st.markdown(f"- `{key}`")

                        st.markdown("---")
                        st.markdown("**Configuration Structure:**")
                        st.json(analysis.get('structure', {}))
                    else:
                        st.error(f"Error analyzing file: {analysis['error']}")

                with open(selected_config, 'r') as f:
                    st.code(f.read(), language='yaml')
        else:
            st.info("No configuration files found")

    with tab3:
        st.subheader("Project Dependencies")

        # Check for requirements.txt, pixi.toml, etc.
        dep_files = {
            'requirements.txt': 'Python',
            'pixi.toml': 'Pixi',
            'package.json': 'Node.js'
        }

        found_deps = []
        for dep_file, dep_type in dep_files.items():
            if Path(dep_file).exists():
                found_deps.append((dep_file, dep_type))

        if found_deps:
            for dep_file, dep_type in found_deps:
                st.markdown(f"### {dep_type} Dependencies ({dep_file})")

                with open(dep_file, 'r') as f:
                    content = f.read()
                    st.code(content, language='toml' if dep_file.endswith('.toml') else 'text')
        else:
            st.info("No dependency files found")

        # R dependencies from all files
        st.markdown("---")
        st.subheader("R Libraries Used")

        all_libraries = set()
        r_files = [f['path'] for f in analyzer.get_file_stats()['file_list'] if f['extension'].lower() in ['.r']]

        for r_file in r_files:
            analysis = analyzer.analyze_r_file(r_file)
            all_libraries.update(analysis.get('libraries', []))

        if all_libraries:
            st.markdown(f"**Total unique libraries:** {len(all_libraries)}")

            cols = st.columns(3)
            for idx, lib in enumerate(sorted(all_libraries)):
                with cols[idx % 3]:
                    st.markdown(f"- `{lib}`")
        else:
            st.info("No R libraries found")

elif page == "📜 Git History":
    st.markdown('<h1 class="main-header">Git History</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Repository information and commit history</p>', unsafe_allow_html=True)

    git_info = analyzer.get_git_info()

    if 'error' not in git_info:
        # Current branch info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Current Branch", git_info['current_branch'])

        with col2:
            st.metric("Total Branches", len(git_info['branches']))

        with col3:
            status = "Clean ✅" if not git_info['is_dirty'] else "Modified ⚠️"
            st.metric("Working Tree", status)

        st.markdown("---")

        # Branches
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🌿 Branches")
            for branch in git_info['branches']:
                icon = "➡️" if branch == git_info['current_branch'] else "  "
                st.markdown(f"{icon} `{branch}`")

        with col2:
            st.subheader("📊 Repository Stats")
            st.markdown(f"**Total commits shown:** {len(git_info['recent_commits'])}")

        # Commit history
        st.markdown("---")
        st.subheader("📜 Recent Commits")

        if git_info['recent_commits']:
            for commit in git_info['recent_commits']:
                with st.expander(f"🔹 {commit['hash']} - {commit['message'][:60]}..."):
                    st.markdown(f"**Author:** {commit['author']}")
                    st.markdown(f"**Date:** {commit['date']}")
                    st.markdown(f"**Message:**\n```\n{commit['message']}\n```")

            # Create timeline visualization
            df_commits = pd.DataFrame(git_info['recent_commits'])
            df_commits['date'] = pd.to_datetime(df_commits['date'])

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df_commits['date'],
                y=[1] * len(df_commits),
                mode='markers+text',
                marker=dict(size=15, color='#667eea'),
                text=df_commits['hash'],
                textposition='top center',
                hovertemplate='<b>%{text}</b><br>%{x}<extra></extra>',
                showlegend=False
            ))

            fig.update_layout(
                title="Commit Timeline",
                xaxis_title="Date",
                yaxis_visible=False,
                height=200,
                margin=dict(t=40, b=20, l=20, r=20)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No commits found")
    else:
        st.warning(f"Git information not available: {git_info['error']}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Prognosis Marker Codebase Analyzer | Built with Streamlit</p>
        <p style='font-size: 0.9rem;'>🔬 Biostatistical Research Tool for Prognostic Gene Signatures</p>
    </div>
    """,
    unsafe_allow_html=True
)
