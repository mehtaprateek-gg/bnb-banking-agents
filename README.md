# Bharat National Bank (BNB) — Multi-Agent AI Banking System

A proof-of-concept multi-agent AI system for an Indian retail bank, demonstrating 3 core banking use cases powered by LLM-based AI agents.

## 🏦 Use Cases

1. **Intelligent Customer Onboarding & KYC** — Aadhaar/PAN verification, document processing, auto-provisioning
2. **AI-Powered Customer Service** — Transaction disputes, card management, loan advisory via WhatsApp + Voice
3. **Proactive Financial Health** — Spending analytics, savings recommendations, automated voice summaries

## 🛠️ Tech Stack

- **Backend:** Python 3.12, Azure Functions, FastAPI, Semantic Kernel
- **LLM:** Azure OpenAI (GPT-4o)
- **CRM:** SharePoint Online (Microsoft 365 E5)
- **Voice:** Azure Communication Services + Azure AI Speech (Hindi + English)
- **Chat:** WhatsApp Business Cloud API
- **Data:** Azure Cosmos DB, Azure AI Document Intelligence
- **Dashboard:** React 18, TypeScript, React Flow, Recharts, Tailwind CSS
- **Identity:** Azure AD Entra ID (B2C)

## 📁 Project Structure

```
bnb-banking-agents/
├── docs/           # Architecture documentation
├── backend/        # Python Azure Functions (agents)
├── dashboard/      # React visualization dashboard
├── mobile/         # React Native mock app
├── infra/          # Azure resource templates
└── .github/        # CI/CD workflows
```

## 🇮🇳 Indian Context

- All personas use Indian names (Priya Sharma, Rajesh Iyer, Ananya Deshmukh)
- ₹ currency, Aadhaar/PAN KYC, RBI compliance
- Hindi + English with auto-detection and Hinglish support
- Neural Hindi voices for automated calls

## 📖 Documentation

- [Architecture Document](docs/architecture.md)

## 🚀 Getting Started

*Coming soon — project scaffolding in progress*
