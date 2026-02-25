# f25_team_21
Repository for f25_team_21

# POGOH Station Operations Dashboard
## 1. Overview
The dashboard helps POGOH operations managers and dispatchers monitor bike-share stations in real time. It consumes the POGOH API, stores snapshots for historical charts, and presents an interactive map with KPIs, charts, and filters. Tech stack: Django + PostgreSQL (backend), React + WebSocket/Ajax (frontend), Google Maps JS API (visualisation).
## 2. Product Backlog (grouped by module)

| Module                | Action (user-observable behaviour) |
|------------------------|------------------------------------|
| **Authentication**     | • Register a new account<br>• Log in / Log out |
| **Station Management** | • Add a new station record (admin)<br>• Edit station metadata (admin)<br>• View station list with filter pane |
| **Real-time Data**     | • Fetch current bike counts for all stations every 60 s via POGOH API<br>• Persist snapshots for analytics |
| **Dashboard Map**      | • Display all stations on map<br>• Colour icon green / yellow / red for full / filling / empty<br>• Click icon to open station detail |
| **Station Detail View**| • Show KPI “Bikes available now”<br>• Show line chart of bikes today (00:00 → now)<br>• Highlight KPI with same colour rule |
| **Comments / Feedback**| • Post comment about a station<br>• List comments chronologically |
| **Performance & DevOps**| • WebSocket push to React when new snapshot arrives<br>• Docker compose for local dev<br>• Unit tests ≥ 70% coverage |
## 3. Demo
https://github.com/user-attachments/assets/c5d6d159-cac9-425e-b530-2879aa027a83
