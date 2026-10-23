// 1. CACHE DOM ELEMENTS (Massive performance boost for polling)
const dom = {
    chartCtx: document.getElementById('telemetryChart').getContext('2d'),
    selector: document.getElementById('agent-selector'),
    status: document.getElementById('status-indicator'),
    cpuText: document.getElementById('cpu-text'),
    ramText: document.getElementById('ram-text'),
    ramDetails: document.getElementById('ram-details'),
    diskText: document.getElementById('disk-text'),
    diskDetails: document.getElementById('disk-details'),
    logTableBody: document.getElementById('log-table-body')
};

// 2. INITIALIZE CHART
const telemetryChart = new Chart(dom.chartCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            { label: 'CPU Usage (%)', borderColor: '#60A5FA', backgroundColor: 'rgba(96,165,250,0.1)', borderWidth: 2, tension: 0.3, data: [], fill: true },
            { label: 'RAM Usage (%)', borderColor: '#C084FC', borderWidth: 2, tension: 0.3, data: [] },
            { label: 'Disk Usage (%)', borderColor: '#34d399', borderWidth: 2, tension: 0.3, data: [] }
        ]
    },
    options: {
        responsive: true,
        scales: {
            y: { beginAtZero: true, max: 100, grid: { color: '#374151' } },
            x: { grid: { color: '#374151' } }
        },
    }
});

// STATE VARIABLES
let lastGraphedTimestamp = null;
let currentAgentId = null;

// 3. UI UPDATE HELPERS
function resetTextCards() {
    dom.cpuText.innerText = '--%';
    dom.ramText.innerText = '--%';
    dom.diskText.innerText = '--%';
    dom.ramDetails.innerText = '-- / -- GB';
    dom.diskDetails.innerText = 'Storage monitored';
}

function updateLogTable(log) {
    if (!log || !dom.logTableBody) return;

    const row = document.createElement('tr');
    row.className = "border-b border-gray-700 hover:bg-gray-750 transition-colors";
    row.innerHTML = `
        <td class="p-3 py-2">${new Date(log.timestamp).toLocaleTimeString()}</td>
        <td class="p-3 py-2 text-blue-400">${log.cpu_percent}%</td>
        <td class="p-3 py-2 text-purple-400">${log.ram_percent}%</td>
        <td class="p-3 py-2 text-teal-400">${log.disk_percent}%</td>
    `;

    // Add new row to the top
    dom.logTableBody.prepend(row);

    // Keep only the 10 most recent logs to prevent memory leaks
    if (dom.logTableBody.children.length > 10) {
        dom.logTableBody.removeChild(dom.logTableBody.lastChild);
    }
}

// 4. MAIN FETCH LOGIC
async function fetchAgentData() {
    try {
        const token=localStorage.getItem('jwt_token');

        const response = await fetch('/api/hosts', {
            headers: {
                'Authorization':`Bearer ${token}`
            }
        });
        const hostsData = await response.json();

        //save current selected user
        const previousSelectedId = dom.selector.value || currentAgentId

        //clear and rebuild dropdown on every poll
        dom.selector.innerText=''

        if (hostsData.length === 0) {
            const opt = new Option("No agents online","")
            dom.selector.add(opt);
            currentAgentId=null;
            resetTextCards()
            return;
        } else {
            hostsData.forEach(item => {
                const opt=new Option(`${item.host.hostname}`, item.host.id);
                dom.selector.add(opt);
            });

            const agentsStillOnline=Array.from(dom.selector.options).some(opt => opt.value === previousSelectedId)
            if (agentsStillOnline) {
                dom.selector.value=previousSelectedId;
                currentAgentId=previousSelectedId;
            } else {
                currentAgentId=hostsData[0].host.id.toString();
                dom.selector.value = currentAgentId;
                await loadAgentHistory(currentAgentId);
            }
        }

        const activeHostData = hostsData.find(item => item.host.id.toString() === currentAgentId);
        if (!activeHostData) return;

        const latest = activeHostData.latest_metric;

        dom.status.innerText = 'SYSTEM ONLINE';
        dom.status.className = "px-3 py-1 text-xs font-semibold rounded-full bg-green-900 text-green-400 tracking-wide";

        if (!latest) {
            resetTextCards();
            return;
        }

        // Update text cards with fixed math
        dom.cpuText.innerText = `${latest.cpu_percent}%`;
        dom.ramText.innerText = `${latest.ram_percent}%`;
        dom.diskText.innerText = `${latest.disk_percent}%`;

        if (latest.total_ram_gb) {
            const usedRam = ((latest.ram_percent/100)*latest.total_ram_gb).toFixed(1);
            dom.ramDetails.innerText = `${usedRam}/${latest.total_ram_gb} GB`;
        }

        if (latest.total_disk_gb) {
            const freeDisk = (latest.total_disk_gb-((latest.disk_percent/100)*latest.total_disk_gb)).toFixed(1);
            dom.diskDetails.innerText = `${freeDisk}/${latest.total_disk_gb} GB available`;
        }

        // Update chart and table with new data point
        if (latest.timestamp !== lastGraphedTimestamp) {
            const timeLabel = new Date(latest.timestamp).toLocaleTimeString();

            if (telemetryChart.data.labels.length >= 20) {
                telemetryChart.data.labels.shift();
                telemetryChart.data.datasets.forEach(dataset => dataset.data.shift());
            }

            telemetryChart.data.labels.push(timeLabel);
            telemetryChart.data.datasets[0].data.push(latest.cpu_percent);
            telemetryChart.data.datasets[1].data.push(latest.ram_percent);
            telemetryChart.data.datasets[2].data.push(latest.disk_percent);
            telemetryChart.update();

            updateLogTable(latest);
            lastGraphedTimestamp = latest.timestamp;
        }

    } catch (error) {
        console.error('Error fetching agent telemetry:', error);
        dom.status.innerText = 'CONNECTION ERROR';
        dom.status.className = "px-3 py-1 text-xs font-semibold rounded-full bg-red-900 text-red-400 tracking-wide";
    }
}

async function loadAgentHistory(agentId) {
    if (!agentId || agentId === 'underfined' || agentId === 'null') {
        console.warn("skipped history fetch: Invalid agentId");
        return;
    }
    try {

        const token = localStorage.getItem('jwt_token')
        const response = await fetch(`/api/hosts/${agentId}/history?limit=20`, {headers: {
                'Authorization': `Bearer ${token}`
            }
            });
        const data = await response.json();

        // Clear existing chart and table data
        telemetryChart.data.labels = [];
        telemetryChart.data.datasets.forEach(dataset => dataset.data = []);
        if (dom.logTableBody) dom.logTableBody.innerHTML = '';

        if (!data.history || data.history.length === 0) {
            telemetryChart.update();
            return;
        }

        // Hydrate chart and table
        data.history.forEach(log => {
            const timeLabel = new Date(log.timestamp).toLocaleTimeString();
            telemetryChart.data.labels.push(timeLabel);
            telemetryChart.data.datasets[0].data.push(log.cpu_percent);
            telemetryChart.data.datasets[1].data.push(log.ram_percent);
            telemetryChart.data.datasets[2].data.push(log.disk_percent);

            // Add to table (we prepend so oldest history is at bottom)
            updateLogTable(log);
        });

        telemetryChart.update();
        lastGraphedTimestamp = data.history[data.history.length-1].timestamp;

    } catch (error) {
        console.error("Error loading history:", error);
    }
}

// 5. EVENT LISTENERS
dom.selector.addEventListener('change', async function(e) {
    currentAgentId = e.target.value;
    lastGraphedTimestamp = null;
    resetTextCards();
    await loadAgentHistory(currentAgentId);
    await fetchAgentData();
});

// 6. START POLLING
setInterval(fetchAgentData, 5000);
fetchAgentData().catch(error=>console.error("Polling fetch error", error));