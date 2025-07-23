# aws-hackathon-gs

# Multi-Agent Product Manager Assistant

This project demonstrates a **multi-agent system** built on **AWS Bedrock**, **Lambda**, and **Confluence** to support **Product Managers (PMs)** in making faster, data-driven decisions based on safety alerts, consumer insights, and market trends.

---

##  Use Case

Product Managers often deal with scattered data across various tools and teams — from safety alerts to customer feedback and market trends. This solution brings it all together using autonomous agents, turning raw data into structured documentation — without switching tools or chasing teams.

---

##  Key Features

-  **Multi-agent collaboration** between specialized Bedrock agents
-  **Automated Confluence documentation** (via Lambda + Bedrock actions)
-  **Scoring engine** to classify feedback as `alert` or `insight`
-  **Real-time user interaction** via UI and Bedrock Runtime
-  **Trend analysis and knowledge retrieval** using markdown-based KBs

---

## System Architecture
<img width="2009" height="1060" alt="image" src="https://github.com/user-attachments/assets/320a88ef-9ec6-424f-a1fc-b67de8452f70" />


- **Frontend**: Static S3 Website (chat UI)
- **Backend**:
  - `bedrock-agent-ui-handler`: Routes user input to the PM agent
  - `get_alerts`: Collects alert summaries from the alert agent
  - `Scorer_Agent_Invoker`: Classifies feedback using Bedrock Converse
  - `JsonToJsonl_Converter`: Converts insights to JSONL for KB ingestion
  - `Create_Confluence_Doc`: Publishes pages to Confluence
- **Agents**:
  - `Product Manager Agent`: Coordinates all interactions
  - `Market Agent`: Sources alert and feedback data
  - `Trend Agent`: Summarizes markdown trend reports
  - `Documentation Agent`: Handles uploads to Confluence (via Lambda)

---
