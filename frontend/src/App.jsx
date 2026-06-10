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

  return `${session.location || "Unknown Location"} · ${
    session.circuit_short_name || "Unknown Circuit"
  } · ${date}`;
}

function RaceMap({
  trackMapPoints,
  selectedDriverLocations,
  latestDriverLocations,
  drivers,
  selectedDriver,
  isReplaying,
  setIsReplaying,
  replayIndex,
  setReplayIndex,
  replaySpeed,
  setReplaySpeed,
}) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const selectedDriverData = useMemo(() => {
    return drivers.find(
      (driver) => Number(driver.driver_number) === Number(selectedDriver)
    );
  }, [drivers, selectedDriver]);

  const replayPoint = useMemo(() => {
    if (!selectedDriverLocations.length) return null;

    const safeIndex = Math.min(
      replayIndex,
      selectedDriverLocations.length - 1
    );

    return selectedDriverLocations[safeIndex];
  }, [selectedDriverLocations, replayIndex]);

  const bounds = useMemo(() => {
    if (!trackMapPoints.length) return null;

    const xs = trackMapPoints.map((point) => point.x);
    const ys = trackMapPoints.map((point) => point.y);

    return {
      minX: Math.min(...xs),
      maxX: Math.max(...xs),
      minY: Math.min(...ys),
      maxY: Math.max(...ys),
    };
  }, [trackMapPoints]);

  useEffect(() => {
    if (!isReplaying || selectedDriverLocations.length === 0) return;

    const interval = setInterval(() => {
      setReplayIndex((previousIndex) => {
        const nextIndex = previousIndex + 1;

        if (nextIndex >= selectedDriverLocations.length) {
          setIsReplaying(false);
          return selectedDriverLocations.length - 1;
        }

        return nextIndex;
      });
    }, 250 / replaySpeed);

    return () => clearInterval(interval);
  }, [
    isReplaying,
    replaySpeed,
    selectedDriverLocations.length,
    setIsReplaying,
    setReplayIndex,
  ]);

  const getDriver = (driverNumber) => {
    return drivers.find(
      (driver) => Number(driver.driver_number) === Number(driverNumber)
    );
  };

  const getTeamColor = (driver) => {
    return driver?.team_colour
      ? `#${driver.team_colour.replace("#", "")}`
      : "#e5e7eb";
  };

  const scalePoint = (point) => {
    if (!bounds) return { cx: 0, cy: 0 };

    const width = 900;
    const height = 420;
    const padding = 40;

    const xRange = bounds.maxX - bounds.minX || 1;
    const yRange = bounds.maxY - bounds.minY || 1;

    return {
      cx:
        padding +
        ((point.x - bounds.minX) / xRange) * (width - padding * 2),
      cy:
        padding +
        ((bounds.maxY - point.y) / yRange) * (height - padding * 2),
    };
  };

  const trackMapPolyline = useMemo(() => {
    if (trackMapPoints.length < 2 || !bounds) return "";

    return trackMapPoints
      .map((point) => {
        const { cx, cy } = scalePoint(point);
        return `${cx},${cy}`;
      })
      .join(" ");
  }, [trackMapPoints, bounds]);

  return (
    <section className="chart-card">
      <div className="chart-header">
        <div>
          <p className="label">Race Map</p>
          <h2>Track Map</h2>
        </div>
        <p className="chart-note">Replay selected driver around the circuit</p>
      </div>

      <div className="replay-controls">
        <button
          type="button"
          onClick={() => setIsReplaying((current) => !current)}
          disabled={selectedDriverLocations.length === 0}
        >
          {isReplaying ? "Pause" : "Play"}
        </button>

        <button
          type="button"
          onClick={() => {
            setIsReplaying(false);
            setReplayIndex(0);
          }}
          disabled={selectedDriverLocations.length === 0}
        >
          Reset
        </button>

        <select
          value={replaySpeed}
          onChange={(event) => setReplaySpeed(Number(event.target.value))}
        >
          <option value={1}>1x</option>
          <option value={2}>2x</option>
          <option value={4}>4x</option>
        </select>

        <input
          type="range"
          min="0"
          max={Math.max(selectedDriverLocations.length - 1, 0)}
          value={replayIndex}
          onChange={(event) => {
            setIsReplaying(false);
            setReplayIndex(Number(event.target.value));
          }}
          disabled={selectedDriverLocations.length === 0}
        />

        <span className="replay-status">
          {selectedDriverLocations.length > 0
            ? `${replayIndex + 1} / ${selectedDriverLocations.length}`
            : "No replay data"}
        </span>
      </div>

      <div className="race-map-container">
        {trackMapPoints.length === 0 ? (
          <p className="driver-meta">No track map available yet.</p>
        ) : (
          <svg viewBox="0 0 900 420" className="race-map-svg">
            <rect x="0" y="0" width="900" height="420" rx="18" />

            {trackMapPolyline && (
              <>
                <polyline points={trackMapPolyline} className="track-outline" />
                <polyline points={trackMapPolyline} className="track-surface" />
                <polyline
                  points={trackMapPolyline}
                  className="track-centerline"
                />
              </>
            )}

            {latestDriverLocations
              .filter(
                (point) =>
                  String(point.driver_number) !== String(selectedDriver)
              )
              .map((point) => {
                const driver = getDriver(point.driver_number);
                const { cx, cy } = scalePoint(point);

                return (
                  <g
                    key={point.driver_number}
                    onMouseEnter={() => setHoveredPoint(point)}
                    onMouseLeave={() => setHoveredPoint(null)}
                  >
                    <circle
                      cx={cx}
                      cy={cy}
                      r="9"
                      className="driver-dot"
                      style={{
                        fill: getTeamColor(driver),
                        stroke: "#020617",
                      }}
                    />

                    <text x={cx + 12} y={cy + 4} className="driver-dot-label">
                      {driver?.name_acronym || point.driver_number}
                    </text>
                  </g>
                );
              })}

            {replayPoint && (
              <g
                onMouseEnter={() => setHoveredPoint(replayPoint)}
                onMouseLeave={() => setHoveredPoint(null)}
              >
                <circle
                  cx={scalePoint(replayPoint).cx}
                  cy={scalePoint(replayPoint).cy}
                  r="14"
                  className="driver-dot selected"
                  style={{
                    fill: getTeamColor(selectedDriverData),
                    stroke: "#ffffff",
                  }}
                />

                <text
                  x={scalePoint(replayPoint).cx + 15}
                  y={scalePoint(replayPoint).cy + 5}
                  className="driver-dot-label"
                >
                  {selectedDriverData?.name_acronym || selectedDriver}
                </text>
              </g>
            )}
          </svg>
        )}

        {hoveredPoint && (
          <div className="map-tooltip">
            <strong>
              {getDriver(hoveredPoint.driver_number)?.name_acronym ||
                selectedDriverData?.name_acronym ||
                `Driver ${hoveredPoint.driver_number}`}
            </strong>
            <span>
              {getDriver(hoveredPoint.driver_number)?.full_name ||
                selectedDriverData?.full_name}
            </span>
            <span>
              {getDriver(hoveredPoint.driver_number)?.team_name ||
                selectedDriverData?.team_name}
            </span>
            <span>X: {hoveredPoint.x}</span>
            <span>Y: {hoveredPoint.y}</span>
            <span>{hoveredPoint.event_time}</span>
          </div>
        )}
      </div>
    </section>
  );
} 

function App() {
  const [sessions, setSessions] = useState([]);
  const [years, setYears] = useState([]);
  const [selectedYear, setSelectedYear] = useState("");
  const [drivers, setDrivers] = useState([]);
  const [selectedSession, setSelectedSession] = useState("");
  const [selectedDriver, setSelectedDriver] = useState("");
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayIndex, setReplayIndex] = useState(0);
  const [replaySpeed, setReplaySpeed] = useState(1);

  const [telemetry, setTelemetry] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [trackMapData, setTrackMapData] = useState([]);
  const [selectedDriverLocationData, setSelectedDriverLocationData] =
    useState([]);
  const [latestDriverLocations, setLatestDriverLocations] = useState([]);
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
    const fetchYears = async () => {
      try {
        const response = await fetch(`${API_BASE}/years`);

        if (!response.ok) {
          throw new Error("Failed to fetch years");
        }

        const data = await response.json();

        setYears(data.years || []);

        if (data.years?.length > 0) {
          setSelectedYear(String(data.years[0]));
        }
      } catch (error) {
        console.error("Failed to fetch years:", error);
      }
    };

    fetchYears();
  }, []);

  useEffect(() => {
    if (!selectedYear) return;

    const fetchSessionsByYear = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/years/${selectedYear}/sessions`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch sessions");
        }

        const data = await response.json();

        setSessions(data.sessions || []);

        if (data.sessions?.length > 0) {
          setSelectedSession(
            String(data.sessions[0].session_key)
          );
        }
      } catch (error) {
        console.error("Failed to fetch sessions:", error);
      }
    };

    fetchSessionsByYear();
  }, [selectedYear]);

  useEffect(() => {
    if (!selectedSession) return;

    const fetchDrivers = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/sessions/${selectedSession}/drivers`
        );
        if (!response.ok) throw new Error("Failed to fetch drivers");

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

    const fetchTrackMap = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/sessions/${selectedSession}/track-map`
        );
        if (!response.ok) throw new Error("Failed to fetch track map");

        const data = await response.json();
        setTrackMapData(data.points || []);
      } catch (error) {
        console.error("Failed to fetch track map:", error);
      }
    };

    const fetchLatestDriverLocations = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/sessions/${selectedSession}/openf1-latest-locations`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch latest driver locations");
        }

        const data = await response.json();

        console.log(
          "Latest driver locations:",
          data.count,
          data.locations
        );

        setLatestDriverLocations(data.locations || []);
      } catch (error) {
        console.error(
          "Failed to fetch latest driver locations:",
          error
        );
      }
    };

    fetchDrivers();
    fetchTrackMap();
    fetchLatestDriverLocations();
  }, [selectedSession]);

  useEffect(() => {
    if (!selectedSession || !selectedDriver) return;

    const fetchHistory = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/sessions/${selectedSession}/drivers/${selectedDriver}/history?limit=30`
        );
        if (!response.ok) throw new Error("Failed to fetch driver history");

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

    const fetchSelectedDriverLocations = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/sessions/${selectedSession}/drivers/${selectedDriver}/openf1-locations?limit=10000`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch selected driver locations");
        }

        const data = await response.json();
        setSelectedDriverLocationData(data.locations || []);
      } catch (error) {
        console.error("Failed to fetch selected driver locations:", error);
      }
    };

    fetchHistory();
    fetchSelectedDriverLocations();
  }, [selectedSession, selectedDriver]);

  useEffect(() => {
    if (!selectedDriver) return;

    setTelemetry(null);
    setChartData([]);
    setConnected(false);

    const socket = new WebSocket(`${WS_BASE}/ws/telemetry/${selectedDriver}`);

    socket.onopen = () => setConnected(true);

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

    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);

    return () => socket.close();
  }, [selectedDriver]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_BASE}/metrics/system`);
        if (!response.ok) throw new Error("Failed to fetch metrics");

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
          <p className="label">Season</p>

          <select
            value={selectedYear}
            onChange={(event) => {
              setSelectedYear(event.target.value);

              setSelectedSession("");
              setSelectedDriver("");

              setDrivers([]);
              setTrackMapData([]);
              setLatestDriverLocations([]);
              setSelectedDriverLocationData([]);
            }}
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
        <div>
          <p className="label">Race</p>
          <select
            value={selectedSession}
            onChange={(event) => {
              setSelectedSession(event.target.value);
              setSelectedDriver("");
              setTelemetry(null);
              setChartData([]);
              setHistoryData([]);
              setTrackMapData([]);
              setSelectedDriverLocationData([]);
              setLatestDriverLocations([]);
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
              setSelectedDriverLocationData([]);
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

      <RaceMap
        trackMapPoints={trackMapData}
        selectedDriverLocations={selectedDriverLocationData}
        latestDriverLocations={latestDriverLocations}
        drivers={drivers}
        selectedDriver={selectedDriver}
        isReplaying={isReplaying}
        setIsReplaying={setIsReplaying}
        replayIndex={replayIndex}
        setReplayIndex={setReplayIndex}
        replaySpeed={replaySpeed}
        setReplaySpeed={setReplaySpeed}
      />

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