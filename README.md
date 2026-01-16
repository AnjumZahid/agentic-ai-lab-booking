# Agentic AI Medical Lab Booking System

A full-stack, AI-driven medical lab test booking system built using **Agentic AI**, **LangGraph orchestration**, and **MCP-based tool calling**.  
The system demonstrates how LLM-powered agents can safely reason, call backend tools, and manage real-world workflows such as medical lab scheduling and bookings.

---

## ▶️ How to Run the App >>>> Demo Video

🎥 **Watch the full demo here:**  
👉 [https://www.youtube.com/<YOUR_DEMO_LINK>](https://youtu.be/xOaPJ_Pyg_w?si=tbIr90m5iUUck0Fq)

The demo shows:
- AI chatbot booking lab tests
- Tool-based reasoning and slot validation
- Admin panel for managing lab operations

---

## 🚀 How to Run the Project Locally

### 1️⃣ Clone the repository
```bash
git clone https://github.com/AnjumZahid/agentic-ai-lab-booking.git
cd agentic-ai-lab-booking

2️⃣ Create and activate virtual environment
conda create -n lab_ai python=3.10 -y
conda activate lab_ai

3️⃣ Install dependencies

*Create .env file and put: 
GOOGLE_API_KEY = "Your Google API KEY"

4️⃣ Start backend server (FastAPI) & crud_backend.py
python server.py
uvicorn backend.crud_backend:app --reload


Backend will be available at:

http://localhost:8000

5️⃣ Run the Streamlit frontend
streamlit run frontend_run.py OR streamlit run frontend_run.py


Frontend will open in your browser:

http://localhost:8501

🧠 System Architecture (High Level)

AI Chatbot (LangGraph)
Orchestrates multi-step reasoning, tool execution, and conversation state.

MCP Tool Layer
Secure tool calls for schedules, availability, bookings, and validation.

FastAPI Backend
Business logic, booking rules, and database operations.

Streamlit Frontend
User chatbot interface + Admin dashboard.

SQLite Database
Stores tests, schedules, doctors, holidays, and bookings.

🛠 Key Features
🤖 AI Chatbot for Lab Booking

Natural language booking

Availability checks

Doctor requirement handling

Context-aware, streaming responses

🔗 Agentic AI with MCP Tool Calls

LLM decides when and which tool to call

No hardcoded flows

Safe, structured execution

⚙️ Admin Panel

Manage lab tests

Configure schedules & windows

Add doctors & holidays

Assign tests to doctors

View & manage bookings

📅 Advanced Booking Logic

Lab holidays & partial days

Test-specific closures

Doctor availability

Proportional slot calculation

Concurrency-safe booking

🧩 LangGraph Orchestration

Threaded conversations

Stateful agent execution

Reliable tool orchestration

Production-grade control vs no-code tools

🧪 Tech Stack

Python

LangGraph

LangChain

MCP (Model Context Protocol)

FastAPI

Streamlit

SQLite

LLMs (tool-calling capable)

📌 Why LangGraph (vs CrewAI / n8n)

Fine-grained control over execution

Stateful, multi-turn agent flows

Safe tool invocation

Easier debugging & observability

Designed for real production systems

📂 Project Structure
.
├── backend/                # FastAPI backend & booking logic
├── frontend/               # Streamlit admin pages
├── utils/                  # Helper & validation utilities
├── langgraph_mcp_backend.py# Agent + tool orchestration
├── frontend_chatpage.py    # Chat interface
├── frontend_run.py         # Streamlit entry point
├── server.py               # FastAPI server
├── requirements.txt
└── README.md

🔒 Disclaimer

This project is a technical demo for showcasing agentic AI and orchestration patterns.
It is not a certified medical system.

🤝 Connect

If you’re interested in:

Agentic AI

LangGraph orchestration

MCP tool calling

Healthcare AI workflows

Feel free to connect on LinkedIn or reach out on GitHub.

⭐ If you find this project useful, please consider starring the repo!

