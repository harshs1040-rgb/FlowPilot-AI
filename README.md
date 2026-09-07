\# FlowPilot AI — Multi-Agent Business Automation Platform



FlowPilot AI is a production-oriented multi-agent AI platform designed to transform a user's business objective into a structured, researched, planned, marketed, and verified workflow.



The system coordinates multiple specialized AI agents through an orchestrator and provides real-time workflow progress through a React dashboard.



\## 🚀 Features



\* Multi-agent AI workflow orchestration

\* Automatic task planning and decomposition

\* Web research with external search

\* AI-powered marketing strategy generation

\* Independent verification and quality scoring

\* Gemini → Groq → fallback architecture

\* Real-time agent progress using Server-Sent Events (SSE)

\* PostgreSQL workflow history

\* React dashboard

\* REST API with FastAPI

\* Swagger/OpenAPI API documentation

\* Responsive dark neon UI



\## 🏗️ Architecture



```text

User

&#x20; ↓

React Frontend

&#x20; ↓

FastAPI API

&#x20; ↓

Orchestrator

&#x20; ↓

Planner

&#x20; ↓

Research Agent

&#x20; ↓

Marketing Agent

&#x20; ↓

Verification Agent

&#x20; ↓

Final Result

&#x20; ↓

React Dashboard

&#x20; ↓

PostgreSQL History

```



\## 🤖 Agents



\### Orchestrator Agent



Determines the workflow requirements and selects available tools such as web search.



\### Planner Agent



Breaks the user's objective into structured tasks and produces an execution plan.



\### Research Agent



Performs web research and provides evidence and source information to downstream agents.



\### Marketing Agent



Uses the objective, planning information, and research findings to generate a structured marketing strategy.



\### Verification Agent



Reviews the generated result, checks its quality, and produces a verification status and quality score.



\## 🔄 AI Provider Fallback



FlowPilot AI uses a resilient provider strategy:



```text

Gemini

&#x20; ↓ failure / quota issue

Groq

&#x20; ↓ failure

Development fallback

```



This allows the application to continue operating when the primary AI provider is temporarily unavailable.



\## 🛠️ Technology Stack



\### Backend



\* Python

\* FastAPI

\* SQLModel

\* PostgreSQL

\* Psycopg

\* Google Gemini API

\* Groq API

\* DuckDuckGo Search



\### Frontend



\* React

\* Vite

\* JavaScript

\* CSS



\### Communication



\* REST API

\* Server-Sent Events (SSE)



\## 📁 Project Structure



```text

FlowPilot-AI/

│

├── backend/

│   ├── agents/

│   │   ├── orchestrator.py

│   │   ├── planner.py

│   │   ├── research.py

│   │   ├── marketing.py

│   │   └── verifier.py

│   │

│   ├── tools/

│   │   ├── web\_search.py

│   │   └── \_\_init\_\_.py

│   │

│   ├── config.py

│   ├── database.py

│   ├── main.py

│   ├── models.py

│   ├── requirements.txt

│   └── .env

│

├── frontend/

│   ├── src/

│   ├── public/

│   ├── package.json

│   └── vite.config.js

│

├── docs/

├── .gitignore

├── README.md

└── venv/

```



\## ⚙️ Installation



\### 1. Clone the project



```bash

git clone <your-repository-url>

cd FlowPilot-AI

```



\### 2. Create and activate the Python environment



```powershell

python -m venv venv

.\\venv\\Scripts\\Activate.ps1

```



\### 3. Install backend dependencies



```powershell

pip install -r .\\backend\\requirements.txt

```



\### 4. Configure environment variables



Create:



```text

backend/.env

```



Add your own API keys and PostgreSQL configuration.



Never commit `.env` to GitHub.



\### 5. Start the backend



```powershell

cd backend

python -m uvicorn main:app --reload

```



Backend:



```text

http://127.0.0.1:8000

```



Swagger documentation:



```text

http://127.0.0.1:8000/docs

```



\### 6. Start the frontend



Open another terminal:



```powershell

cd frontend

npm install

npm run dev

```



Frontend:



```text

http://localhost:5173

```



\## 🔌 API Endpoints



| Endpoint       | Method | Purpose                           |

| -------------- | ------ | --------------------------------- |

| `/`            | GET    | Application information           |

| `/health`      | GET    | Health check                      |

| `/orchestrate` | POST   | Run orchestration                 |

| `/plan`        | POST   | Generate a plan                   |

| `/research`    | POST   | Perform research                  |

| `/marketing`   | POST   | Generate marketing strategy       |

| `/run`         | POST   | Run complete workflow             |

| `/run-stream`  | GET    | Run workflow with live SSE events |

| `/history`     | GET    | Retrieve workflow history         |



\## 📊 Example Workflow



Example user objective:



```text

Create a marketing strategy for an AI productivity app for college students.

```



FlowPilot AI processes the objective through:



```text

Orchestrator

&#x20;     ↓

Planner

&#x20;     ↓

Research

&#x20;     ↓

Marketing

&#x20;     ↓

Verification

&#x20;     ↓

Final Result

```



The frontend displays the progress of each agent in real time.



\## 💾 Workflow History



Completed workflows are stored in PostgreSQL.



The History section of the dashboard allows previously completed workflows to be viewed again.



\## 🔐 Security



\* API keys are stored in environment variables.

\* `.env` is excluded from Git.

\* Virtual environments are excluded from Git.

\* Python cache files are excluded from Git.

\* Frontend dependencies are excluded from Git.



Do not publish API keys, database passwords, or other credentials.



\## 🎯 Project Goals



FlowPilot AI demonstrates practical implementation of:



\* Multi-agent AI systems

\* Agent orchestration

\* AI provider fallback

\* Tool selection

\* Web research

\* Structured workflows

\* Verification pipelines

\* Real-time frontend/backend communication

\* Persistent workflow storage



\## 🔮 Future Improvements



Potential future extensions include:



\* Additional specialized agents

\* Retrieval-Augmented Generation (RAG)

\* Long-term agent memory

\* More external tools

\* Advanced observability

\* Docker deployment

\* Cloud deployment

\* Authentication and user accounts

\* More sophisticated verification and retry mechanisms



\## 👨‍💻 Project



\*\*FlowPilot AI — Multi-Agent Business Automation Platform\*\*



Built as a practical AI engineering project demonstrating multi-agent orchestration, full-stack development, API integration, research automation, verification, and persistent workflow management.



