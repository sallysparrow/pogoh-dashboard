document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("map") && document.getElementById("stationList")) {
    initOverview();
  }
  if (document.getElementById("stationDetailRoot")) {
    initStationDetail();
  }
});

// CSRF
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
const csrftoken = getCookie('csrftoken');

// Leaflet colored pins
function makePin(color) {
  const svg = encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="38" viewBox="0 0 26 38">
      <path fill="${color}" d="M13 0C6 0 1 5 1 12c0 8.4 9 17 12 26 3-9 12-17.6 12-26C25 5 20 0 13 0z"/>
      <circle cx="13" cy="12" r="5" fill="#ffffff"/>
    </svg>`
  );
  return L.icon({
    iconUrl: "data:image/svg+xml," + svg,
    iconSize: [26, 38],
    iconAnchor: [13, 38],
    popupAnchor: [0, -30]
  });
}

const ICONS = {
  bad_empty: makePin("#ef4444"), // 0% bad
  low:       makePin("#f97316"), // 1-15% not great
  ok:        makePin("#22c55e"), // 16-75% okay
  high:      makePin("#f97316"), // 76-90% not great
  bad_full:  makePin("#ef4444")  // 100% bad
};

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("map") && document.getElementById("stationList")) {
    initOverview();
  }
  if (document.getElementById("stationDetailRoot")) {
    initStationDetail();
  }
});

/* -------- Overview page: station list + map -------- */

function initOverview() {
  const listEl = document.getElementById("stationList");
  const map = L.map('map').setView([40.4406, -79.9959], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  fetch("/api/stations/")
    .then(r => r.json())
    .then(data => {
      data.stations.forEach(s => {
        // list item
        const li = document.createElement("li");

        const link = document.createElement("a");
        link.href = `/dashboard/station/${s.id}/`;
        link.textContent = s.name;
        link.className = "name-link";

        const status = document.createElement("span");
        status.className = "status-pill";

        let statusText;
        switch (s.status) {
          case "bad_empty":
            status.classList.add("status-bad");
            statusText = "0%";
            break;
          case "low":
            status.classList.add("status-low");
            statusText = `${s.pct_full}%`;
            break;
          case "ok":
            status.classList.add("status-ok");
            statusText = `${s.pct_full}%`;
            break;
          case "high":
            status.classList.add("status-high");
            statusText = `${s.pct_full}%`;
            break;
          case "bad_full":
            status.classList.add("status-bad");
            statusText = "100%";
            break;
          default:
            status.classList.add("status-ok");
            statusText = `${s.pct_full}%`;
        }
        status.textContent = statusText;

        li.append(link, status);
        listEl.appendChild(li);

        // marker
        const icon = ICONS[s.status] || ICONS.ok;
        const m = L.marker([s.latitude, s.longitude], { icon }).addTo(map);

        m.bindPopup(
          `<strong>${s.name}</strong><br>${s.pct_full}% full`
        );

        // clicking pin goes to detail page (like clicking list)
        m.on("click", () => {
          // popup shows info; navigation is explicit
          m.openPopup();
        });

        // if you want direct navigation on pin click instead:
        // m.on("click", () => { window.location.href = `/dashboard/station/${s.id}/`; });
      });
    });
}

/* -------- Station detail page: details + comments + chart -------- */

function initStationDetail() {
  const root = document.getElementById("stationDetailRoot");
  const stationId = parseInt(root.dataset.stationId, 10);

  const stationName = document.getElementById("stationName");
  const bikeCount = document.getElementById("bikeCount");
  const pctFull = document.getElementById("pctFull");
  const slots = document.getElementById("slots");

  const commentList = document.getElementById("commentList");
  const commentForm = document.getElementById("commentForm");
  const commentInput = document.getElementById("commentInput");
  const trendCanvas = document.getElementById("trendChart");

  let chart = null;

  // Station detail
  fetch(`/api/stations/${stationId}/`)
    .then(r => r.json())
    .then(d => {
      stationName.textContent = d.name;
      bikeCount.textContent = d.free_bikes;
      pctFull.textContent = `${d.pct_full}%`;
      slots.textContent = d.slots;
    });

  // Comments
  function loadComments() {
    fetch(`/api/stations/${stationId}/comments/`)
      .then(r => r.json())
      .then(d => {
        commentList.innerHTML = "";
        if (!d.comments.length) {
          const li = document.createElement("li");
          li.innerHTML = `<span class="muted">No comments yet.</span><span></span>`;
          commentList.appendChild(li);
          return;
        }
        d.comments.forEach(c => {
          const li = document.createElement("li");
          const left = document.createElement("span");
          left.textContent = c.content;
          const right = document.createElement("span");
          right.className = "muted";
          right.textContent = c.time;
          li.append(left, right);
          commentList.appendChild(li);
        });
      });
  }
  loadComments();

  commentForm.addEventListener("submit", e => {
    e.preventDefault();
    const text = (commentInput.value || "").trim();
    if (!text) return;

    const formData = new FormData();
    formData.append("content", text);

    fetch(`/api/stations/${stationId}/comments/add/`, {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken },
      body: formData
    })
      .then(r => {
        if (!r.ok) throw new Error();
        commentInput.value = "";
        loadComments();
      })
      .catch(() => {});
  });

  // Trend chart
  fetch(`/api/stations/${stationId}/trend/`)
    .then(r => r.json())
    .then(d => {
      if (!d.labels.length) return;
      const ctx = trendCanvas.getContext("2d");
      chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: d.labels,
          datasets: [{
            data: d.values,
            tension: 0.3
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1 } }
          }
        }
      });
    });
}