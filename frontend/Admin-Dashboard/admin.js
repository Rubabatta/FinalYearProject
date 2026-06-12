const API_URL = "https://acceptable-solace-production-06f3.up.railway.app";
const ONLINE_THRESHOLD_SECONDS = 60;
let adminMap;
let adminMarkers = {};
let stopsCache = {};
const busStatusMap = {};

function setSidebarState(collapsed) {
    document.body.classList.toggle("sidebar-collapsed", collapsed);
    document.documentElement.style.setProperty('--sidebar-offset', collapsed ? '0px' : '210px');
    setTimeout(() => {
        if (adminMap) adminMap.invalidateSize();
    }, 260);
}

function initAdminMap() {
    if (adminMap || typeof L === "undefined") return;
    adminMap = L.map('adminMap').setView([30.1575, 71.5249], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(adminMap);
    setTimeout(() => adminMap.invalidateSize(), 150);
}

function parseTimestamp(timestamp) {
    if (!timestamp) return NaN;
    const match = timestamp.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})$/);
    if (match) {
        const year = parseInt(match[1], 10);
        const month = parseInt(match[2], 10) - 1;
        const day = parseInt(match[3], 10);
        const hour = parseInt(match[4], 10);
        const minute = parseInt(match[5], 10);
        const second = parseInt(match[6], 10);
        return Date.UTC(year, month, day, hour, minute, second);
    }
    let parsed = Date.parse(timestamp);
    if (isNaN(parsed)) {
        parsed = Date.parse(timestamp.replace(' ', 'T') + 'Z');
    }
    return parsed;
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function formatAge(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return "--";
    if (seconds < 60) return `${Math.floor(seconds)} sec`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min`;
    return `${Math.floor(seconds / 3600)} hr ${Math.floor((seconds % 3600) / 60)} min`;
}

function getStatusLabel(status) {
    if (status === "ONLINE") return "Active";
    if (status === "STOPPED") return "At Stop";
    if (status === "DISCONNECTED") return "Disconnected";
    return "Offline";
}

function getLatestLocations(locations) {
    const latest = {};
    locations.forEach(item => {
        const id = item.bus_id;
        const time = parseTimestamp(item.last_updated);
        if (!id || isNaN(time)) return;
        if (!latest[id] || time > latest[id].time) {
            latest[id] = { data: item, time };
        }
    });
    return latest;
}

function fetchStops(routeId) {
    if (!routeId) return Promise.resolve([]);
    if (!stopsCache[routeId]) {
        stopsCache[routeId] = fetch(`${API_URL}/get_stops/${routeId}`)
            .then(res => res.json())
            .then(stops => Array.isArray(stops) ? stops : [])
            .catch(() => []);
    }
    return stopsCache[routeId];
}

function findStopInfo(stops, lat, lng) {
    let nearest = null;
    let nearestIndex = -1;
    const validStops = stops
        .slice()
        .sort((a, b) => (Number(a.stop_order) || 0) - (Number(b.stop_order) || 0))
        .filter(stop => Number.isFinite(Number(stop.latitude)) && Number.isFinite(Number(stop.longitude)));

    validStops.forEach((stop, index) => {
        const distance = calculateDistance(lat, lng, Number(stop.latitude), Number(stop.longitude));
        if (!nearest || distance < nearest.distance) {
            nearest = { ...stop, distance };
            nearestIndex = index;
        }
    });

    const nextStop = nearestIndex >= 0 && nearestIndex < validStops.length - 1 ? validStops[nearestIndex + 1] : null;
    return {
        currentStop: nearest,
        nextStop,
        isStopped: !!nearest && nearest.distance <= 0.12
    };
}

function markerIcon(status) {
    const color = status === "ONLINE" ? "#16a34a" : status === "STOPPED" ? "#2563eb" : status === "DISCONNECTED" ? "#f59e0b" : "#ef4444";
    return L.divIcon({
        className: "",
        html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 4px 12px rgba(15,23,42,0.35);"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
}

function renderMarker(item) {
    if (!adminMap || !Number.isFinite(item.lat) || !Number.isFinite(item.lng)) return;
    const popup = `${item.busNumber}<br>${getStatusLabel(item.status)}<br>${item.currentStop || "No stop data"}`;
    if (adminMarkers[item.id]) {
        adminMarkers[item.id].setLatLng([item.lat, item.lng]).setIcon(markerIcon(item.status)).bindPopup(popup);
    } else {
        adminMarkers[item.id] = L.marker([item.lat, item.lng], { icon: markerIcon(item.status) })
            .addTo(adminMap)
            .bindPopup(popup);
    }
}

function renderMonitor(items) {
    const list = document.getElementById("busMonitorList");
    if (!list) return;

    if (items.length === 0) {
        list.innerHTML = '<div class="empty-state">No buses found.</div>';
        return;
    }

    list.innerHTML = "";
    items
        .sort((a, b) => a.statusOrder - b.statusOrder || String(a.busNumber).localeCompare(String(b.busNumber)))
        .forEach(item => {
            const div = document.createElement("div");
            const cssStatus = item.status === "ONLINE" ? "online" : item.status === "STOPPED" ? "stopped" : item.status === "DISCONNECTED" ? "disconnected" : "offline";
            div.className = `bus-status-item bus-${cssStatus}`;
            div.innerHTML = `
                <div class="bus-status-top">
                    <div class="bus-name"><i class="fa-solid fa-bus"></i> ${item.busNumber}</div>
                    <span class="status-badge status-${cssStatus}">${getStatusLabel(item.status)}</span>
                </div>
                <div class="bus-meta">${item.ageLabel}: ${item.ageText}</div>
                <div class="bus-meta">Current: ${item.currentStop || "-"}</div>
                <div class="bus-meta">Next: ${item.nextStop || "-"}</div>
            `;
            div.onclick = () => {
                if (adminMap && Number.isFinite(item.lat) && Number.isFinite(item.lng)) {
                    adminMap.setView([item.lat, item.lng], 16);
                    if (adminMarkers[item.id]) adminMarkers[item.id].openPopup();
                }
            };
            list.appendChild(div);
        });
}

function updateMonitorCounts(items) {
    const active = items.filter(item => item.status === "ONLINE" || item.status === "STOPPED").length;
    const offline = items.filter(item => item.status === "OFFLINE").length;
    const disconnected = items.filter(item => item.status === "DISCONNECTED").length;
    const stopped = items.filter(item => item.status === "STOPPED").length;

    document.getElementById("monitorActive").innerText = active;
    document.getElementById("monitorOffline").innerText = offline;
    document.getElementById("monitorDisconnected").innerText = disconnected;
    document.getElementById("monitorStopped").innerText = stopped;
    document.getElementById("activeBuses").innerText = active;
    document.getElementById("mapStatus").innerText = `${items.length} buses tracked`;
    document.getElementById("monitorUpdated").innerText = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function showToast(message) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `<div class="toast-close"><strong>🚍 Bus Alert</strong><button aria-label="Close">×</button></div><small>${message}</small>`;

    const closeButton = toast.querySelector("button");
    closeButton.addEventListener("click", () => {
        toast.classList.add("hide");
        setTimeout(() => toast.remove(), 350);
    });

    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add("hide");
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 350);
    }, 4500);
}

async function checkBusStatus() {
    initAdminMap();
    try {
        const [buses, locations] = await Promise.all([
            fetch(`${API_URL}/get_buses`).then(res => res.json()),
            fetch(`${API_URL}/get_all_locations`).then(res => res.json()).catch(() => [])
        ]);

        const latest = getLatestLocations(Array.isArray(locations) ? locations : []);
        const items = await Promise.all((Array.isArray(buses) ? buses : []).map(async bus => {
            const location = latest[bus.id]?.data;
            const previousStatus = busStatusMap[bus.id]?.status || null;
            const now = Date.now();
            let status = "DISCONNECTED";
            let ageSeconds = NaN;
            let lat = NaN;
            let lng = NaN;
            let currentStop = "";
            let nextStop = "";

            if (location) {
                lat = Number(location.latitude);
                lng = Number(location.longitude);
                const lastUpdate = parseTimestamp(location.last_updated);
                ageSeconds = (now - lastUpdate) / 1000;
                status = ageSeconds < ONLINE_THRESHOLD_SECONDS ? "ONLINE" : "OFFLINE";

                if (Number.isFinite(lat) && Number.isFinite(lng) && bus.route_id) {
                    const stopInfo = findStopInfo(await fetchStops(bus.route_id), lat, lng);
                    currentStop = stopInfo.currentStop?.stop_name || "";
                    nextStop = stopInfo.nextStop?.stop_name || (currentStop ? "End" : "");
                    if (status === "ONLINE" && stopInfo.isStopped) {
                        status = "STOPPED";
                    }
                }
            }

            if (previousStatus && previousStatus !== status) {
                if (status === "OFFLINE") showToast(`Bus ${bus.bus_number || bus.id} offline for ${formatAge(ageSeconds)}`);
                if (status === "DISCONNECTED") showToast(`Bus ${bus.bus_number || bus.id} disconnected`);
                if (status === "STOPPED") showToast(`Bus ${bus.bus_number || bus.id} stopped at ${currentStop || "a stop"}`);
            }

            busStatusMap[bus.id] = { status };
            return {
                id: bus.id,
                busNumber: bus.bus_number || `Bus ${bus.id}`,
                status,
                statusOrder: status === "STOPPED" ? 0 : status === "ONLINE" ? 1 : status === "OFFLINE" ? 2 : 3,
                ageLabel: status === "OFFLINE" ? "Offline for" : status === "DISCONNECTED" ? "Signal" : "Last update",
                ageText: status === "DISCONNECTED" ? "No location signal" : formatAge(ageSeconds),
                currentStop,
                nextStop,
                lat,
                lng
            };
        }));

        Object.keys(adminMarkers).forEach(id => {
            if (!items.some(item => String(item.id) === String(id))) {
                adminMap.removeLayer(adminMarkers[id]);
                delete adminMarkers[id];
            }
        });

        items.forEach(renderMarker);
        renderMonitor(items);
        updateMonitorCounts(items);
        if (adminMap) setTimeout(() => adminMap.invalidateSize(), 100);
    } catch (err) {
        console.error("Error checking bus status:", err);
        document.getElementById("mapStatus").innerText = "Sync failed";
        document.getElementById("busMonitorList").innerHTML = '<div class="empty-state">Unable to load bus status.</div>';
    }
}

function fetchCount(endpoint, elementId) {
    fetch(`${API_URL}/${endpoint}`)
        .then(res => res.json())
        .then(data => {
            const el = document.getElementById(elementId);
            if (el) el.innerText = Array.isArray(data) ? data.length : 0;
        })
        .catch(() => {});
}

function openChangePassword() {
    const modal = document.getElementById("passwordModal");
    if (modal) modal.style.display = "flex";
}

function closeModal() {
    const modal = document.getElementById("passwordModal");
    if (modal) modal.style.display = "none";
}

function loadFragment(url, placeholderId) {
    return fetch(url)
        .then(res => res.text())
        .then(html => {
            const placeholder = document.getElementById(placeholderId);
            if (placeholder) placeholder.innerHTML = html;
        })
        .catch(() => {});
}

setSidebarState(true);

document.addEventListener("DOMContentLoaded", () => {
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");

    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            setSidebarState(!document.body.classList.contains("sidebar-collapsed"));
        });
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener("click", () => {
            setSidebarState(true);
        });
    }

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            setSidebarState(true);
        }
    });

    initAdminMap();
    checkBusStatus();
    setInterval(checkBusStatus, 15000);
    fetchCount('get_students', 'totalStudents');
    fetchCount('get_buses', 'totalBuses');
    fetchCount('get_drivers', 'totalDrivers');
    loadFragment('sidebar.html', 'sidebar-placeholder');
    loadFragment('header.html', 'header-placeholder');
});
