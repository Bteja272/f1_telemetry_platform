import { useEffect, useState } from "react";
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

const WS_URL = "ws://127.0.0.1:8000/ws/telemetry/1";
const METRICS_URL = "http://127.0.0.1:8000/metrics/system";

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

function App() {
  const [telemetry, setTelemetry] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [connected, setConnected] = useState(false);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (!data || data.message) {
        return;
      }

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
    };

    socket.onclose = () => {
      setConnected(false);
    };

    socket.onerror = () => {
      setConnected(false);
    };

    return () => {
      socket.close();
    };
  }, []);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(METRICS_URL);
        const data = await response.json();
        setMetrics(data);
      } catch (error) {
        console.error("Failed to fetch metrics", error);
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

      <section className="driver-panel">
        <div>
          <p className="label">Driver</p>
          <h2>#{telemetry?.driver_number ?? 1}</h2>
        </div>

        <div>
          <p className="label">Session</p>
          <h2>{telemetry?.session_key ?? "--"}</h2>
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
            <h2>Speed Trace</h2>
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
    </main>
  );
}

export default App;