# Bharat National Bank (BNB) — Multi-Agent AI Architecture Document

## 1. Executive Summary

This document describes the architecture for a **multi-agent AI system** for **Bharat National Bank (BNB)**, a fictional Indian retail bank. The system uses specialized AI agents powered by Large Language Models (LLMs) to automate banking operations across three core use cases:

1. **Intelligent Customer Onboarding & KYC** — End-to-end account opening with Aadhaar/PAN verification
2. **AI-Powered Customer Service & Issue Resolution** — Omnichannel dispute handling, card management, and loan advisory
3. **Proactive Financial Health & Smart Notifications** — AI-driven spending insights and personalized recommendations

### Key Differentiators
- **Multi-channel:** Mobile App + WhatsApp + Voice calls
- **Multi-lingual:** Hindi + English with auto-detection and code-switching (Hinglish)
- **Multi-agent:** 15+ specialist agents orchestrated by a central orchestrator
- **Real-time visualization:** Live dashboard showing agent workflows, decisions, and data flows
- **Indian context:** ₹ currency, Aadhaar/PAN KYC, RBI compliance, Indian names and personas

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER CHANNELS                                │
│                                                                         │
│   ┌────────────┐     ┌────────────────┐     ┌────────────────┐         │
│   │  Mobile    │     │   WhatsApp     │     │    Voice       │         │
│   │  Banking   │     │   Business     │     │    (Phone)     │         │
│   │  App       │     │   API          │     │    Azure ACS   │         │
│   │  (React    │     │                │     │                │         │
│   │  Native)   │     │                │     │                │         │
│   └─────┬──────┘     └───────┬────────┘     └───────┬────────┘         │
│         │                    │                      │                   │
│    Entra ID B2C         WhatsApp Webhook      Azure AI Speech          │
│    (OAuth 2.0)          (Azure Functions)     (STT/TTS hi-IN)          │
└─────────┼────────────────────┼──────────────────────┼───────────────────┘
          │                    │                      │
          └────────────────────┼──────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Azure API Management)                   │
│              Auth validation • Rate limiting • Channel routing          │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│               ORCHESTRATOR AGENT (Semantic Kernel / Python)             │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │  Intent Classification │ Agent Selection │ Workflow Engine  │      │
│   │  Language Detection    │ Context Manager │ Error Handler    │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                                                         │
│   Registered in: Agent Registry (Cosmos DB)                             │
│   LLM: Azure OpenAI GPT-4o                                             │
│   Languages: Hindi (hi-IN) + English (en-IN) — auto-detect             │
│                                                                         │
└───┬────────┬────────┬────────┬────────┬────────┬────────┬───────────────┘
    │        │        │        │        │        │        │
    ▼        ▼        ▼        ▼        ▼        ▼        ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│Identity││KYC/AML ││Document││Account ││Customer││Transac-││Card    │
│Verify  ││Compli- ││Agent   ││Provis- ││360     ││tion    ││Mgmt    │
│Agent   ││ance    ││        ││ioning  ││Agent   ││Agent   ││Agent   │
└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│Loan    ││Spending││Savings ││Notifi- ││Compli- ││Voice   ││WhatsApp│
│Advisor ││Analyt- ││Advisor ││cation  ││ance    ││Agent   ││Agent   │
│Agent   ││ics     ││Agent   ││Agent   ││Guard   ││        ││        │
└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
    │        │        │        │        │        │        │
    ▼        ▼        ▼        ▼        ▼        ▼        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND SERVICES                                │
│                                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │ SharePoint │  │ Azure AD   │  │ Azure      │  │ Mock Banking    │  │
│  │ CRM (M365) │  │ Entra ID   │  │ OpenAI     │  │ APIs (₹)        │  │
│  │            │  │            │  │ GPT-4o     │  │                 │  │
│  └────────────┘  └────────────┘  └────────────┘  └─────────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │ Cosmos DB  │  │ Azure AI   │  │ Azure      │  │ Azure AI        │  │
│  │ (Data +    │  │ Document   │  │ Notif Hub  │  │ Speech          │  │
│  │  Registry) │  │ Intel      │  │            │  │ (STT/TTS)       │  │
│  └────────────┘  └────────────┘  └────────────┘  └─────────────────┘  │
│  ┌────────────┐  ┌────────────┐                                       │
│  │ Key Vault  │  │ SignalR    │  ← Real-time events to Dashboard      │
│  │ (Secrets)  │  │ Service    │                                       │
│  └────────────┘  └────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   VISUALIZATION DASHBOARD (React)                       │
│                                                                         │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────────────┐    │
│  │ Agent Workflow  │  │ Event        │  │ Agent State             │    │
│  │ Graph          │  │ Timeline     │  │ Inspector               │    │
│  │ (React Flow)   │  │ (Scrolling)  │  │ (Input/Output/Reason)   │    │
│  └────────────────┘  └──────────────┘  └─────────────────────────┘    │
│  ┌────────────────┐  ┌──────────────┐                                 │
│  │ System Health  │  │ Agent        │                                 │
│  │ Overview       │  │ Registry     │                                 │
│  └────────────────┘  └──────────────┘                                 │
│                                                                         │
│  Modes: Live | Replay (step-by-step)                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Two-Tenant Architecture

The solution spans two Microsoft tenants:

| Tenant | Domain | Purpose | Services |
|--------|--------|---------|----------|
| **Azure Tenant** | MngEnvMCAP935400.onmicrosoft.com | Compute, AI, Data | Azure Functions, OpenAI, Cosmos DB, ACS, Speech, Key Vault |
| **M365 E5 Tenant** | M365CPI71015715.onmicrosoft.com | CRM, Agent Platform | SharePoint Online, Copilot Studio, M365 Agents |

**Cross-tenant access** is via an App Registration (`BNB-Banking-Agents`, App ID: `c04e730e-89d1-4799-840f-fc53b964d337`) with Graph API permissions (`Sites.ReadWrite.All`, `Files.ReadWrite.All`, `User.Read.All`). Credentials are stored in Azure Key Vault (`bnb-poc-kv`).

---

## 3. Personas & Sample Data

All data uses Indian context with ₹ currency, Aadhaar/PAN for KYC, and Indian names.

### 3.1 Customer Personas

| Name | Role | Profile | Account |
|------|------|---------|---------|
| **Ananya Deshmukh** | New Customer | 21-year-old college student in Pune, first-time account opener | Savings Account (new) |
| **Priya Sharma** | Existing Customer | 34-year-old IT professional in Delhi, salaried | Savings A/C XXXX4523, Credit Card XXXX8891 |
| **Rajesh Iyer** | Business Customer | 45-year-old small business owner in Mumbai | Current A/C XXXX7712, Business Loan |

### 3.2 Bank Staff Personas

| Name | Role | Specialization |
|------|------|---------------|
| **Vikram Mehta** | Relationship Manager | High-value customers, disputes, escalations |
| **Sunita Nair** | Relationship Manager | Loan products, new account onboarding |

### 3.3 Sample Data Examples

**Transactions (Priya Sharma):**
| Date | Description | Amount | Category |
|------|-------------|--------|----------|
| 27-Feb-2026 | QuickMart Delhi | ₹15,000 | Shopping (DISPUTED) |
| 26-Feb-2026 | Swiggy Order | ₹450 | Food |
| 25-Feb-2026 | Amazon India | ₹2,300 | Shopping |
| 24-Feb-2026 | Salary Credit - TCS | ₹85,000 | Income |
| 23-Feb-2026 | Electricity Bill - BSES | ₹3,200 | Utilities |

**KYC Documents (Ananya Deshmukh):**
- Aadhaar Card: XXXX XXXX 4589
- PAN Card: ABCDE1234F
- Address Proof: Aadhaar-linked address, Pune, Maharashtra

---

## 4. Use Case 1: Intelligent Customer Onboarding & KYC

### 4.1 Overview
A new customer (Ananya Deshmukh) applies for her first bank account via WhatsApp or the mobile app. Multiple AI agents collaborate to complete Aadhaar/PAN verification and account opening without manual intervention.

### 4.2 Agent Roster

| Agent | Responsibility | Technology |
|-------|---------------|-----------|
| **Orchestrator** | Receives request, delegates, tracks progress | Semantic Kernel + Azure OpenAI |
| **WhatsApp Channel Agent** | Handles WhatsApp conversation flow | Azure Functions + WhatsApp API |
| **Identity Verification Agent** | Validates Aadhaar, PAN, selfie match | Azure AI Services |
| **KYC/AML Compliance Agent** | AML screening, sanctions check, risk scoring | Azure Functions + Mock API |
| **Document Agent** | Extracts data from uploaded documents | Azure AI Document Intelligence |
| **Account Provisioning Agent** | Creates account, provisions Azure AD identity | Azure AD + Mock Core Banking |

### 4.3 Sequence Diagram

```
Customer          WhatsApp       Orchestrator     ID Verify    KYC/AML     Document     Account
(Ananya)          Agent          Agent            Agent        Agent       Agent        Provisioning
   │                │                │               │            │           │              │
   │──"Hi, BNB"───►│                │               │            │           │              │
   │                │──onboarding──►│               │            │           │              │
   │                │◄──greeting────│               │            │           │              │
   │◄──"Namaste     │               │               │            │           │              │
   │   Ananya ji"───│               │               │            │           │              │
   │                │               │               │            │           │              │
   │──uploads       │               │               │            │           │              │
   │  Aadhaar+PAN──►│──documents──►│               │            │           │              │
   │                │               │──verify──────►│            │           │              │
   │                │               │──extract─────►│────────────│──────────►│              │
   │                │               │               │            │           │              │
   │                │               │◄──verified────│            │           │              │
   │                │               │◄──data────────│────────────│◄──────────│              │
   │                │               │               │            │           │              │
   │                │               │──AML check───►│───────────►│           │              │
   │                │               │◄──approved────│◄───────────│           │              │
   │                │               │               │            │           │              │
   │                │               │──provision───►│────────────│───────────│─────────────►│
   │                │               │◄──account─────│────────────│───────────│◄─────────────│
   │                │               │  created      │            │           │              │
   │                │◄──"Account    │               │            │           │              │
   │◄──created!"────│  created"─────│               │            │           │              │
   │                │               │               │            │           │              │
   │                │               │──store docs──►│────────────│───────────│──SharePoint  │
   │                │               │               │            │           │              │
```

### 4.4 Decision Points

| Decision | Agent | Logic |
|----------|-------|-------|
| Language preference | WhatsApp Agent | Auto-detect from first message; ask if ambiguous |
| Document quality | Document Agent | If OCR confidence < 80%, request re-upload |
| KYC risk score | KYC/AML Agent | Low (<30): auto-approve. Medium (30-70): additional verification. High (>70): escalate to RM |
| Account type | Orchestrator | Based on age, income, and customer preference |
| Escalation to RM | Orchestrator | If any step fails or risk is high → voice call to Sunita Nair |

### 4.5 Data Flow

```
WhatsApp Message → Azure Functions Webhook → Orchestrator
  ├── Document Agent → Azure AI Document Intelligence → Extract Aadhaar/PAN data
  ├── Identity Agent → Mock Aadhaar Verification API → Verify identity
  ├── KYC Agent → Mock AML/Sanctions API → Risk assessment
  └── Account Agent → Azure AD (create user) + Mock Core Banking (create account)
       └── SharePoint CRM → Create customer record + store documents
```

---

## 5. Use Case 2: AI-Powered Customer Service & Issue Resolution

### 5.1 Overview
Priya Sharma contacts BNB about a disputed ₹15,000 transaction. She can use WhatsApp, mobile app chat, or voice call. Multiple agents collaborate across channels to resolve the issue — including automatic card blocking and escalation to RM Vikram Mehta via voice call.

### 5.2 Agent Roster

| Agent | Responsibility | Technology |
|-------|---------------|-----------|
| **Orchestrator** | Intent classification, routing, context management | Semantic Kernel + Azure OpenAI |
| **WhatsApp Agent** | WhatsApp conversation handling | Azure Functions + WhatsApp API |
| **Voice Agent** | Inbound/outbound voice calls, STT/TTS | Azure Communication Services + AI Speech |
| **Customer 360 Agent** | Full customer profile from SharePoint CRM | Microsoft Graph API + Azure OpenAI |
| **Transaction Agent** | Transaction history, fraud analysis | Azure Functions + Mock Transaction API |
| **Card Management Agent** | Card block/unblock, replacement | Azure Functions + Mock Card API |
| **Loan Advisor Agent** | Pre-qualification, product recommendations | Azure OpenAI + Mock Eligibility API |

### 5.3 Multi-Channel Flow

```
                    ┌─────────────────────────────────┐
                    │         PRIYA SHARMA             │
                    │  "Maine ₹15,000 ka transaction   │
                    │   nahi kiya"                     │
                    └───────┬──────────┬───────────────┘
                            │          │
                   WhatsApp │          │ Voice Call
                            ▼          ▼
                    ┌──────────┐  ┌──────────┐
                    │ WhatsApp │  │  Voice   │
                    │  Agent   │  │  Agent   │
                    │          │  │ STT→Text │
                    └────┬─────┘  └────┬─────┘
                         │             │
                         └──────┬──────┘
                                ▼
                    ┌───────────────────┐
                    │   ORCHESTRATOR    │
                    │                   │
                    │ Intent: dispute   │
                    │ Confidence: 0.96  │
                    │ Language: Hindi   │
                    └───┬─────────┬─────┘
                        │         │
               parallel │         │ parallel
                        ▼         ▼
              ┌────────────┐ ┌────────────────┐
              │ Customer   │ │ Transaction    │
              │ 360 Agent  │ │ Agent          │
              │            │ │                │
              │ Profile:   │ │ ₹15,000 at     │
              │ Priya      │ │ QuickMart      │
              │ A/C: 4523  │ │ Fraud: 0.82    │
              └────────────┘ └───────┬────────┘
                                     │
                                     │ high fraud score
                                     ▼
                             ┌────────────────┐
                             │ Card Mgmt      │
                             │ Agent          │
                             │                │
                             │ AUTO-BLOCK     │
                             │ Card: 8891     │
                             └───────┬────────┘
                                     │
                                     ▼
                             ┌────────────────┐
                             │ Orchestrator   │
                             │ Create case    │
                             │ BNB-2026-0847  │
                             │ → SharePoint   │
                             └───────┬────────┘
                                     │
                            ┌────────┴────────┐
                            │                 │
                            ▼                 ▼
                    ┌──────────┐      ┌──────────┐
                    │ WhatsApp │      │ Voice    │
                    │ Response │      │ Agent    │
                    │ "Card    │      │ Connect  │
                    │ blocked" │      │ → RM     │
                    └──────────┘      │ Vikram   │
                                      └──────────┘
```

### 5.4 Voice Agent Capabilities

| Feature | Implementation |
|---------|---------------|
| Real-time STT | Azure AI Speech, hi-IN + en-IN, streaming |
| Neural TTS | Azure Neural Voice (hi-IN-MadhurNeural for male, hi-IN-SwaraNeural for female) |
| Sentiment Analysis | Real-time during call — detects frustration, urgency, confusion |
| Call Transcription | Full transcript auto-saved to SharePoint CRM case |
| RM Context Handoff | Orchestrator generates AI brief for RM before connecting |
| Call Recording | Azure Communication Services recording with consent prompt |

### 5.5 WhatsApp Agent Capabilities

| Feature | Implementation |
|---------|---------------|
| Natural Language | Hindi, English, Hinglish — powered by GPT-4o |
| Rich Media | Transaction screenshots, document uploads, location sharing |
| Quick Replies | Interactive buttons: "Block Card", "Check Balance", "Speak to RM" |
| Document Upload | Aadhaar/PAN images → Azure AI Document Intelligence |
| Handoff | Seamless transfer to Voice Agent or human RM with full context |

---

## 6. Use Case 3: Proactive Financial Health & Smart Notifications

### 6.1 Overview
BNB proactively analyzes Rajesh Iyer's spending patterns and sends personalized insights via WhatsApp, push notifications, and optional automated voice summary calls — all reviewed for RBI compliance before delivery.

### 6.2 Agent Roster

| Agent | Responsibility | Technology |
|-------|---------------|-----------|
| **Orchestrator** | Schedules batch analysis, coordinates delivery | Semantic Kernel + Azure OpenAI |
| **Spending Analytics Agent** | Transaction pattern analysis, anomaly detection | Azure Functions + Azure OpenAI |
| **Savings Advisor Agent** | Saving opportunities, goal recommendations | Azure OpenAI + Mock Account API |
| **Notification Agent** | Multi-channel message generation | Azure Functions + Notification Hub + WhatsApp |
| **Compliance Guard Agent** | RBI regulatory review of outbound messages | Azure OpenAI + Compliance Rules (SharePoint) |
| **Voice Summary Agent** | Automated weekly voice call summary | Azure Communication Services + AI Speech |

### 6.3 Batch Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    WEEKLY BATCH TRIGGER                      │
│               (Sunday 9:00 AM IST)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR: For each customer in batch...                 │
└──────┬───────────────────────────────────────────────────────┘
       │
       ├──►  SPENDING ANALYTICS AGENT
       │     ├── Categorize all transactions (last 7 days)
       │     ├── Compare with historical averages
       │     ├── Detect anomalies (e.g., "GST payments up 35%")
       │     └── Generate spending summary
       │
       ├──►  SAVINGS ADVISOR AGENT
       │     ├── Analyze cash flow patterns
       │     ├── Identify saving opportunities
       │     ├── Calculate potential FD returns at current rates
       │     └── Generate personalized recommendations
       │
       ├──►  NOTIFICATION AGENT
       │     ├── Draft conversational message (Hindi/English)
       │     ├── Generate infographic/chart data
       │     └── Prepare for multi-channel delivery
       │
       ├──►  COMPLIANCE GUARD AGENT
       │     ├── Review message against RBI guidelines
       │     ├── Check for prohibited claims/guarantees
       │     ├── Verify disclaimer requirements
       │     └── Approve or flag for revision
       │
       └──►  DELIVERY (if approved)
             ├── WhatsApp: Conversational message + chart image
             ├── Mobile App: Rich push notification
             └── Voice (opt-in): Automated call — "Rajesh ji, yeh aapka weekly summary hai..."
```

### 6.4 Sample Output (Rajesh Iyer)

**WhatsApp Message:**
```
🏦 BNB Weekly Financial Health — Rajesh ji

📊 This Week's Spending: ₹47,200
   ├── GST Payments: ₹18,000 (↑35% vs last week)
   ├── Utilities: ₹8,000 (↑₹2,000 vs average)
   ├── Inventory: ₹15,200
   └── Food & Transport: ₹6,000

💡 Savings Tip:
   "₹12,000/month se FD mein auto-sweep karein —
    7.5% p.a. pe ₹1,49,400 saal mein!"

📈 Your Business Health Score: 78/100 (Good ↑3)

Reply "Details" for breakdown | "Call" for voice summary
```

**Voice Call Script:**
```
"Namaste Rajesh ji, main BNB ki taraf se bol rahi hoon.
 Yeh aapka weekly financial summary hai.

 Is hafte aapne kul ₹47,200 kharch kiye.
 GST payments mein 35% ki badhot hui hai, jo ₹18,000 hai.
 Ek achhi baat — agar aap ₹12,000 monthly FD mein daalein,
 toh saal mein ₹1,49,400 mil sakte hain.

 Aapka business health score 78 hai, jo pichle hafte se 3 points behtar hai.

 Koi sawaal ho toh abhi poochh sakte hain, ya 'bye' bolein."
```

---

## 7. Agent Registry

### 7.1 Registry Structure (Cosmos DB)

Each agent is registered with the following metadata:

```json
{
  "agentId": "transaction-agent",
  "displayName": "Transaction Agent",
  "description": "Queries transaction history, detects fraud patterns, initiates disputes",
  "version": "1.0.0",
  "type": "specialist",
  "category": "banking-operations",
  "useCases": ["UC2-CustomerService"],
  "endpoint": "https://bnb-agents.azurewebsites.net/api/transaction-agent",
  "authMethod": "managed-identity",
  "capabilities": [
    "query_transactions",
    "fraud_analysis",
    "initiate_dispute",
    "categorize_spending"
  ],
  "inputSchema": {
    "customerId": "string",
    "action": "string",
    "parameters": "object"
  },
  "outputSchema": {
    "result": "object",
    "reasoning": "string",
    "confidence": "number"
  },
  "llmModel": "gpt-4o",
  "maxTokens": 4096,
  "temperature": 0.3,
  "healthCheck": "/api/health",
  "status": "active",
  "metrics": {
    "avgLatencyMs": 900,
    "callsLast24h": 95,
    "errorRate": 0.02
  }
}
```

### 7.2 Complete Agent Inventory

| # | Agent ID | Display Name | Type | Use Cases |
|---|----------|-------------|------|-----------|
| 1 | orchestrator | Orchestrator Agent | router | UC1, UC2, UC3 |
| 2 | whatsapp-agent | WhatsApp Agent | channel | UC1, UC2, UC3 |
| 3 | voice-agent | Voice Agent | channel | UC2, UC3 |
| 4 | identity-verify | Identity Verification Agent | specialist | UC1 |
| 5 | kyc-aml | KYC/AML Compliance Agent | specialist | UC1 |
| 6 | document-agent | Document Agent | specialist | UC1 |
| 7 | account-provision | Account Provisioning Agent | specialist | UC1 |
| 8 | customer-360 | Customer 360 Agent | specialist | UC2 |
| 9 | transaction-agent | Transaction Agent | specialist | UC2, UC3 |
| 10 | card-mgmt | Card Management Agent | specialist | UC2 |
| 11 | loan-advisor | Loan Advisor Agent | specialist | UC2 |
| 12 | spending-analytics | Spending Analytics Agent | specialist | UC3 |
| 13 | savings-advisor | Savings Advisor Agent | specialist | UC3 |
| 14 | notification-agent | Notification Agent | specialist | UC3 |
| 15 | compliance-guard | Compliance Guard Agent | specialist | UC3 |
| 16 | voice-summary | Voice Summary Agent | specialist | UC3 |

---

## 8. Security & Identity Architecture

### 8.1 Identity Model

```
┌─────────────────────────────────────────────────┐
│              AZURE AD ENTRA ID                   │
│                                                   │
│  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ B2C Tenant   │  │ App Registration         │  │
│  │              │  │ BNB-Banking-Agents       │  │
│  │ Customer     │  │                          │  │
│  │ Identities:  │  │ Client Credentials Flow  │  │
│  │ - Ananya     │  │ → SharePoint (M365)      │  │
│  │ - Priya      │  │ → Graph API              │  │
│  │ - Rajesh     │  │                          │  │
│  └──────────────┘  └──────────────────────────┘  │
│                                                   │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent Identities (Managed Identity)       │    │
│  │ Each Azure Function has MI for:           │    │
│  │ → Cosmos DB, Key Vault, OpenAI, ACS       │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### 8.2 Security Controls

| Control | Implementation |
|---------|---------------|
| Customer Auth | OAuth 2.0 + PKCE via Entra ID B2C |
| Agent Auth | Managed Identity (Azure Functions → Azure services) |
| Cross-tenant CRM | Client Credentials flow via App Registration |
| Secrets Management | Azure Key Vault (bnb-poc-kv) |
| Data Encryption | TLS 1.3 in transit, AES-256 at rest |
| Voice Call Consent | Automated consent prompt before recording |
| PII Handling | Aadhaar/PAN masked in logs, full data only in encrypted store |
| Audit Trail | Every agent action logged with user identity in Cosmos DB |
| RBI Compliance | Compliance Guard Agent reviews all outbound customer communications |

---

## 9. Data Architecture

### 9.1 Data Stores

| Store | Purpose | Technology | Tenant |
|-------|---------|-----------|--------|
| **CRM Data** | Customer records, cases, interactions | SharePoint Lists | M365 |
| **CRM Documents** | Aadhaar, PAN, statements, call recordings | SharePoint Doc Libraries | M365 |
| **Transaction Data** | Account transactions, balances | Cosmos DB (mock) | Azure |
| **Agent State** | Session context, conversation memory | Cosmos DB | Azure |
| **Agent Registry** | Agent metadata, endpoints, health | Cosmos DB | Azure |
| **Event Stream** | Agent action events for dashboard | Cosmos DB + SignalR | Azure |
| **Secrets** | API keys, client secrets, connection strings | Key Vault | Azure |

### 9.2 SharePoint CRM Structure

**SharePoint Site:** `BNB-CRM`

| List/Library | Purpose | Key Columns |
|-------------|---------|-------------|
| **Customers** | Customer master data | Name, Phone, Email, Aadhaar (masked), PAN (masked), Account Number, Segment, RM |
| **Cases** | Service cases and disputes | Case ID, Customer, Type, Status, Priority, Assigned RM, Resolution, Channel |
| **Interactions** | All customer touchpoints | Customer, Channel, Direction, Summary, Timestamp, Agent, Sentiment |
| **Documents** | KYC docs, statements | Customer, Doc Type, Status, Verified By, Uploaded Date |
| **Compliance Rules** | RBI regulatory rules | Rule ID, Category, Rule Text, Severity, Active |

### 9.3 Cosmos DB Collections

| Container | Partition Key | Purpose |
|-----------|--------------|---------|
| `transactions` | `/customerId` | Mock transaction data |
| `accounts` | `/customerId` | Mock account data |
| `agent-registry` | `/agentId` | Agent metadata and health |
| `agent-sessions` | `/sessionId` | Conversation context and memory |
| `agent-events` | `/sessionId` | Event stream for dashboard visualization |

---

## 10. Visualization Dashboard

### 10.1 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🏦 BNB Agent Orchestration Dashboard          [Live ● ] [▶ Replay]  │
│                                                                       │
│  Active Agents: 5/16 │ Messages: 3 │ Latency: 2.3s │ Channel: WhatsApp│
├──────────────────────────────────┬────────────────────────────────────┤
│                                  │                                    │
│   ┌─────────────────────────┐   │   EVENT TIMELINE                   │
│   │                         │   │                                    │
│   │   AGENT WORKFLOW GRAPH  │   │   11:30:01 📱 Priya sends msg     │
│   │                         │   │   11:30:02 🤖 Language: Hindi      │
│   │   [Customer]            │   │   11:30:03 🧠 Intent: dispute      │
│   │      │                  │   │   11:30:04 👤 Profile retrieved    │
│   │      ▼                  │   │   11:30:05 💳 Transaction found    │
│   │   [WhatsApp] ──► [Orch] │   │   11:30:05 🔍 Fraud score: 0.82   │
│   │               ┌──┤      │   │   11:30:06 🔒 Card auto-blocked   │
│   │               ▼  ▼      │   │   11:30:06 📝 Case created        │
│   │   [Cust360] [TxnAgent]  │   │   11:30:07 📲 Confirmation sent   │
│   │              │          │   │                                    │
│   │              ▼          │   │                                    │
│   │         [CardMgmt]      │   │                                    │
│   │                         │   │                                    │
│   └─────────────────────────┘   │                                    │
│                                  │                                    │
├──────────────────────────────────┴────────────────────────────────────┤
│                                                                       │
│   AGENT STATE INSPECTOR: Transaction Agent                            │
│                                                                       │
│   Input: { customerId: "CUST-001-PRIYA", action: "find_disputed" }   │
│   Output: { transaction: "₹15,000 at QuickMart", fraudScore: 0.82 } │
│   Reasoning: "Amount exceeds typical spend by 3.2x, merchant not in  │
│              history, time of transaction (2:30 AM) is unusual"       │
│   Tokens: 245 │ Latency: 0.9s │ Confidence: 0.96                    │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 10.2 Event Schema

```typescript
interface AgentEvent {
  eventId: string;           // "evt-20260228-001"
  timestamp: string;         // ISO 8601
  sessionId: string;         // Links all events in a conversation
  useCase: string;           // "UC1-Onboarding" | "UC2-CustomerService" | "UC3-ProactiveHealth"
  agentId: string;           // "transaction-agent"
  agentName: string;         // "Transaction Agent"
  eventType: string;         // "action" | "decision" | "error" | "handoff"
  action: string;            // "find_disputed_transaction"
  input: Record<string, any>;
  output: Record<string, any>;
  reasoning: string;         // LLM chain-of-thought
  tokensUsed: number;
  latencyMs: number;
  confidence: number;        // 0.0 - 1.0
  nextAgents: string[];      // Agents to invoke next
  channel: string;           // "whatsapp" | "voice" | "mobile"
  customerId: string;
  metadata: {
    language: string;        // "hi" | "en" | "hi-en"
    sentiment: string;       // "positive" | "neutral" | "negative" | "frustrated"
  };
}
```

### 10.3 Real-time Event Streaming

```
Azure Functions (Agents) ──emit events──► Cosmos DB (agent-events)
                                              │
                                              │ Change Feed
                                              ▼
                                      Azure SignalR Service
                                              │
                                              │ WebSocket
                                              ▼
                                      React Dashboard (Browser)
```

---

## 11. Technology Stack

### 11.1 Complete Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **LLM** | Azure OpenAI (GPT-4o) | 2024-08-06 |
| **Agent Framework** | Semantic Kernel (Python) | 1.x |
| **Backend** | Python 3.12, Azure Functions | v4 |
| **API Framework** | FastAPI | 0.100+ |
| **CRM** | SharePoint Online (via Microsoft Graph) | v1.0 |
| **Database** | Azure Cosmos DB (NoSQL) | Serverless |
| **Voice** | Azure Communication Services + AI Speech | Latest |
| **WhatsApp** | WhatsApp Business Cloud API | v18+ |
| **Identity** | Azure AD Entra ID (B2C) | v2.0 |
| **Secrets** | Azure Key Vault | Standard |
| **Documents** | Azure AI Document Intelligence | v4.0 |
| **Real-time** | Azure SignalR Service | Latest |
| **Notifications** | Azure Notification Hubs | Standard |
| **Dashboard** | React 18 + TypeScript | 18.x |
| **Graph Viz** | React Flow | 11.x |
| **Charts** | Recharts | 2.x |
| **UI Framework** | Tailwind CSS + shadcn/ui | 3.x |
| **Mobile (Mock)** | React Native | 0.73+ |
| **Mock Data** | Python Faker | 24.x |
| **CI/CD** | GitHub Actions | Latest |

### 11.2 Project Structure

```
bnb-banking-agents/
├── docs/
│   └── architecture.md          ← This document
├── backend/
│   ├── agents/
│   │   ├── orchestrator/        # Central orchestrator agent
│   │   ├── identity_verify/     # UC1: Aadhaar/PAN verification
│   │   ├── kyc_aml/             # UC1: AML compliance
│   │   ├── document_agent/      # UC1: Document extraction
│   │   ├── account_provision/   # UC1: Account creation
│   │   ├── customer_360/        # UC2: Customer profile
│   │   ├── transaction/         # UC2: Transaction queries
│   │   ├── card_mgmt/           # UC2: Card operations
│   │   ├── loan_advisor/        # UC2: Loan recommendations
│   │   ├── spending_analytics/  # UC3: Spending patterns
│   │   ├── savings_advisor/     # UC3: Savings opportunities
│   │   ├── notification/        # UC3: Multi-channel notifications
│   │   ├── compliance_guard/    # UC3: RBI compliance review
│   │   └── voice_summary/       # UC3: Voice call summaries
│   ├── channels/
│   │   ├── whatsapp/            # WhatsApp Business API integration
│   │   └── voice/               # Azure Communication Services
│   ├── shared/
│   │   ├── models/              # Pydantic data models
│   │   ├── crm/                 # SharePoint CRM client
│   │   ├── registry/            # Agent registry client
│   │   ├── events/              # Event emitter for dashboard
│   │   └── mock_data/           # Indian banking mock data
│   ├── host.json
│   ├── requirements.txt
│   └── local.settings.json
├── dashboard/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentGraph/      # React Flow workflow visualization
│   │   │   ├── EventTimeline/   # Scrolling event log
│   │   │   ├── AgentInspector/  # Agent state detail panel
│   │   │   ├── SystemHealth/    # Top bar with metrics
│   │   │   └── RegistryView/    # Agent registry table
│   │   ├── hooks/               # WebSocket, data fetching hooks
│   │   ├── types/               # TypeScript interfaces
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
├── mobile/                      # React Native mock app
├── infra/                       # Azure resource templates (Bicep/ARM)
├── .github/
│   └── workflows/               # CI/CD pipelines
└── README.md
```

---

## 12. Deployment Architecture

### 12.1 Azure Resources

| Resource | Name | Location | Resource Group |
|----------|------|----------|---------------|
| Azure Functions | bnb-agents | Sweden Central | COPILOTCLI |
| Azure OpenAI | bnb-openai | Sweden Central | COPILOTCLI |
| Cosmos DB | bnb-cosmos | Sweden Central | COPILOTCLI |
| Communication Services | wapp | Global (India) | Default-ActivityLogAlerts |
| AI Speech | bnb-speech | Sweden Central | COPILOTCLI |
| AI Document Intelligence | bnb-docint | Sweden Central | COPILOTCLI |
| Key Vault | bnb-poc-kv | Sweden Central | COPILOTCLI |
| SignalR Service | bnb-signalr | Sweden Central | COPILOTCLI |
| Notification Hub | bnb-notifhub | Sweden Central | COPILOTCLI |
| API Management | bnb-apim | Sweden Central | COPILOTCLI |
| Storage Account | bnbstorage | Sweden Central | COPILOTCLI |

### 12.2 Estimated Monthly Cost (PoC)

| Service | Estimated Cost |
|---------|---------------|
| Azure Functions (Consumption) | ~₹0–₹800 |
| Azure OpenAI (GPT-4o, light usage) | ~₹4,000–₹16,000 |
| Azure AI Speech | ~₹800–₹4,000 |
| Azure Communication Services | ~₹800–₹4,000 |
| Azure Cosmos DB (Serverless) | ~₹400–₹2,000 |
| Azure AI Document Intelligence | ~₹800–₹2,400 |
| Azure SignalR Service (Free tier) | ₹0 |
| API Management (Developer) | ~₹4,000 |
| Azure AD B2C (Free tier) | ₹0 |
| Key Vault | ~₹200 |
| SharePoint (via M365 E5 license) | Existing license |
| **Total PoC Estimate** | **~₹12,000–₹33,400/month** |

---

## 13. References

- [Microsoft Multi-Agent Reference Architecture](https://microsoft.github.io/multi-agent-reference-architecture/)
- [Banking Multi-Agent Workshop (Azure Samples)](https://github.com/AzureCosmosDB/banking-multi-agent-workshop)
- [Azure Communication Services Voice Live API](https://learn.microsoft.com/en-us/azure/communication-services/)
- [Azure AI Speech - Hindi Neural Voices](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/)
- [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/)
- [Semantic Kernel (Python)](https://github.com/microsoft/semantic-kernel)
- [React Flow](https://reactflow.dev/)
- [WhatsApp Business Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
