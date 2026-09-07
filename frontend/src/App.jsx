import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL =
  "https://flowpilot-ai-zcg1.onrender.com";

const AGENTS = [
  {
    number: "01",
    name: "Orchestrator",
    description: "Plans and coordinates the workflow",
    icon: "✦",
  },
  {
    number: "02",
    name: "Planner",
    description: "Breaks the goal into executable tasks",
    icon: "◇",
  },
  {
    number: "03",
    name: "Research",
    description: "Analyzes markets and opportunities",
    icon: "⌕",
  },
  {
    number: "04",
    name: "Marketing",
    description: "Creates actionable strategies",
    icon: "↗",
  },
  {
    number: "05",
    name: "Verification",
    description: "Reviews and validates the result",
    icon: "✓",
  },
];

const AGENT_NAMES = [
  "Orchestrator Agent",
  "Planner Agent",
  "Research Agent",
  "Marketing Agent",
  "Verification Agent",
];

const INITIAL_STATUSES = {
  "Orchestrator Agent": "Ready",
  "Planner Agent": "Ready",
  "Research Agent": "Ready",
  "Marketing Agent": "Ready",
  "Verification Agent": "Ready",
};

function App() {
  const [task, setTask] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState("");
  const [activePage, setActivePage] = useState("dashboard");

  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  const [agentStatuses, setAgentStatuses] =
    useState(INITIAL_STATUSES);

  // =========================================
  // AUTHENTICATION STATE
  // =========================================

  const [authMode, setAuthMode] = useState("login");

  const [isAuthenticated, setIsAuthenticated] =
    useState(
      Boolean(localStorage.getItem("flowpilot_token"))
    );

  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  // =========================================
  // LOAD HISTORY
  // =========================================

  useEffect(() => {
    if (isAuthenticated) {
      loadHistory();
    }
  }, [isAuthenticated]);

  const loadHistory = async () => {
    setHistoryLoading(true);
    setHistoryError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/history`
      );

      if (!response.ok) {
        throw new Error(
          `History request failed: ${response.status}`
        );
      }

      const data = await response.json();

      if (!Array.isArray(data)) {
        throw new Error(
          "History API returned an unexpected response."
        );
      }

      const formattedHistory = data.map((item) => ({
        id: item.id,
        objective: item.objective,
        status: item.status,
        result: item.result,
        date: item.created_at
          ? new Date(
              item.created_at
            ).toLocaleString()
          : "Unknown date",
      }));

      setHistory(formattedHistory);

      console.log(
        "PostgreSQL history loaded:",
        formattedHistory
      );
    } catch (error) {
      console.error(
        "Could not load workflow history:",
        error
      );

      setHistoryError(
        "Could not connect to the workflow history service."
      );
    } finally {
      setHistoryLoading(false);
    }
  };

  // =========================================
  // LOGIN / SIGNUP
  // =========================================

  const handleAuth = async (event) => {
    event.preventDefault();

    setAuthError("");

    if (!authEmail.trim() || !authPassword) {
      setAuthError(
        "Please enter your email and password."
      );
      return;
    }

    setAuthLoading(true);

    try {
      const endpoint =
        authMode === "login"
          ? "/auth/login"
          : "/auth/signup";

      const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: authEmail.trim(),
            password: authPassword,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Authentication failed."
        );
      }

      localStorage.setItem(
        "flowpilot_token",
        data.access_token
      );

      localStorage.setItem(
        "flowpilot_email",
        data.user.email
      );

      setIsAuthenticated(true);

      setAuthEmail("");
      setAuthPassword("");
      setAuthError("");
    } catch (error) {
      console.error(
        "Authentication error:",
        error
      );

      setAuthError(
        error.message ||
          "Could not connect to FlowPilot."
      );
    } finally {
      setAuthLoading(false);
    }
  };

  // =========================================
  // LOGOUT
  // =========================================

  const handleLogout = () => {
    localStorage.removeItem(
      "flowpilot_token"
    );

    localStorage.removeItem(
      "flowpilot_email"
    );

    setIsAuthenticated(false);
    setAuthMode("login");
    setAuthEmail("");
    setAuthPassword("");
    setAuthError("");
    setTask("");
    setResult(null);
    setActivePage("dashboard");
  };

  // =========================================
  // RUN WORKFLOW
  // =========================================

  const runWorkflow = () => {
    if (!task.trim() || loading) {
      return;
    }

    setLoading(true);
    setResult(null);
    setAgentStatuses(INITIAL_STATUSES);
    setCurrentAgent("");
    setActivePage("dashboard");

    const encodedTask = encodeURIComponent(
      task.trim()
    );

    const eventSource = new EventSource(
      `${API_BASE_URL}/run-stream?task=${encodedTask}`
    );

    // =========================================
    // AGENT START
    // =========================================

    eventSource.addEventListener(
      "agent_start",
      (event) => {
        try {
          const message = JSON.parse(
            event.data
          );

          const agent = message.agent;

          console.log(
            "Agent started:",
            agent
          );

          setCurrentAgent(agent);

          setAgentStatuses((previous) => {
            const updated = {
              ...previous,
            };

            const currentIndex =
              AGENT_NAMES.indexOf(agent);

            AGENT_NAMES.forEach((name) => {
              const index =
                AGENT_NAMES.indexOf(name);

              if (index < currentIndex) {
                updated[name] = "Completed";
              } else if (name === agent) {
                updated[name] = "Running";
              } else {
                updated[name] = "Ready";
              }
            });

            return updated;
          });
        } catch (error) {
          console.error(
            "Agent start parsing error:",
            error
          );
        }
      }
    );

    // =========================================
    // AGENT COMPLETE
    // =========================================

    eventSource.addEventListener(
      "agent_complete",
      (event) => {
        try {
          const message = JSON.parse(
            event.data
          );

          const agent = message.agent;

          console.log(
            "Agent completed:",
            agent
          );

          setAgentStatuses((previous) => ({
            ...previous,
            [agent]: "Completed",
          }));
        } catch (error) {
          console.error(
            "Agent complete parsing error:",
            error
          );
        }
      }
    );

    // =========================================
    // WORKFLOW COMPLETE
    // =========================================

    eventSource.addEventListener(
      "workflow_complete",
      async (event) => {
        try {
          const message = JSON.parse(
            event.data
          );

          console.log(
            "Workflow completed:",
            message
          );

          setResult(message);

          setAgentStatuses({
            "Orchestrator Agent": "Completed",
            "Planner Agent": "Completed",
            "Research Agent": "Completed",
            "Marketing Agent": "Completed",
            "Verification Agent": "Completed",
          });

          setCurrentAgent(
            "Workflow Complete"
          );

          setLoading(false);

          eventSource.close();

          await loadHistory();
        } catch (error) {
          console.error(
            "Workflow result parsing error:",
            error
          );

          setResult({
            success: false,
            error:
              "Could not read the workflow result.",
          });

          setLoading(false);
          setCurrentAgent("");

          eventSource.close();
        }
      }
    );

    // =========================================
    // BACKEND ERROR EVENT
    // =========================================

    eventSource.addEventListener(
      "error",
      (event) => {
        console.error(
          "FlowPilot backend error:",
          event
        );

        setResult({
          success: false,
          error:
            "The workflow encountered an error.",
        });

        setLoading(false);
        setCurrentAgent("");

        eventSource.close();
      }
    );

    // =========================================
    // SSE CONNECTION ERROR
    // =========================================

    eventSource.onerror = (error) => {
      console.error(
        "SSE connection error:",
        error
      );

      setLoading(false);
      setCurrentAgent("");

      eventSource.close();
    };
  };

  // =========================================
  // RESET WORKFLOW
  // =========================================

  const resetWorkflow = () => {
    setTask("");
    setResult(null);
    setLoading(false);
    setCurrentAgent("");
    setAgentStatuses(INITIAL_STATUSES);
    setActivePage("dashboard");
  };

  // =========================================
  // OPEN HISTORY ITEM
  // =========================================

  const openHistoryItem = (item) => {
    setTask(item.objective);
    setResult(item.result);

    setAgentStatuses({
      "Orchestrator Agent": "Completed",
      "Planner Agent": "Completed",
      "Research Agent": "Completed",
      "Marketing Agent": "Completed",
      "Verification Agent": "Completed",
    });

    setCurrentAgent(
      "Workflow Complete"
    );

    setActivePage("dashboard");
  };

  // =========================================
  // AUTH SCREEN
  // =========================================

  if (!isAuthenticated) {
    return (
      <div className="auth-app">
        <div className="auth-container">

          <div className="auth-brand">
            <div className="auth-logo">
              ✦
            </div>

            <div>
              <h1>FlowPilot</h1>
              <p>
                AI Automation Platform
              </p>
            </div>
          </div>

          <div className="auth-card">

            <div className="auth-header">
              <p className="eyebrow">
                {authMode === "login"
                  ? "WELCOME BACK"
                  : "GET STARTED"}
              </p>

              <h2>
                {authMode === "login"
                  ? "Sign in to FlowPilot"
                  : "Create your account"}
              </h2>

              <p>
                {authMode === "login"
                  ? "Access your AI-powered business automation workspace."
                  : "Create an account and start automating your business workflows."}
              </p>
            </div>

            {authError && (
              <div className="auth-error">
                ⚠ {authError}
              </div>
            )}

            <form
              className="auth-form"
              onSubmit={handleAuth}
            >

              <div className="form-group">
                <label>
                  Email address
                </label>

                <input
                  type="email"
                  value={authEmail}
                  onChange={(event) =>
                    setAuthEmail(
                      event.target.value
                    )
                  }
                  placeholder="you@example.com"
                  autoComplete="email"
                  disabled={authLoading}
                />
              </div>

              <div className="form-group">
                <label>
                  Password
                </label>

                <input
                  type="password"
                  value={authPassword}
                  onChange={(event) =>
                    setAuthPassword(
                      event.target.value
                    )
                  }
                  placeholder="Enter your password"
                  autoComplete={
                    authMode === "login"
                      ? "current-password"
                      : "new-password"
                  }
                  disabled={authLoading}
                />
              </div>

              <button
                type="submit"
                className="auth-button"
                disabled={authLoading}
              >
                {authLoading
                  ? "Please wait..."
                  : authMode === "login"
                  ? "Sign In"
                  : "Create Account"}
              </button>

            </form>

            <div className="auth-switch">

              <span>
                {authMode === "login"
                  ? "Don't have an account?"
                  : "Already have an account?"}
              </span>

              <button
                type="button"
                onClick={() => {
                  setAuthMode(
                    authMode === "login"
                      ? "signup"
                      : "login"
                  );

                  setAuthError("");
                }}
              >
                {authMode === "login"
                  ? "Create account"
                  : "Sign in"}
              </button>

            </div>

          </div>

          <div className="auth-footer">
            <span>
              FlowPilot AI
            </span>

            <span>
              Multi-Agent Business Automation
            </span>
          </div>

        </div>
      </div>
    );
  }

  // =========================================
  // MAIN APPLICATION
  // =========================================

  return (
    <div className="app">

      {/* SIDEBAR */}

      <aside className="sidebar">

        <div className="logo">

          <div className="logo-icon">
            ✦
          </div>

          <div>
            <h2>
              FlowPilot
            </h2>

            <span>
              AI Automation
            </span>
          </div>

        </div>

        <nav>

          <button
            className={`nav-item ${
              activePage === "dashboard"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage("dashboard")
            }
          >
            ⌂ Dashboard
          </button>

          <button
            className={`nav-item ${
              activePage === "workflows"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage("workflows")
            }
          >
            ⚡ Workflows
          </button>

          <button
            className={`nav-item ${
              activePage === "agents"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage("agents")
            }
          >
            ◈ Agents
          </button>

          <button
            className={`nav-item ${
              activePage === "history"
                ? "active"
                : ""
            }`}
            onClick={() => {
              setActivePage("history");
              loadHistory();
            }}
          >
            ▣ History
          </button>

        </nav>

        <div className="sidebar-bottom">

          <div className="status-dot"></div>

          <span>
            System Online
          </span>

        </div>

      </aside>

      {/* MAIN */}

      <main className="main">

        {/* =========================
            DASHBOARD
        ========================= */}

        {activePage === "dashboard" && (
          <>

            <header className="topbar">

              <div>

                <p className="eyebrow">
                  MULTI-AGENT PLATFORM
                </p>

                <h1>
                  Business Automation
                </h1>

                <p className="subtitle">
                  Give FlowPilot a goal and let AI
                  agents build the workflow.
                </p>

              </div>

              <div className="profile">

                <div className="avatar">
                  FP
                </div>

                <div className="profile-info">

                  <span>
                    {localStorage.getItem(
                      "flowpilot_email"
                    ) || "Workspace"}
                  </span>

                  <small>
                    FlowPilot Account
                  </small>

                </div>

                <button
                  className="logout-button"
                  onClick={handleLogout}
                >
                  Logout
                </button>

              </div>

            </header>

            {/* TASK CARD */}

            <section className="task-card">

              <div className="card-title">

                <div>

                  <h2>
                    What do you want to accomplish?
                  </h2>

                  <p>
                    Describe your business objective
                    in natural language.
                  </p>

                </div>

                <span className="ai-badge">
                  AI POWERED
                </span>

              </div>

              <textarea
                value={task}
                onChange={(event) =>
                  setTask(event.target.value)
                }
                placeholder="Example: Create a marketing strategy for a new online learning platform for college students..."
                disabled={loading}
              />

              <div className="task-footer">

                <span>
                  {task.length} characters
                </span>

                <div className="task-actions">

                  {result && !loading && (
                    <button
                      className="reset-button"
                      onClick={resetWorkflow}
                    >
                      ↻ New Workflow
                    </button>
                  )}

                  <button
                    className="run-button"
                    onClick={runWorkflow}
                    disabled={
                      loading ||
                      !task.trim()
                    }
                  >
                    {loading
                      ? "Running..."
                      : "▶ Run Workflow"}
                  </button>

                </div>

              </div>

            </section>

            {/* AGENT WORKFLOW */}

            <section className="agents-section">

              <div className="section-heading">

                <div>

                  <h2>
                    Agent Workflow
                  </h2>

                  <p>
                    AI agents collaborate to complete
                    your objective.
                  </p>

                </div>

              </div>

              <div className="agent-grid">

                {AGENTS.map((agent) => (
                  <AgentCard
                    key={agent.name}
                    number={agent.number}
                    name={agent.name}
                    description={
                      agent.description
                    }
                    icon={agent.icon}
                    status={
                      agentStatuses[
                        `${agent.name} Agent`
                      ]
                    }
                  />
                ))}

              </div>

            </section>

            {/* LIVE STATUS */}

            {loading && (
              <section className="loading-card">

                <div className="loader"></div>

                <div>

                  <h3>
                    {currentAgent ||
                      "FlowPilot"}{" "}
                    is working...
                  </h3>

                  <p>
                    {currentAgent
                      ? `${currentAgent} is currently processing your objective.`
                      : "AI agents are coordinating your workflow."}
                  </p>

                </div>

              </section>
            )}

            {/* RESULTS */}

            {result && !loading && (
              <section className="results-section">

                {result.success ? (
                  <>

                    {/* RESULT HEADER */}

                    <div className="result-header">

                      <div>

                        <p className="eyebrow">
                          WORKFLOW COMPLETE
                        </p>

                        <h2>
                          Execution Results
                        </h2>

                      </div>

                      <div className="task-actions">

                        <button
                          className="reset-button"
                          onClick={() =>
                            downloadReport(
                              result,
                              task
                            )
                          }
                        >
                          ↓ Download Report
                        </button>

                        <div className="success-badge">
                          ✓ SUCCESS
                        </div>

                      </div>

                    </div>

                    {/* ORCHESTRATOR */}

                    <div className="orchestrator-card">

                      <div className="orchestrator-header">

                        <div>

                          <span className="result-label">
                            ORCHESTRATOR AGENT
                          </span>

                          <h3>
                            Workflow Coordination
                          </h3>

                        </div>

                        <span className="completed-badge">
                          ✓ COMPLETED
                        </span>

                      </div>

                      <div className="orchestrator-content">

                        {/* SELECTED AGENTS */}

                        <div className="orchestrator-section">

                          <span>
                            SELECTED AGENTS
                          </span>

                          <div className="agent-tags">

                            {result
                              .orchestrator
                              ?.orchestration
                              ?.selected_agents
                              ?.map(
                                (agent) => (
                                  <div
                                    className="agent-tag"
                                    key={agent}
                                  >
                                    ✓ {agent}
                                  </div>
                                )
                              )}

                          </div>

                        </div>

                        {/* EXECUTION ORDER */}

                        <div className="orchestrator-section">

                          <span>
                            EXECUTION ORDER
                          </span>

                          <div className="execution-list">

                            {result
                              .orchestrator
                              ?.orchestration
                              ?.execution_order
                              ?.map(
                                (
                                  agent,
                                  index
                                ) => (
                                  <div
                                    className="execution-item"
                                    key={`${agent}-${index}`}
                                  >

                                    <div className="execution-number">
                                      {index + 1}
                                    </div>

                                    <strong>
                                      {agent}
                                    </strong>

                                    {index <
                                      result
                                        .orchestrator
                                        .orchestration
                                        .execution_order
                                        .length -
                                        1 && (
                                      <div className="execution-arrow">
                                        →
                                      </div>
                                    )}

                                  </div>
                                )
                              )}

                          </div>

                        </div>

                        {/* REASONING */}

                        <div className="orchestrator-section">

                          <span>
                            ORCHESTRATOR REASONING
                          </span>

                          <p className="reasoning">
                            {result
                              .orchestrator
                              ?.orchestration
                              ?.reasoning ||
                              "No reasoning available."}
                          </p>

                        </div>

                      </div>

                    </div>

                    {/* PLANNER */}

                    <ResultCard
                      title="Planner Agent"
                      icon="◇"
                      content={
                        result.planner?.plan
                      }
                    />

                    {/* RESEARCH */}

                    <ResultCard
                      title="Research Agent"
                      icon="⌕"
                      content={
                        result.research?.research
                      }
                    />

                    {/* RESEARCH SOURCES */}

                    {result.research?.sources
                      ?.length > 0 && (
                      <SourcesCard
                        sources={
                          result.research.sources
                        }
                      />
                    )}

                    {/* MARKETING */}

                    <ResultCard
                      title="Marketing Agent"
                      icon="↗"
                      content={
                        result.marketing
                          ?.marketing_plan
                      }
                    />

                    {/* VERIFICATION */}

                    <ResultCard
                      title="Verification Agent"
                      icon="✓"
                      content={
                        result.verification
                          ?.verification
                      }
                    />

                  </>
                ) : (
                  <div className="error-card">

                    <h3>
                      ⚠ Workflow Error
                    </h3>

                    <p>
                      {result.error ||
                        "Unknown workflow error."}
                    </p>

                  </div>
                )}

              </section>
            )}

          </>
        )}

        {/* =========================
            WORKFLOWS PAGE
        ========================= */}

        {activePage === "workflows" && (
          <>

            <PageHeader
              eyebrow="WORKFLOW ENGINE"
              title="Workflows"
              subtitle="Build and execute AI-powered business workflows."
            />

            <section className="info-grid">

              <InfoCard
                icon="✦"
                title="Business Automation"
                text="Give FlowPilot a business goal and the AI agents coordinate the work automatically."
              />

              <InfoCard
                icon="◇"
                title="Sequential Execution"
                text="Agents work in a controlled sequence so each stage can use the output of the previous stage."
              />

              <InfoCard
                icon="✓"
                title="Verification"
                text="The final Verification Agent reviews the generated result before the workflow is completed."
              />

            </section>

            <section className="workflow-preview">

              <div className="result-header">

                <div>

                  <p className="eyebrow">
                    DEFAULT WORKFLOW
                  </p>

                  <h2>
                    Business Strategy Workflow
                  </h2>

                </div>

                <button
                  className="run-button"
                  onClick={() =>
                    setActivePage("dashboard")
                  }
                >
                  Create Workflow →
                </button>

              </div>

              <div className="execution-list">

                {AGENT_NAMES.map(
                  (agent, index) => (
                    <div
                      className="execution-item"
                      key={agent}
                    >

                      <div className="execution-number">
                        {index + 1}
                      </div>

                      <strong>
                        {agent}
                      </strong>

                      {index <
                        AGENT_NAMES.length -
                          1 && (
                        <div className="execution-arrow">
                          →
                        </div>
                      )}

                    </div>
                  )
                )}

              </div>

            </section>

          </>
        )}

        {/* =========================
            AGENTS PAGE
        ========================= */}

        {activePage === "agents" && (
          <>

            <PageHeader
              eyebrow="AI AGENT SYSTEM"
              title="Agents"
              subtitle="Five specialized agents collaborate inside FlowPilot."
            />

            <div className="agent-page-grid">

              {AGENTS.map((agent) => (
                <AgentCard
                  key={agent.name}
                  number={agent.number}
                  name={agent.name}
                  description={
                    agent.description
                  }
                  icon={agent.icon}
                  status="Ready"
                />
              ))}

            </div>

            <section className="workflow-preview">

              <div className="result-header">

                <div>

                  <p className="eyebrow">
                    AGENT ARCHITECTURE
                  </p>

                  <h2>
                    Multi-Agent Collaboration
                  </h2>

                </div>

              </div>

              <p className="reasoning">
                FlowPilot uses specialized AI agents
                instead of relying on a single model
                response. The Orchestrator coordinates
                the workflow, the Planner creates the
                execution plan, Research gathers
                information, Marketing creates the
                strategy, and Verification reviews
                the final result.
              </p>

            </section>

          </>
        )}

        {/* =========================
            HISTORY PAGE
        ========================= */}

        {activePage === "history" && (
          <>

            <PageHeader
              eyebrow="WORKFLOW HISTORY"
              title="History"
              subtitle="Review workflows saved in PostgreSQL."
            />

            {historyLoading ? (
              <section className="empty-state">

                <div className="loader"></div>

                <h2>
                  Loading history...
                </h2>

                <p>
                  Fetching your saved workflows
                  from PostgreSQL.
                </p>

              </section>
            ) : historyError ? (
              <section className="error-card">

                <h3>
                  ⚠ History Error
                </h3>

                <p>
                  {historyError}
                </p>

                <button
                  className="run-button"
                  onClick={loadHistory}
                >
                  ↻ Retry
                </button>

              </section>
            ) : history.length === 0 ? (
              <section className="empty-state">

                <div className="empty-icon">
                  ▣
                </div>

                <h2>
                  No workflows yet
                </h2>

                <p>
                  Run your first workflow from
                  the Dashboard and it will appear
                  here.
                </p>

                <button
                  className="run-button"
                  onClick={() =>
                    setActivePage("dashboard")
                  }
                >
                  Start Workflow →
                </button>

              </section>
            ) : (
              <section className="history-list">

                {history.map((item) => (
                  <div
                    className="history-item"
                    key={item.id}
                  >

                    <div className="history-icon">
                      ✓
                    </div>

                    <div className="history-info">

                      <h3>
                        {item.objective}
                      </h3>

                      <p>
                        {item.status ===
                        "completed"
                          ? "Completed"
                          : "Failed"}{" "}
                        {item.date}
                      </p>

                    </div>

                    <button
                      className="history-button"
                      onClick={() =>
                        openHistoryItem(item)
                      }
                    >
                      View →
                    </button>

                  </div>
                ))}

              </section>
            )}

          </>
        )}

      </main>

    </div>
  );
}

// =========================================
// PAGE HEADER
// =========================================

function PageHeader({
  eyebrow,
  title,
  subtitle,
}) {
  return (
    <header className="topbar">

      <div>

        <p className="eyebrow">
          {eyebrow}
        </p>

        <h1>
          {title}
        </h1>

        <p className="subtitle">
          {subtitle}
        </p>

      </div>

      <div className="profile">

        <div className="avatar">
          FP
        </div>

        <div className="profile-info">

          <span>
            {localStorage.getItem(
              "flowpilot_email"
            ) || "Workspace"}
          </span>

          <small>
            FlowPilot Account
          </small>

        </div>

      </div>

    </header>
  );
}

// =========================================
// INFO CARD
// =========================================

function InfoCard({
  icon,
  title,
  text,
}) {
  return (
    <div className="result-card">

      <div className="result-card-header">

        <div className="result-title">

          <span className="result-icon">
            {icon}
          </span>

          <h3>
            {title}
          </h3>

        </div>

        <span>
          ACTIVE
        </span>

      </div>

      <div className="result-content">
        {text}
      </div>

    </div>
  );
}

// =========================================
// AGENT CARD
// =========================================

function AgentCard({
  number,
  name,
  description,
  icon,
  status = "Ready",
}) {
  const statusClass =
    status.toLowerCase();

  return (
    <div
      className={`agent-card ${statusClass}`}
    >

      <div className="agent-top">

        <span className="agent-number">
          {number}
        </span>

        <span className="agent-icon">
          {icon}
        </span>

      </div>

      <h3>
        {name} Agent
      </h3>

      <p>
        {description}
      </p>

      <div
        className={`agent-status ${statusClass}`}
      >

        <span className="status-indicator"></span>

        {status}

      </div>

    </div>
  );
}

// =========================================
// RESULT CARD
// =========================================

function ResultCard({
  title,
  icon,
  content,
}) {
  return (
    <div className="result-card">

      <div className="result-card-header">

        <div className="result-title">

          <span className="result-icon">
            {icon}
          </span>

          <h3>
            {title}
          </h3>

        </div>

        <span>
          COMPLETED
        </span>

      </div>

      <div className="result-content">
        {content ||
          "No output available."}
      </div>

    </div>
  );
}

// =========================================
// SOURCES CARD
// =========================================

function SourcesCard({
  sources = [],
}) {
  return (
    <div className="result-card sources-card">

      <div className="result-card-header">

        <div className="result-title">

          <span className="result-icon">
            🔎
          </span>

          <h3>
            Research Sources
          </h3>

        </div>

        <span>
          WEB SOURCES
        </span>

      </div>

      <div className="sources-list">

        {sources.map(
          (source, index) => (
            <a
              key={`${source.url}-${index}`}
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="source-item"
            >

              <span className="source-number">
                {index + 1}
              </span>

              <div>

                <strong>
                  {source.title ||
                    "Research Source"}
                </strong>

                <small>
                  {source.url}
                </small>

              </div>

              <span className="source-arrow">
                ↗
              </span>

            </a>
          )
        )}

      </div>

    </div>
  );
}

// =========================================
// DOWNLOAD REPORT
// =========================================

function downloadReport(result, task) {
  if (!result) {
    return;
  }

  const selectedAgents =
    result.orchestrator
      ?.orchestration
      ?.selected_agents
      ?.join("\n") ||
    "Not available";

  const executionOrder =
    result.orchestrator
      ?.orchestration
      ?.execution_order
      ?.join(" → ") ||
    "Not available";

  const reasoning =
    result.orchestrator
      ?.orchestration
      ?.reasoning ||
    "Not available";

  const planner =
    result.planner?.plan ||
    "No planner output available.";

  const research =
    result.research?.research ||
    "No research output available.";

  const marketing =
    result.marketing?.marketing_plan ||
    "No marketing output available.";

  const verification =
    result.verification?.verification ||
    "No verification output available.";

  const report = `
FLOWPILOT AI
MULTI-AGENT BUSINESS AUTOMATION PLATFORM
==========================================

WORKFLOW OBJECTIVE
${task || "No objective provided"}

GENERATED
${new Date().toLocaleString()}

==========================================
ORCHESTRATOR AGENT
==========================================

SELECTED AGENTS

${selectedAgents}

EXECUTION ORDER

${executionOrder}

REASONING

${reasoning}


==========================================
PLANNER AGENT
==========================================

${planner}


==========================================
RESEARCH AGENT
==========================================

${research}


==========================================
MARKETING AGENT
==========================================

${marketing}


==========================================
VERIFICATION AGENT
==========================================

${verification}


==========================================
FLOWPILOT AI
==========================================

Multi-Agent Business Automation Platform

Report generated automatically by FlowPilot AI.
`;

  const blob = new Blob(
    [report],
    {
      type: "text/plain;charset=utf-8",
    }
  );

  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;

  link.download =
    "FlowPilot-Workflow-Report.txt";

  document.body.appendChild(link);

  link.click();

  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}

export default App;