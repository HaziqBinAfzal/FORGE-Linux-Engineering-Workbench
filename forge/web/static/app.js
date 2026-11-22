const $ = id => document.getElementById(id);
const bytes = value => (value / 1073741824).toFixed(1) + " GB";
const percent = value => Number(value).toFixed(1) + "%";
const safe = value => String(value ?? "—");

function metric(id, value) {
  $(id).textContent = percent(value);
  $(id + "-bar").style.width = Math.max(0, Math.min(100, value)) + "%";
}

async function refresh() {
  try {
    const [systemResponse, processResponse] = await Promise.all([
      fetch("/api/system", {cache:"no-store"}),
      fetch("/api/processes", {cache:"no-store"})
    ]);
    if (!systemResponse.ok || !processResponse.ok) throw new Error("API unavailable");
    const s = await systemResponse.json();
    const p = await processResponse.json();

    metric("cpu", s.cpu.usage_percent);
    metric("memory", s.memory.usage_percent);
    metric("disk", s.disk.usage_percent);
    $("cores").textContent = safe(s.cpu.logical_cores) + " logical cores";
    $("memory-detail").textContent = bytes(s.memory.used_bytes) + " / " + bytes(s.memory.total_bytes);
    $("disk-detail").textContent = bytes(s.disk.used_bytes) + " / " + bytes(s.disk.total_bytes);
    $("hostname").textContent = safe(s.hostname);
    $("platform").textContent = safe(s.platform);
    $("kernel").textContent = safe(s.kernel);
    $("uptime").textContent = Math.floor(s.uptime_seconds / 3600) + " hours";
    $("process-count").textContent = safe(s.process_count);

    const tbody = $("process-table");
    tbody.replaceChildren();
    for (const process of p.processes) {
      const tr = document.createElement("tr");
      for (const value of [
        process.name, process.pid,
        percent(process.cpu_percent),
        percent(process.memory_percent)
      ]) {
        const td = document.createElement("td");
        td.textContent = safe(value);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    if (!p.processes.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 4;
      td.textContent = "No processes available";
      tr.appendChild(td);
      tbody.appendChild(tr);
    }

    $("connection").textContent = "● SYSTEM CONNECTED";
    $("updated").textContent = "Updated " + new Date().toLocaleTimeString();
  } catch (error) {
    $("connection").textContent = "● CONNECTION UNAVAILABLE";
    $("updated").textContent = "Telemetry refresh failed";
  }
}
refresh();
setInterval(refresh, 5000);
