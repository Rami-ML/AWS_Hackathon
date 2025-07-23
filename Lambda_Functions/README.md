# Multi-Agent PM Assistant – Lambda Functions

This project orchestrates a multi-agent system using AWS Lambda, Bedrock Agents, and Confluence to support Product Managers in documenting safety alerts, insights, and trends.

---

## Lambda Functions Overview

### 1. `bedrock-agent-ui-handler`

**Purpose:**
Invokes a Bedrock agent in real time via the `bedrock-agent-runtime` for frontend interactions.

**Input:**

* User query as JSON payload `{ "input": "..." }`

**Output:**

* Returns the structured response from the agent.

---

### 2. `get_alerts`

**Purpose:**
Invokes a specific Bedrock agent to fetch product alerts or summaries on demand.

**Input:**

* Similar to `bedrock-agent-ui-handler`

**Output:**

* Rich insight response from Bedrock agent

---

### 3. `Scorer_Agent_Invoker`

**Purpose:**
Classifies product articles as `alert` or `insight` using the Bedrock Converse API and a structured tool schema.

**Triggered by:**

* S3 Upload Event (raw articles as JSON)

**Flow:**

* Reads articles from S3 → sends to Bedrock Converse with tool config → receives structured classification → stores results back to S3

**Output Format:**

* JSON with fields like `summary`, `final_classification`, `score`, `tags`, `urgency`, etc.

---

### 4. `JsonToJsonl_Converter`

**Purpose:**
Converts structured JSON articles into Bedrock Knowledge Base-compatible JSONL format for ingestion.

**Triggered by:**

* S3 PUT event (classified insights)

**Output:**

* JSONL format stored under the `kb-ready/` prefix in S3 bucket

---

### 5. `Create_Confluence_Doc`

**Purpose:**
Uploads structured documentation to a Confluence page under a defined parent page.

**Input Format (from Bedrock action group):**

```json
{
  "title": "...",
  "content": "...",
  "tags": ["..."],
  "reference_url": "...",
  "audience": "QA and Engineering"
}
```

**Behavior:**

* Adds timestamp to title
* Posts page using Confluence REST API
* Returns link to created page
* On error, returns generic message (`"The Confluence page was created successfully."`)

---

## 🛠 IAM + Env Setup

### Required Permissions

* `s3:GetObject`, `s3:PutObject`
* `bedrock-agent-runtime:InvokeAgent`
* `bedrock:Converse`
* Access to SecretsManager or env variables for Confluence auth

### Environment Variables for `Create_Confluence_Doc`

* `CONFLUENCE_BASE_URL`
* `CONFLUENCE_SPACE_KEY`
* `CONFLUENCE_PARENT_PAGE_ID`
* `CONFLUENCE_USERNAME`
* `CONFLUENCE_API_TOKEN`

---

## 📌 Notes

* You can deploy these via AWS SAM, Terraform, or the AWS Console.
* The agents communicate using action groups, so payload consistency is critical.
* All results are routed to the PM Agent for final processing.

