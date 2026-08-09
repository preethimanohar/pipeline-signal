# 🎯 UPDATED STREAMLIT APP - Live Databricks Integration
# Copy this entire cell into your app.py file

import streamlit as st
import os
import pandas as pd
from databricks import sql
import networkx as nx

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PipelineSignal | Data Platform Risk Engine",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ PipelineSignal")
st.caption("Databricks Unity Catalog Risk & Governance Intelligence Agent")

# --- DATABRICKS CONNECTION ---
@st.cache_resource
def get_databricks_connection():
    """Establish connection to Databricks SQL warehouse."""
    return sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )

connection = get_databricks_connection()

# --- DATA LOADING FUNCTIONS ---
@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_risk_data():
    """Load high-risk models from gold table."""
    query = """
    SELECT 
      model_name,
      resource_type,
      database,
      schema,
      risk_level,
      linked_issue_number,
      linked_issue_title,
      linked_issue_state,
      linked_issue_url,
      has_active_incident,
      SIZE(upstream_depends_on) AS upstream_dependency_count,
      upstream_depends_on
    FROM pipeline_signal.gold.gold_pipeline_impact_risk
    WHERE risk_level = 'HIGH'
    ORDER BY SIZE(upstream_depends_on) DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
    
    return pd.DataFrame(data, columns=columns)

@st.cache_data(ttl=600)
def load_all_models():
    """Load all dbt models for investigation."""
    query = """
    SELECT 
      model_name,
      resource_type,
      database,
      schema,
      risk_level,
      upstream_depends_on,
      has_active_incident
    FROM pipeline_signal.gold.gold_pipeline_impact_risk
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
    
    return pd.DataFrame(data, columns=columns)

@st.cache_data(ttl=300)
def get_ai_remediation_summaries():
    """Execute AI-powered remediation query."""
    query = """
    SELECT 
      model_name,
      resource_type,
      database,
      schema,
      risk_level,
      linked_issue_number,
      linked_issue_title,
      linked_issue_state,
      linked_issue_url,
      has_active_incident,
      ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT(
          'You are a senior data platform engineer reviewing a high-risk incident. ',
          'Generate a concise executive remediation summary (3-4 sentences) that includes: ',
          '1) Root cause analysis, 2) Immediate actions needed, 3) Timeline estimate.\\n\\n',
          'DBT MODEL: ', model_name, '\\n',
          'RESOURCE TYPE: ', resource_type, '\\n',
          'LOCATION: ', database, '.', schema, '\\n',
          'LINKED INCIDENT: #', CAST(linked_issue_number AS STRING), ' - ', linked_issue_title, '\\n',
          'INCIDENT STATUS: ', linked_issue_state, '\\n',
          'UPSTREAM DEPENDENCIES: ', 
          CASE 
            WHEN SIZE(upstream_depends_on) > 0 
            THEN CONCAT_WS(', ', upstream_depends_on)
            ELSE 'None'
          END
        ),
        modelParameters => named_struct(
          'max_tokens', 300,
          'temperature', 0.3,
          'top_p', 0.9
        )
      ) AS ai_remediation_summary,
      SIZE(upstream_depends_on) AS upstream_dependency_count,
      CASE 
        WHEN SIZE(upstream_depends_on) > 0 
        THEN CONCAT_WS(', ', upstream_depends_on)
        ELSE 'None'
      END AS upstream_dependencies_list
    FROM pipeline_signal.gold.gold_pipeline_impact_risk
    WHERE 
      risk_level = 'HIGH'
      AND has_active_incident = TRUE
      AND linked_issue_number IS NOT NULL
    ORDER BY 
      SIZE(upstream_depends_on) DESC,
      linked_issue_number DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
    
    return pd.DataFrame(data, columns=columns)

# --- LOAD DATA ---
try:
    risk_df = load_risk_data()
    all_models_df = load_all_models()
    
    # Build NetworkX Graph
    G = nx.DiGraph()
    for _, row in all_models_df.iterrows():
        node_id = f"{row['database']}.{row['schema']}.{row['model_name']}"
        G.add_node(
            node_id,
            name=row['model_name'],
            schema=row['schema'],
            risk_level=row['risk_level']
        )
        
        # Add edges from upstream dependencies
        if row['upstream_depends_on']:
            for upstream in row['upstream_depends_on']:
                G.add_edge(upstream, node_id)
    
    # --- TOP METRICS ROW ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Catalog Assets", len(all_models_df))
    col2.metric("High-Risk Models", len(risk_df))
    
    # Calculate max blast radius
    max_blast = risk_df['upstream_dependency_count'].max() if not risk_df.empty else 0
    max_blast_model = risk_df.loc[risk_df['upstream_dependency_count'].idxmax()]['model_name'] if not risk_df.empty else "N/A"
    
    col3.metric("Max Upstream Dependencies", int(max_blast))
    col4.metric("Highest Risk Asset", max_blast_model)
    
    active_incidents = risk_df[risk_df['has_active_incident'] == True].shape[0]
    if active_incidents > 0:
        st.error(f"⚠️ {active_incidents} HIGH RISK models with active GitHub incidents require immediate attention!")
    else:
        st.success("✅ No critical incidents detected")
    
    st.markdown("---")
    
    # --- TAB NAVIGATION ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Investigation", 
        "🔮 Prediction (Impact)", 
        "📊 Prioritization", 
        "🤖 AI Remediation Agent"
    ])
    
    # --- TAB 1: INVESTIGATION ---
    with tab1:
        st.subheader("Asset Lineage & Dependency Discovery")
        
        model_options = all_models_df['model_name'].unique().tolist()
        selected_model = st.selectbox(
            "Select a dbt Model to Investigate:",
            options=model_options
        )
        
        model_info = all_models_df[all_models_df['model_name'] == selected_model].iloc[0]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Model:** `{model_info['model_name']}`")
            st.markdown(f"**Schema:** `{model_info['database']}.{model_info['schema']}`")
            st.markdown(f"**Risk Level:** `{model_info['risk_level']}`")
            st.markdown(f"**Active Incident:** `{model_info['has_active_incident']}`")
        
        with c2:
            node_id = f"{model_info['database']}.{model_info['schema']}.{model_info['model_name']}"
            
            # Get upstream dependencies
            upstream = list(G.predecessors(node_id)) if node_id in G else []
            st.markdown(f"**Upstream Dependencies ({len(upstream)}):**")
            if upstream:
                for u in upstream:
                    st.write(f"- `{u}`")
            else:
                st.write("*No upstream dependencies (source table)*")
            
            # Get downstream dependencies
            downstream = list(G.successors(node_id)) if node_id in G else []
            st.markdown(f"**Downstream Dependent Assets ({len(downstream)}):**")
            if downstream:
                for d in downstream:
                    st.write(f"- `{d}`")
            else:
                st.write("*No downstream dependencies (leaf node)*")
    
    # --- TAB 2: PREDICTION ---
    with tab2:
        st.subheader("Simulate Schema Alteration / Breaking Change")
        
        target_model = st.selectbox(
            "Select Model to Deprecate or Alter:",
            options=model_options,
            key="predict_select"
        )
        
        change_type = st.radio(
            "Select Proposed Change Type:",
            ["Drop Column / Table Deprecation", "Type Shift (e.g. STRING to BIGINT)", "Rename Column"]
        )
        
        if st.button("Run Impact Simulation"):
            model_row = all_models_df[all_models_df['model_name'] == target_model].iloc[0]
            node_id = f"{model_row['database']}.{model_row['schema']}.{target_model}"
            
            downstream = list(nx.descendants(G, node_id)) if node_id in G else []
            
            if downstream:
                st.error(f"⚠️ **CRITICAL RISK:** Altering `{target_model}` will impact **{len(downstream)}** downstream assets!")
                st.markdown("### Impacted Assets:")
                for d in downstream:
                    st.write(f"❌ `{d}`")
                
                st.markdown("### Recommended Actions:")
                st.info(f"""
                1. **Apply Data Contract:** Enforce strict schema validation on `{target_model}`
                2. **Notify Stakeholders:** Alert owners of {len(downstream)} downstream assets
                3. **Staged Rollout:** Test changes in dev/staging before production
                4. **Backward Compatibility:** Consider adding new column instead of modifying existing
                """)
            else:
                st.success(f"✅ **LOW RISK:** `{target_model}` has 0 downstream dependencies. Safe to modify.")
    
    # --- TAB 3: PRIORITIZATION ---
    with tab3:
        st.subheader("Load-Bearing Asset Risk Ranking")
        st.markdown("Models ranked by risk level and upstream dependencies:")
        
        # Create prioritization dataframe
        priority_data = risk_df[[
            'model_name', 'database', 'schema', 'risk_level', 
            'upstream_dependency_count', 'has_active_incident', 
            'linked_issue_number', 'linked_issue_title'
        ]].copy()
        
        priority_data['location'] = priority_data['database'] + '.' + priority_data['schema']
        priority_data = priority_data[[
            'model_name', 'location', 'risk_level', 'upstream_dependency_count',
            'has_active_incident', 'linked_issue_number', 'linked_issue_title'
        ]]
        
        st.dataframe(
            priority_data.sort_values('upstream_dependency_count', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    
    # --- TAB 4: AI REMEDIATION ---
    with tab4:
        st.subheader("🤖 AI-Powered Remediation Workflow")
        st.markdown("*Powered by Databricks Foundation Models & Vector Search*")
        
        with st.spinner("🤖 Generating AI remediation summaries..."):
            ai_df = get_ai_remediation_summaries()
        
        if ai_df.empty:
            st.success("✅ No high-risk incidents detected!")
        else:
            st.error(f"⚠️ {len(ai_df)} high-risk models require immediate attention")
            
            # Display metrics
            rcol1, rcol2, rcol3 = st.columns(3)
            with rcol1:
                st.metric("High-Risk Models", len(ai_df))
            with rcol2:
                avg_dependencies = ai_df['upstream_dependency_count'].mean()
                st.metric("Avg Upstream Dependencies", f"{avg_dependencies:.1f}")
            with rcol3:
                open_issues = ai_df[ai_df['linked_issue_state'] == 'open'].shape[0]
                st.metric("Open GitHub Issues", open_issues)
            
            st.divider()
            
            # Display each high-risk model with AI remediation
            for idx, row in ai_df.iterrows():
                with st.expander(
                    f"🔴 {row['model_name']} (Issue #{row['linked_issue_number']})",
                    expanded=(idx == 0)
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("### 🤖 AI Remediation Summary")
                        st.info(row['ai_remediation_summary'])
                        
                        st.markdown("### 📋 Incident Details")
                        st.write(f"**Title:** {row['linked_issue_title']}")
                        st.write(f"**Status:** {row['linked_issue_state'].upper()}")
                        st.write(f"**URL:** [{row['linked_issue_url']}]({row['linked_issue_url']})")
                        
                        st.markdown("### 💬 Draft Slack Alert")
                        st.code(f"""
[PipelineSignal Alert] HIGH RISK: {row['model_name']}

Linked Issue: #{row['linked_issue_number']} - {row['linked_issue_title']}
Status: {row['linked_issue_state'].upper()}
Location: {row['database']}.{row['schema']}
Upstream Dependencies: {row['upstream_dependency_count']}

AI Assessment:
{row['ai_remediation_summary']}

Action Required: Review and remediate immediately.
Issue: {row['linked_issue_url']}
                        """, language="text")
                    
                    with col2:
                        st.markdown("### 📊 Model Details")
                        st.write(f"**Resource Type:** {row['resource_type']}")
                        st.write(f"**Location:** `{row['database']}.{row['schema']}`")
                        st.write(f"**Risk Level:** {row['risk_level']}")
                        st.write(f"**Upstream Dependencies:** {row['upstream_dependency_count']}")
                        
                        if row['upstream_dependencies_list'] != 'None':
                            st.markdown("**Upstream Models:**")
                            st.code(row['upstream_dependencies_list'], language="text")

except Exception as e:
    st.error(f"Error loading data from Databricks: {e}")
    st.info("""
    **Setup Instructions:**
    
    1. Set environment variables:
       - `DATABRICKS_SERVER_HOSTNAME`
       - `DATABRICKS_HTTP_PATH`
       - `DATABRICKS_TOKEN`
    
    2. Install dependencies:
       ```bash
       pip install streamlit databricks-sql-connector pandas networkx
       ```
    
    3. Run the app:
       ```bash
       streamlit run app.py
       ```
    """)

st.divider()
st.caption("Powered by Databricks AI & Unity Catalog | Data refreshes every 5-10 minutes")
