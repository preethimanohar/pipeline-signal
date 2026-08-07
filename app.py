import streamlit as st
import json
import networkx as nx

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PipelineSignal | Data Platform Risk Engine",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ PipelineSignal")
st.caption("Databricks Unity Catalog Risk & Governance Intelligence Agent")

# --- LOAD SNAPSHOT DATA ---
@st.cache_data
def load_metadata():
    try:
        with open("metadata_snapshot.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("`metadata_snapshot.json` not found in repository root.")
        return None

data = load_metadata()

if data:
    # Build NetworkX Graph from Snapshot
    G = nx.DiGraph()
    for node in data["nodes"]:
        G.add_node(
            node["id"],
            name=node["name"],
            schema=node["schema"],
            blast_radius=node["blast_radius_score"]
        )
    for edge in data["edges"]:
        G.add_edge(edge["source"], edge["target"])

    # --- TOP METRICS ROW ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Catalog Assets", len(data["nodes"]))
    col2.metric("Total Lineage Edges", len(data["edges"]))
    
    # Calculate highest blast radius
    max_blast_node = max(data["nodes"], key=lambda x: x["blast_radius_score"], default=None)
    max_score = max_blast_node["blast_radius_score"] if max_blast_node else 0
    top_asset = max_blast_node["name"] if max_blast_node else "N/A"
    
    col3.metric("Max Blast Radius", f"{max_score} Downstream")
    col4.metric("Highest Risk Asset", top_asset)

    st.markdown("---")

    # --- TAB NAVIGATION ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Investigation", 
        "🔮 Prediction (Impact)", 
        "📊 Prioritization", 
        "🤖 Recommendation Agent"
    ])

    # --- TAB 1: INVESTIGATION ---
    with tab1:
        st.subheader("Asset Lineage & Dependency Discovery")
        selected_asset = st.selectbox(
            "Select a Databricks Table to Investigate:",
            options=[n["id"] for n in data["nodes"]]
        )
        
        node_info = next((n for n in data["nodes"] if n["id"] == selected_asset), None)
        if node_info:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Schema:** `{node_info['schema']}`")
                st.markdown(f"**Blast Radius Score:** `{node_info['blast_radius_score']}`")
            with c2:
                downstream = node_info.get("downstream_nodes", [])
                st.markdown(f"**Downstream Dependent Assets ({len(downstream)}):**")
                if downstream:
                    for d in downstream:
                        st.write(f"- `{d}`")
                else:
                    st.write("*No downstream dependencies detected (leaf node).*")

    # --- TAB 2: PREDICTION ---
    with tab2:
        st.subheader("Simulate Schema Alteration / Breaking Change")
        target_node = st.selectbox(
            "Select Upstream Table to Deprecate or Alter:",
            options=[n["id"] for n in data["nodes"]],
            key="predict_select"
        )
        
        change_type = st.radio(
            "Select Proposed Change Type:",
            ["Drop Column / Table Deprecation", "Type Shift (e.g. STRING to BIGINT)", "Rename Column"]
        )
        
        if st.button("Run Impact Simulation"):
            downstream = list(nx.descendants(G, target_node)) if target_node in G else []
            if downstream:
                st.error(f"⚠️ **CRITICAL RISK:** Altering `{target_node}` will impact **{len(downstream)}** downstream assets!")
                for d in downstream:
                    st.write(f"❌ Impacted: `{d}`")
            else:
                st.success(f"✅ **LOW RISK:** `{target_node}` has 0 downstream dependencies. Safe to modify.")

    # --- TAB 3: PRIORITIZATION ---
    with tab3:
        st.subheader("Load-Bearing Asset Risk Ranking")
        st.markdown("Tables ranked by downstream impact score across the lakehouse:")
        
        sorted_nodes = sorted(data["nodes"], key=lambda x: x["blast_radius_score"], reverse=True)
        table_data = [
            {
                "Table ID": n["id"],
                "Schema": n["schema"],
                "Blast Radius Score": n["blast_radius_score"],
                "Downstream Dependents": len(n.get("downstream_nodes", []))
            }
            for n in sorted_nodes
        ]
        st.dataframe(table_data, use_container_width=True)

    # --- TAB 4: RECOMMENDATIONS ---
    with tab4:
        st.subheader("Agentic Remediation Workflow")
        high_risk_nodes = [n for n in data["nodes"] if n["blast_radius_score"] > 0]
        
        if high_risk_nodes:
            rec_target = st.selectbox(
                "Select High-Impact Asset for Remediation Plan:",
                options=[n["id"] for n in high_risk_nodes],
                key="rec_select"
            )
            
            st.markdown("### 📋 Generated Action Plan")
            st.info(f"**Target:** `{rec_target}`")
            st.markdown(f"""
            1. **Apply Data Contract:** Enforce strict schema validation rules on `{rec_target}` in Unity Catalog.
            2. **Downstream Refactoring:** Update SQL views consuming this table prior to merging changes.
            3. **Stakeholder Notification:** Issue automated Slack/Jira alerts to downstream owners.
            """)
            
            st.markdown("### 💬 Draft Slack Alert")
            st.code(f"""
            [PipelineSignal Alert] Planned schema update on `{rec_target}`.
            Impacted Downstream Pipelines: {len(nx.descendants(G, rec_target))}
            Action Required: Review downstream views and confirm compatibility before release window.
            """, language="markdown")
        else:
            st.write("No high-risk assets requiring immediate remediation.")
