import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useSearchParams } from "react-router-dom";
import { apiGet, apiPost, getAuthToken, setAuthToken, submitGatewayForm } from "./api";

const defaultUserId = "";

function useUserId() {
  const [userId, setUserId] = useState(() => localStorage.getItem("nepsense_user_id") || defaultUserId);

  useEffect(() => {
    if (userId) {
      localStorage.setItem("nepsense_user_id", userId);
      return;
    }
    localStorage.removeItem("nepsense_user_id");
  }, [userId]);

  return [userId, setUserId];
}

function useVisibleApiKey() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("nepsense_visible_api_key") || "");

  useEffect(() => {
    if (apiKey) {
      localStorage.setItem("nepsense_visible_api_key", apiKey);
      return;
    }
    localStorage.removeItem("nepsense_visible_api_key");
  }, [apiKey]);

  return [apiKey, setApiKey];
}

function useSessionToken() {
  const [token, setToken] = useState(() => getAuthToken());

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  return [token, setToken];
}

function Page({ title, subtitle, children }) {
  return (
    <main className="page-shell">
      <section className="page-header">
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </section>
      {children}
    </main>
  );
}

function TopNav({ account, onLogout }) {
  const location = useLocation();
  const links = [
    ["/", "Home"],
    ["/pricing", "Pricing"],
    ["/docs", "Docs"],
    ["/dashboard", "Dashboard"],
    ["/data", "Data"],
    ["/status", "Status"],
  ];
  const planLabel = account?.api_key?.plan_id && account.api_key.plan_id !== "free" ? "Paid" : "Free";

  return (
    <header className="top-nav">
      <div className="brand-block">
        <span className="brand">NepSense</span>
        <small>NEPSE Data Platform</small>
        <small className={`plan-badge ${planLabel === "Paid" ? "paid" : "free"}`}>{planLabel}</small>
      </div>
      <nav>
        {links.map(([path, label]) => {
          const active = location.pathname === path || (path !== "/" && location.pathname.startsWith(path));
          return (
            <Link key={path} to={path} className={active ? "active" : ""}>
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="inline-actions">
        <a className="button-link" href="/api/docs" target="_blank" rel="noreferrer">
          API Reference
        </a>
        {account ? <button className="secondary" onClick={onLogout}>Logout</button> : null}
      </div>
    </header>
  );
}

function LandingPage() {
  return (
    <Page
      title="One Domain for NEPSE Data, Product, and Payments"
      subtitle="Portfolio-grade presentation on top, production API and billing on nepsedata.sakshyambanjade.com.np."
    >
      <section className="hero-grid">
        <article className="card card-strong">
          <h2>Unified Platform</h2>
          <p>
            NepSense is no longer only a dataset repo. It is now structured as a full product surface: landing,
            pricing, docs, dashboard, billing, API keys, downloads, and platform status.
          </p>
          <div className="inline-actions">
            <Link className="button-link" to="/pricing">
              Buy Credits
            </Link>
            <Link className="button-link secondary" to="/dashboard">
              Open Dashboard
            </Link>
          </div>
        </article>
        <article className="card">
          <h2>API-First Credit Model</h2>
          <ul>
            <li>Credit packs: Rs. 50, Rs. 100, Rs. 500</li>
            <li>Khalti checkout first, eSewa supported</li>
            <li>Usage-linked credit burn and logs</li>
            <li>Key rotation and data download controls</li>
          </ul>
        </article>
      </section>

      <section className="route-map card">
        <h2>Platform Routes</h2>
        <div className="route-grid">
          <code>/</code>
          <span>Landing and public product pitch</span>
          <code>/pricing</code>
          <span>Credit pack checkout</span>
          <code>/docs</code>
          <span>Developer quickstart + API reference links</span>
          <code>/dashboard</code>
          <span>User usage and account summary</span>
          <code>/dashboard/billing</code>
          <span>Payment and credit history</span>
          <code>/dashboard/api-keys</code>
          <span>API key rotation and access control</span>
          <code>/data</code>
          <span>Coverage and download entrypoint</span>
          <code>/status</code>
          <span>API health + data update status</span>
          <code>/api/v1/...</code>
          <span>Programmatic NEPSE data endpoints</span>
        </div>
      </section>

      <section className="card">
        <h2>Founder Portfolio Context</h2>
        <p>
          The portfolio presentation remains part of the landing experience, but this domain now also handles billing,
          API access, and product operations so visitors convert to active API users.
        </p>
      </section>
    </Page>
  );
}

function PricingPage({ userId }) {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [billing, setBilling] = useState(null);

  useEffect(() => {
    apiGet("/api/v1/plans")
      .then((body) => setPlans(body.data || []))
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!userId) {
      setBilling(null);
      return;
    }
    apiGet(`/api/v1/billing/${userId}`).then((body) => setBilling(body.data)).catch(() => setBilling(null));
  }, [userId]);

  async function checkout(planId, gateway) {
    if (!userId) {
      setError("Create or login from dashboard first, then return to checkout.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const path = gateway === "khalti" ? "/api/v1/payments/khalti/initiate" : "/api/v1/payments/esewa/initiate";
      const response = await apiPost(path, {
        user_id: userId,
        plan_id: planId,
      });
      const data = response.data || {};

      if (gateway === "khalti" && data.payment_url) {
        window.location.href = data.payment_url;
        return;
      }
      if (gateway === "esewa" && data.payment_url && data.form_data) {
        submitGatewayForm(data.payment_url, data.form_data);
        return;
      }
      setError("Payment initiated, but no redirect URL was returned.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Page title="API Credit Packs" subtitle="Pay once, receive credits instantly after verification.">
      {billing ? (
        <section className="card">
          <p>
            Current plan: <strong>{billing.api_key.plan_id}</strong> | Credits: <strong>{billing.api_key.credits_remaining}</strong>
          </p>
        </section>
      ) : null}
      {error ? <p className="status-bad">{error}</p> : null}
      <section className="plans-grid">
        {plans.map((plan) => (
          <article key={plan.id} className="card">
            <h2>{plan.name}</h2>
            <p className="plan-price">Rs. {plan.amount}</p>
            <p>{plan.credits.toLocaleString()} credits</p>
            <p>{plan.valid_days} day validity</p>
            <div className="inline-actions">
              <button disabled={loading} onClick={() => checkout(plan.id, "khalti")}>Khalti</button>
              <button className="secondary" disabled={loading} onClick={() => checkout(plan.id, "esewa")}>eSewa</button>
            </div>
          </article>
        ))}
      </section>
    </Page>
  );
}

function DocsPage() {
  const endpoints = [
    "GET /health",
    "GET /api/v1/symbols",
    "GET /api/v1/prices/{symbol}",
    "GET /api/v1/download/latest.csv",
    "POST /api/v1/auth/signup",
    "POST /api/v1/payments/khalti/initiate",
    "POST /api/v1/payments/esewa/initiate",
  ];

  return (
    <Page title="API Documentation" subtitle="Start from interactive docs, then use code examples for integration.">
      <section className="card">
        <p>
          Interactive OpenAPI docs are available at <a href="/api/docs">/api/docs</a> and OpenAPI JSON at
          {" "}
          <a href="/api/openapi.json">/api/openapi.json</a>.
        </p>
        <h2>Core Endpoints</h2>
        <ul>
          {endpoints.map((endpoint) => (
            <li key={endpoint}>{endpoint}</li>
          ))}
        </ul>
      </section>
    </Page>
  );
}

function DashboardPage({ userId, setUserId, visibleApiKey, setVisibleApiKey, setSessionToken, clearSession }) {
  const [inputValue, setInputValue] = useState(userId);
  const [billing, setBilling] = useState(null);
  const [signupEmail, setSignupEmail] = useState("");
  const [signupName, setSignupName] = useState("");
  const [signupLoading, setSignupLoading] = useState(false);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setInputValue(userId);
  }, [userId]);

  useEffect(() => {
    if (!userId) {
      setBilling(null);
      return;
    }

    apiGet(`/api/v1/billing/${userId}`)
      .then((body) => {
        setBilling(body.data);
        setError("");
      })
      .catch((err) => {
        setError(err.message);
        setBilling(null);
      });
  }, [userId]);

  async function createFreeAccount() {
    setSignupLoading(true);
    setError("");
    try {
      const body = await apiPost("/api/v1/auth/signup", {
        email: signupEmail,
        name: signupName || undefined,
      });
      const createdUserId = body?.data?.user?.id;
      const createdApiKey = body?.data?.api_key?.api_key;
      const token = body?.data?.access_token || "";
      if (token) {
        setSessionToken(token);
      }
      if (createdUserId) {
        setUserId(createdUserId);
      }
      if (createdApiKey) {
        setVisibleApiKey(createdApiKey);
      }
      setSignupEmail("");
      setSignupName("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSignupLoading(false);
    }
  }

  async function loginExistingAccount() {
    setLoginLoading(true);
    setError("");
    try {
      const body = await apiPost("/api/v1/auth/login", { email: loginEmail });
      const token = body?.data?.access_token || "";
      const loginUserId = body?.data?.user?.id || "";
      if (!token || !loginUserId) {
        throw new Error("Login failed: session token not returned");
      }
      setSessionToken(token);
      setUserId(loginUserId);
      setLoginEmail("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoginLoading(false);
    }
  }

  return (
    <Page title="User Dashboard" subtitle="Track credits, usage, key status, and account activity.">
      <section className="card">
        <h2>Create Free Account</h2>
        <label htmlFor="signup-email">Email</label>
        <input
          id="signup-email"
          value={signupEmail}
          onChange={(e) => setSignupEmail(e.target.value)}
          placeholder="you@example.com"
        />
        <label htmlFor="signup-name">Name (optional)</label>
        <input
          id="signup-name"
          value={signupName}
          onChange={(e) => setSignupName(e.target.value)}
          placeholder="Sakshyam"
        />
        <div className="inline-actions">
          <button disabled={signupLoading || !signupEmail.trim()} onClick={createFreeAccount}>Create Free Account</button>
        </div>
        <p className="hint-text">Creates user + free plan key. Upgrade later by buying credits from pricing.</p>
      </section>

      <section className="card">
        <h2>Login Existing Account</h2>
        <label htmlFor="login-email">Email</label>
        <input
          id="login-email"
          value={loginEmail}
          onChange={(e) => setLoginEmail(e.target.value)}
          placeholder="you@example.com"
        />
        <div className="inline-actions">
          <button disabled={loginLoading || !loginEmail.trim()} onClick={loginExistingAccount}>Login</button>
        </div>
        <p className="hint-text">Existing users can recover dashboard access by email login.</p>
      </section>

      <section className="card">
        <label htmlFor="user-id">User ID</label>
        <input
          id="user-id"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Current authenticated user_id"
        />
        <div className="inline-actions">
          <button onClick={() => setUserId(inputValue.trim())}>Load Dashboard</button>
          <button className="secondary" onClick={clearSession}>Clear</button>
          <Link className="button-link secondary" to="/dashboard/billing">
            Billing
          </Link>
          <Link className="button-link secondary" to="/dashboard/api-keys">
            API Keys
          </Link>
        </div>
        {error ? <p className="status-bad">{error}</p> : null}
      </section>

      {visibleApiKey ? (
        <section className="card">
          <h2>Visible API Key (One-Time Sensitive)</h2>
          <pre>{visibleApiKey}</pre>
          <p className="hint-text">Store this key safely. Use it in X-API-Key for protected endpoints.</p>
        </section>
      ) : null}

      {billing ? (
        <section className="hero-grid">
          <article className="card">
            <h2>Account</h2>
            <p>{billing.user.email}</p>
            <p>Plan: {billing.api_key.plan_id}</p>
            <p>Credits: {billing.api_key.credits_remaining}</p>
          </article>
          <article className="card">
            <h2>Recent Usage</h2>
            <p>{billing.usage.length} recent requests logged</p>
            <p>{billing.payments.length} recent payment records</p>
          </article>
        </section>
      ) : null}
    </Page>
  );
}

function BillingPage({ userId }) {
  const [billing, setBilling] = useState(null);
  const [error, setError] = useState("");
  const [params] = useSearchParams();
  const gateway = params.get("gateway");
  const paymentStatus = params.get("payment_status");

  useEffect(() => {
    if (!userId) return;
    apiGet(`/api/v1/billing/${userId}`)
      .then((body) => setBilling(body.data))
      .catch((err) => setError(err.message));
  }, [userId]);

  if (!userId) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Page title="Billing" subtitle="Payments, credits, and usage history.">
      {gateway ? <p className={paymentStatus === "success" ? "status-good" : "status-bad"}>Payment gateway: {gateway} | status: {paymentStatus || "unknown"}</p> : null}
      {error ? <p className="status-bad">{error}</p> : null}
      <section className="card">
        <h2>Payments</h2>
        <ul>
          {(billing?.payments || []).map((payment) => (
            <li key={payment.id}>
              {payment.gateway} | Rs. {payment.amount} | {payment.credits} credits | {payment.status}
            </li>
          ))}
        </ul>
      </section>
      <section className="card">
        <h2>Usage</h2>
        <ul>
          {(billing?.usage || []).map((entry, index) => (
            <li key={`${entry.endpoint}-${index}`}>
              {entry.endpoint} | {entry.credits_used} credits
            </li>
          ))}
        </ul>
      </section>
    </Page>
  );
}

function ApiKeysPage({ userId }) {
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  async function rotate() {
    setError("");
    setResult("");
    try {
      const response = await apiPost("/api/v1/api-keys/rotate", { user_id: userId });
      setResult(response.data.api_key || "Key rotated. API key visible once in response.");
    } catch (err) {
      setError(err.message);
    }
  }

  if (!userId) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Page title="API Key Management" subtitle="Rotate keys and keep production integrations secure.">
      {error ? <p className="status-bad">{error}</p> : null}
      {result ? <p className="status-good">{result}</p> : null}
      <section className="card">
        <p>Current dashboard user: {userId}</p>
        <button onClick={rotate}>Rotate Active Key</button>
      </section>
    </Page>
  );
}

function DataPage() {
  const [coverage, setCoverage] = useState(null);
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([apiGet("/api/v1/coverage"), apiGet("/api/v1/metadata")])
      .then(([coverageResp, metaResp]) => {
        setCoverage(coverageResp.data || coverageResp);
        setMeta(metaResp.data || metaResp);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Page title="Dataset Coverage and Downloads" subtitle="Discover symbol coverage and pull files directly.">
      {error ? <p className="status-bad">{error}</p> : null}
      <section className="card">
        <h2>Downloads</h2>
        <ul>
          <li><a href="/api/v1/download/latest.csv">Latest CSV</a></li>
          <li><a href="/api/v1/download/latest.parquet">Latest Parquet (credit-gated)</a></li>
        </ul>
      </section>
      <section className="hero-grid">
        <article className="card">
          <h2>Coverage</h2>
          <pre>{JSON.stringify(coverage, null, 2)}</pre>
        </article>
        <article className="card">
          <h2>Manifest</h2>
          <pre>{JSON.stringify(meta, null, 2)}</pre>
        </article>
      </section>
    </Page>
  );
}

function StatusPage() {
  const [health, setHealth] = useState(null);
  const [platform, setPlatform] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([apiGet("/health"), apiGet("/api/v1/platform/status")])
      .then(([healthResp, platformResp]) => {
        setHealth(healthResp);
        setPlatform(platformResp.data || platformResp);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Page title="Platform Status" subtitle="Operational heartbeat for API and data update workflows.">
      {error ? <p className="status-bad">{error}</p> : null}
      <section className="hero-grid">
        <article className="card">
          <h2>API Health</h2>
          <pre>{JSON.stringify(health, null, 2)}</pre>
        </article>
        <article className="card">
          <h2>Data/Admin Status</h2>
          <pre>{JSON.stringify(platform, null, 2)}</pre>
        </article>
      </section>
    </Page>
  );
}

function BillingSuccessPage({ setUserId }) {
  const [params] = useSearchParams();
  const userId = params.get("user_id");
  const gateway = params.get("gateway");

  useEffect(() => {
    if (userId) {
      setUserId(userId);
    }
  }, [setUserId, userId]);

  return (
    <Page title="Payment Successful" subtitle="Credits have been applied to your account.">
      <section className="card">
        <p className="status-good">Gateway: {gateway || "unknown"}</p>
        <p>Your account is now ready with updated credits.</p>
        <div className="inline-actions">
          <Link className="button-link" to={`/dashboard/billing?payment_status=success&gateway=${gateway || ""}`}>Open Billing</Link>
          <Link className="button-link secondary" to="/pricing">Back to Pricing</Link>
        </div>
      </section>
    </Page>
  );
}

function BillingFailedPage() {
  const [params] = useSearchParams();
  const gateway = params.get("gateway");
  const status = params.get("status");

  return (
    <Page title="Payment Not Completed" subtitle="No credits were added yet.">
      <section className="card">
        <p className="status-bad">Gateway: {gateway || "unknown"} | Status: {status || "unknown"}</p>
        <div className="inline-actions">
          <Link className="button-link" to="/pricing">Try Again</Link>
          <Link className="button-link secondary" to={`/dashboard/billing?payment_status=failed&gateway=${gateway || ""}`}>Open Billing</Link>
        </div>
      </section>
    </Page>
  );
}

function App() {
  const [userId, setUserId] = useUserId();
  const [visibleApiKey, setVisibleApiKey] = useVisibleApiKey();
  const [sessionToken, setSessionToken] = useSessionToken();
  const [account, setAccount] = useState(null);

  useEffect(() => {
    if (!userId || !sessionToken) {
      setAccount(null);
      return;
    }
    apiGet(`/api/v1/billing/${userId}`).then((body) => setAccount(body.data || null)).catch(() => setAccount(null));
  }, [userId, sessionToken]);

  function clearSession() {
    setUserId("");
    setSessionToken("");
    setVisibleApiKey("");
  }

  const routeContext = useMemo(
    () => ({ userId, setUserId, visibleApiKey, setVisibleApiKey, setSessionToken, clearSession }),
    [userId, visibleApiKey, setSessionToken, clearSession],
  );

  return (
    <div>
      <TopNav account={account} onLogout={clearSession} />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/pricing" element={<PricingPage userId={routeContext.userId} />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route
          path="/dashboard"
          element={<DashboardPage userId={routeContext.userId} setUserId={routeContext.setUserId} visibleApiKey={routeContext.visibleApiKey} setVisibleApiKey={routeContext.setVisibleApiKey} setSessionToken={routeContext.setSessionToken} clearSession={routeContext.clearSession} />}
        />
        <Route path="/dashboard/billing" element={<BillingPage userId={routeContext.userId} />} />
        <Route path="/dashboard/api-keys" element={<ApiKeysPage userId={routeContext.userId} />} />
        <Route path="/billing/success" element={<BillingSuccessPage setUserId={routeContext.setUserId} />} />
        <Route path="/billing/failed" element={<BillingFailedPage />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
