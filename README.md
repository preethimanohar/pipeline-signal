# PipelineSignal: Data Platform Risk & Governance Intelligence

PipelineSignal is an agentic data platform intelligence engine that transforms raw data metadata into actionable risk metrics, dependency maps, and automated remediation plans. Built natively on Databricks Unity Catalog and dbt lineage, PipelineSignal empowers Data Platform PMs, Data Architects, and Analytics Engineers to evaluate schema changes, prevent pipeline outages, and manage lakehouse migrations with zero guesswork.

## 🎯 Capability Matrix

PipelineSignal organizes operational intelligence across four primary dimensions:

### 1. Investigation (Root Cause & Lineage Discovery)

- **Lineage Traceability**: Maps end-to-end dependency chains from raw ingestion sources down to analytical marts and executive dashboards.
- **Ownership & Downstream Mapping**: Identifies all downstream consumer teams and business owners dependent on specific upstream data assets.
- **Orphaned Asset Detection**: Highlights unused tables (zero upstream sources and zero downstream consumers) for cleanup and storage cost optimization.
- **Governance Audit**: Pinpoints critical downstream assets directly referencing unvalidated staging models rather than enterprise-grade production marts.

### 2. Prediction (Impact Analysis & Risk Modeling)

- **Blast Radius Analysis**: Simulates column drops, name changes, or table deprecations to identify every downstream model, report, and ML pipeline that will break.
- **Type-Shift Failure Impact**: Predicts failure cascades resulting from upstream type alterations (e.g., STRING to BIGINT or breaking timestamp formats).
- **Single-Point-of-Failure (SPOF) Identification**: Detects bottleneck datasets in the directed acyclic graph (DAG) prior to production deployments.

### 3. Prioritization (Risk Ranking & Execution Sequencing)

- **Load-Bearing Asset Scoring**: Ranks datasets by downstream blast radius score to apply automated schema contracts to the highest-impact tables.
- **Topological Migration Sequencing**: Computes strict dependency order for schema and catalog migrations to prevent broken pipeline states.
- **Operational Risk Matrix**: Ranks active platform risks based on potential impact to executive decision-making and operational reporting.

### 4. Recommendation (Agentic Remediation & PM Workflows)

- **SQL Refactoring Workflows**: Generates automated migration checklists and SQL transformation fixes for downstream breaking changes.
- **Automated Stakeholder Notifications**: Drafts contextual incident/change tickets for Jira and Slack, tailored to affected downstream owners.
- **Contract & Governance Policies**: Recommends exact Data Contract definitions and Unity Catalog governance rules for high-risk assets.

## 🏗️ System Architecture

PipelineSignal uses a hybrid architecture designed for enterprise-grade execution in Databricks and public accessibility via Streamlit:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       DATABRICKS WORKSPACE (PRIVATE)                    │
│                                                                         │
│   [system.information_schema] ───> [PySpark Extraction Engine]           │
│                                             │                           │
│                                             ▼                           │
│                                 [NetworkX Graph Engine]                 │
│                                             │                           │
│                                             ▼                           │
│                                  [metadata_snapshot.json]               │
└─────────────────────────────────────────────┬───────────────────────────┘
                                              │ (Sync / Export)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       PUBLIC DEMO (STREAMLIT CLOUD)                     │
│                                                                         │
│   [metadata_snapshot.json] ───> [Interactive Blast Radius Visualizer]   │
│                            └───> [LLM Risk & Remediation Agent]         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Components

- **PySpark Extraction Engine**: Queries `system.information_schema` in Databricks to extract metadata
- **NetworkX Graph Engine**: Constructs dependency graphs and performs lineage analysis
- **Metadata Snapshot**: JSON-based export for portability and public demo environments
- **Streamlit Interface**: Interactive visualization and LLM-powered recommendations
- **Agentic Layer**: Automated risk analysis and remediation workflow generation

## 🚀 Getting Started

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- Python 3.9+
- dbt (for lineage integration)
- Streamlit (for UI)

### Installation

```bash
git clone https://github.com/preethimanohar/pipeline-signal.git
cd pipeline-signal
pip install -r requirements.txt
```

### Configuration

1. Set up Databricks credentials in your environment
2. Configure Unity Catalog connection details
3. Export metadata snapshot:
   ```bash
   python extract_metadata.py
   ```
4. Launch Streamlit UI:
   ```bash
   streamlit run app.py
   ```

## 📊 Use Cases

- **Schema Change Impact Assessment**: Understand the full blast radius before deploying breaking changes
- **Pipeline Outage Prevention**: Identify single points of failure and critical dependencies
- **Lakehouse Migrations**: Plan and sequence migrations without downtime
- **Cost Optimization**: Discover and remediate orphaned assets
- **Governance Compliance**: Ensure downstream assets follow governance policies
- **Incident Response**: Automate root cause analysis and stakeholder notifications

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Support

For questions or issues, please open a GitHub issue or contact the maintainers.
