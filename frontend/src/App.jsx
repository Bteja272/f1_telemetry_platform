import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import "./index.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const WS_BASE =
  import.meta.env.VITE_WS_BASE_URL || "ws://127.0.0.1:8000";

function MetricCard({ title, value, unit }) {
  return (
    <div className="metric-card">
      <p className="metric-title">{title}</p>
      <h2>
        {value ?? "--"} <span>{unit}</span>
      </h2>
    </div>
  );
}

function formatSessionLabel(session) {
  if (!session) return "Select Session";

  const date = session.date_start
    ? new Date(session.date_start).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "Date unavailable";

  const location = session.location || "Unknown Location";
  const circuit = session.circuit_short_name || "Unknown Circuit";

  return `${location} · ${circuit} · ${date}`;
}

function App() {
  const [sessions, setSessions] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [selectedSession, setSelectedSession] = useState("");
  const [selectedDriver, setSelectedDriver] = useState("");

  const [telemetry, setTelemetry] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [connected, setConnected] = useState(false);
  const [metrics, setMetrics] = useState(null);

  const selectedSessionData = useMemo(() => {
    return sessions.find(
      (session) => String(session.session_key) === String(selectedSession)
    );
  }, [sessions, selectedSession]);

  const selectedDriverData = useMemo(() => {
    return drivers.find(
      (driver) => String(driver.driver_number) === String(selectedDriver)
    );
  }, [drivers, selectedDriver]);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await fetch(`${API_BASE}/sessions`);

        if (!response.ok) {
          throw new Error("Failed to fetch sessions");
        }

        const data = await response.json();
        const availableSessions = data.sessions || [];

        setSessions(availableSessions);

        if (availableSessions.length > 0) {
          setSelectedSession(String(availableSessions[0].session_key));
        }
      } catch (error) {
        console.error("Failed to fetch sessions:", error);
      }
    };

    fetchSessions();
  }, []);

  useEffect(() => {
    if (!selectedSession) return;

    const fetchDrivers = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/sessions/${selectedSession}/drivers`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch drivers");
        }

        const data = await response.json();
        const availableDrivers = data.drivers || [];

        setDrivers(availableDrivers);

        if (availableDrivers.length > 0) {
          setSelectedDriver(String(availableDrivers[0].driver_number));
        }
      } catch (error) {
        console.error("Failed to fetch drivers:", error);
      }
    };

    fetchDrivers();
  }, [selectedSession]);

  useEffect(() => {
    if (!selectedSession || !selectedDriver) return;

    const fetchHistory = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/sessions/${selectedSession}/drivers/${selectedDriver}/history?limit=30`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch driver history");
        }

        const data = await response.json();

        const formattedHistory = [...(data.telemetry || [])]
          .reverse()
          .map((event) => ({
            time: new Date(event.event_time).toLocaleTimeString(),
            speed: event.speed,
            rpm: event.rpm,
            throttle: event.throttle,
            brake: event.brake,
          }));

        setHistoryData(formattedHistory);
      } catch (error) {
        console.error("Failed to fetch history:", error);
      }
    };

    fetchHistory();
  }, [selectedSession, selectedDriver]);

  useEffect(() => {
    if (!selectedDriver) return;

    setTelemetry(null);
    setChartData([]);
    setConnected(false);

    const socket = new WebSocket(`${WS_BASE}/ws/telemetry/${selectedDriver}`);

    socket.onopen = () => {
      console.log("WebSocket connected");
      setConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (!data || data.message) return;

        setTelemetry(data);

        setChartData((prev) => {
          const next = [
            ...prev,
            {
              time: new Date().toLocaleTimeString(),
              speed: data.speed,
              rpm: data.rpm,
              throttle: data.throttle,
              brake: data.brake,
            },
          ];

          return next.slice(-30);
        });
      } catch (error) {
        console.error("WebSocket parse error:", error);
      }
    };

    socket.onclose = () => {
      console.log("WebSocket disconnected");
      setConnected(false);
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnected(false);
    };

    return () => {
      socket.close();
    };
  }, [selectedDriver]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_BASE}/metrics/system`);

        if (!response.ok) {
          throw new Error("Failed to fetch metrics");
        }

        const data = await response.json();
        setMetrics(data);
      } catch (error) {
        console.error("Failed to fetch metrics:", error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <main className="dashboard">
      <section className="header">
        <div>
          <p className="eyebrow">F1 Telemetry Platform</p>
          <h1>Real-Time Driver Telemetry</h1>
          <p className="subtitle">
            Streaming Formula 1 telemetry through Kafka, Redis, FastAPI
            WebSockets, and TimescaleDB.
          </p>
        </div>

        <div className={connected ? "status online" : "status offline"}>
          {connected ? "WebSocket Connected" : "Disconnected"}
        </div>
      </section>

      <section className="control-panel">
        <div>
          <p className="label">Race / Session</p>
          <select
            value={selectedSession}
            onChange={(event) => {
              setSelectedSession(event.target.value);
              setSelectedDriver("");
              setTelemetry(null);
              setChartData([]);
              setHistoryData([]);
            }}
          >
            {sessions.map((session) => (
              <option key={session.session_key} value={session.session_key}>
                {formatSessionLabel(session)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <p className="label">Driver</p>
          <select
            value={selectedDriver}
            onChange={(event) => {
              setSelectedDriver(event.target.value);
              setTelemetry(null);
              setChartData([]);
            }}
          >
            {drivers.map((driver) => (
              <option key={driver.driver_number} value={driver.driver_number}>
                {driver.name_acronym || "DRV"} · {driver.full_name} ·{" "}
                {driver.team_name}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="driver-profile-card">
        <div className="driver-image-wrapper">
          {selectedDriverData?.headshot_url ? (
            <img
              src={selectedDriverData.headshot_url}
              alt={selectedDriverData.full_name || "Driver headshot"}
              className="driver-headshot"
            />
          ) : (
            <div className="driver-placeholder">
              {selectedDriverData?.name_acronym || "DRV"}
            </div>
          )}
        </div>

        <div>
          <p className="label">Selected Driver</p>
          <h2>
            {selectedDriverData?.name_acronym || "DRV"} ·{" "}
            {selectedDriverData?.full_name || `Driver #${selectedDriver}`}
          </h2>
          <p className="driver-meta">
            {selectedDriverData?.team_name || "Team unavailable"}
          </p>
        </div>

        <div>
          <p className="label">Selected Race</p>
          <h2>{selectedSessionData?.location || "Race unavailable"}</h2>
          <p className="driver-meta">
            {selectedSessionData?.circuit_short_name || "Circuit unavailable"} ·{" "}
            {selectedSessionData?.country_name || "Country unavailable"}
          </p>
        </div>
      </section>

      <section className="driver-panel">
        <div>
          <p className="label">Driver</p>
          <h2>
            {selectedDriverData?.name_acronym
              ? `${selectedDriverData.name_acronym} #${selectedDriver}`
              : `#${telemetry?.driver_number ?? selectedDriver ?? "--"}`}
          </h2>
        </div>

        <div>
          <p className="label">Session</p>
          <h2>{telemetry?.session_key ?? selectedSession ?? "--"}</h2>
        </div>

        <div>
          <p className="label">Last Event</p>
          <h2 className="small-text">{telemetry?.event_time ?? "--"}</h2>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard title="Speed" value={telemetry?.speed} unit="km/h" />
        <MetricCard title="RPM" value={telemetry?.rpm} unit="" />
        <MetricCard title="Gear" value={telemetry?.gear} unit="" />
        <MetricCard title="Throttle" value={telemetry?.throttle} unit="%" />
        <MetricCard title="Brake" value={telemetry?.brake} unit="%" />
        <MetricCard title="DRS" value={telemetry?.drs} unit="" />
      </section>

      <section className="metrics-grid">
        <MetricCard
          title="Total Events"
          value={metrics?.total_telemetry_events}
          unit=""
        />
        <MetricCard
          title="Active Drivers"
          value={metrics?.active_cached_drivers}
          unit=""
        />
        <MetricCard
          title="DB Latency"
          value={metrics?.timescaledb_query_latency_ms}
          unit="ms"
        />
        <MetricCard
          title="Redis Latency"
          value={metrics?.redis_query_latency_ms}
          unit="ms"
        />
      </section>

      <section className="chart-card">
        <div className="chart-header">
          <div>
            <p className="label">Live Chart</p>
            <h2>Live Speed Trace</h2>
          </div>
          <p className="chart-note">Last 30 WebSocket updates</p>
        </div>

        <div className="chart-container">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="speed"
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="chart-card">
        <div className="chart-header">
          <div>
            <p className="label">Historical Chart</p>
            <h2>Session History Speed Trace</h2>
          </div>
          <p className="chart-note">Latest 30 stored events</p>
        </div>

        <div className="chart-container">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={historyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="speed"
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </main>
  );
}

export default App;