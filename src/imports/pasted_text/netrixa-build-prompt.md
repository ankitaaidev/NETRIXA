# MASTER BUILD PROMPT — NETRIXA

Build a production-quality full-stack web application called **NETRIXA**.

## PRODUCT NAME

**NETRIXA**

### Product tagline

**AI-Powered Thermal Intelligence & Early-Warning System**

### One-line description

NETRIXA transforms satellite thermal anomalies into explainable geospatial intelligence by combining NASA FIRMS thermal detections, satellite imagery, OpenStreetMap infrastructure, land-cover context and historical thermal behaviour to classify thermal sources, detect abnormal activity, assess risk and prioritize events for investigation.

### Target

This is a prototype for **Smart India Hackathon 2026 — Problem Statement 26162**, concerning AI-based detection and classification of industrial fires and persistent thermal sources using NASA FIRMS, OSM and satellite data.

The application must look like a serious government-grade geospatial intelligence platform, NOT like a generic startup dashboard.

---

# 1. CORE PRODUCT IDEA

The central product philosophy is:

> FIRMS tells us WHERE the heat is.
> NETRIXA determines WHAT it is, WHETHER it is abnormal, HOW risky it is, and WHAT should be investigated first.

The system must demonstrate this pipeline:

Satellite Data
→ Thermal Detection
→ Geospatial Context
→ AI Classification
→ Historical Behaviour
→ Anomaly Detection
→ Risk Assessment
→ Priority Ranking
→ Explainable Intelligence
→ Human Investigation

Do not build a simple FIRMS map.

The application must clearly demonstrate intelligence layered on top of thermal detections.

---

# 2. DESIGN DIRECTION

Create a sophisticated dark-mode geospatial intelligence interface.

Visual style:

* Government intelligence / mission-control aesthetic
* Dark navy/black background
* High information density
* Clean typography
* Subtle glass panels
* Thin borders
* Minimal gradients
* Professional GIS styling
* No excessive rounded cards
* No cartoonish graphics
* No generic SaaS appearance

Use a restrained accent system:

* Green = low risk
* Amber = medium risk
* Orange = high risk
* Red = critical
* Blue/cyan = neutral intelligence/data

Use animations sparingly:

* Map event pulse
* Panel transitions
* Loading states
* Risk changes
* Event selection

The UI must remain fast and usable.

---

# 3. TECHNOLOGY STACK

## Frontend

Use:

* React
* TypeScript
* Vite
* Tailwind CSS
* shadcn/ui where useful
* Lucide icons
* MapLibre GL JS OR Leaflet
* Recharts for charts
* React Query / TanStack Query
* React Router
* Zustand for lightweight application state

## Backend

Use:

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* PostgreSQL
* PostGIS

## Data processing

Use:

* GeoPandas
* Shapely
* Pandas
* NumPy
* Rasterio where required

## Machine learning

Initial prototype:

* scikit-learn
* XGBoost if available

Design the ML service so it can later be replaced by a deep-learning satellite model.

## Infrastructure

Use Docker Compose.

Services:

frontend
backend
postgres/postgis

Optional:

redis
worker

---

# 4. PROJECT STRUCTURE

Create:

```text
netrixa/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── types/
│   │   ├── data/
│   │   ├── utils/
│   │   └── App.tsx
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── ml/
│   │   ├── geospatial/
│   │   ├── risk/
│   │   ├── database/
│   │   ├── utils/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── data/
│   ├── demo/
│   ├── firms/
│   ├── facilities/
│   └── landcover/
│
├── docker-compose.yml
├── README.md
└── .env.example
```

---

# 5. APPLICATION ROUTES

Create these frontend routes:

```text
/
 /dashboard
 /events
 /events/:eventId
 /priority
 /history
 /facilities
 /alerts
 /reports
 /settings
```

The root route should redirect to `/dashboard`.

---

# 6. GLOBAL APPLICATION LAYOUT

Create a persistent application shell.

## Left sidebar

NETRIXA logo at top.

Navigation:

* Overview
* Thermal Events
* Priority Center
* Historical Intelligence
* Facilities
* Alerts
* Reports

Bottom:

* System Status
* Data Last Updated
* Settings

## Top bar

Show:

NETRIXA

Global search

Data status

Last synchronization

Notification icon

User/operator profile

---

# 7. DASHBOARD

Route:

`/dashboard`

This is the primary landing page.

## Header

Display:

NETRIXA

THERMAL INTELLIGENCE CENTER

Subtitle:

National-scale monitoring of thermal anomalies and industrial risk.

## KPI cards

Show:

* Total Thermal Events
* Industrial Context Events
* Potential Industrial Fires
* Critical Events
* Persistent Thermal Sources

Use real API values.

For demo mode, use seeded data.

---

# 8. MAIN GIS MAP

The map should occupy the largest portion of the dashboard.

Display:

* Thermal events
* Industrial facilities
* Administrative boundaries
* Land-cover context
* Risk layers
* Historical event density

Thermal event markers must be visually differentiated by risk.

Use clustering when zoomed out.

When zoomed in, show individual events.

Clicking an event opens an event preview panel.

---

# 9. MAP CONTROLS

Add controls:

* Zoom
* Locate
* Layer selector
* Fullscreen
* Satellite/base map toggle
* Event clustering toggle
* Heatmap toggle

Layer selector:

```text
☑ Thermal Events
☑ Industrial Facilities
☐ Land Cover
☐ Administrative Boundaries
☐ Historical Events
☐ Risk Heatmap
☐ Satellite Imagery
```

---

# 10. MAP EVENT PREVIEW

Clicking a marker opens:

```text
EVENT NTX-IND-00241

Potential Industrial Fire

CRITICAL

Confidence
87%

Risk Score
94/100

Industrial facility
180 m away

Historical deviation
HIGH

Persistence
2 observations

[Investigate Event]
```

Clicking Investigate opens the event detail page.

---

# 11. EVENT DETAIL PAGE

Route:

`/events/:eventId`

This is the most important page.

Header:

```text
EVENT NTX-IND-00241

Potential Industrial Fire

CRITICAL
```

Show:

* Classification
* Confidence
* Risk score
* Coordinates
* Detection time
* Satellite source
* Facility association
* Land cover
* Administrative location

---

# 12. EVENT DETAIL SECTIONS

Create tabs:

```text
Overview
Thermal Analysis
Historical Behaviour
Satellite Evidence
Infrastructure
AI Explanation
```

---

# 13. OVERVIEW TAB

Display:

## Event Summary

Classification:

Potential Industrial Fire

Confidence:

87%

Risk:

94 / 100

Priority:

CRITICAL

Then show:

* Current thermal intensity
* Detection confidence
* Persistence
* Facility distance
* Historical deviation
* Spatial change

---

# 14. THERMAL ANALYSIS

Create a professional chart.

Show:

* Thermal intensity
* FRP where available
* Observation timestamps
* Historical baseline

Current event should visually stand out.

Example:

```text
Historical baseline
────────────────────────

Current event
                 ●
                 │
                 │
───────────────●─┴────────
```

Add:

Normal Range

Current Observation

Deviation

---

# 15. HISTORICAL BEHAVIOUR

This is a core differentiator.

Create a historical thermal activity chart.

Show:

* Historical mean
* Historical range
* Current value
* Anomaly threshold

Calculate:

```text
z_score =
(current_value - historical_mean)
/
historical_standard_deviation
```

Display:

```text
Historical Mean       52
Current Intensity    118
Deviation             +3.2σ
```

Use demo values if real history is unavailable.

Label demo values honestly as simulated/demo data.

---

# 16. PERSISTENCE INTELLIGENCE

Display:

```text
PERSISTENCE ANALYSIS

First observed:
12 Aug 2026

Last observed:
04 Sep 2026

Observations:
18

Recurrence:
High

Spatial stability:
High

Behaviour:
Persistent
```

Then classify:

```text
NORMAL PERSISTENT
ABNORMAL PERSISTENT
SUDDEN EVENT
INTERMITTENT
UNKNOWN
```

---

# 17. AI CLASSIFICATION PAGE

Create a visual classification probability panel.

Example:

```text
AI SOURCE CLASSIFICATION

Potential Industrial Fire          87%
Persistent Industrial Source        6%
Gas Flare                           4%
Agricultural Burning                1%
Wildfire                            1%
Other                               1%
```

Do NOT claim that these are scientifically validated percentages unless generated by the actual model.

For demo mode, clearly identify them as prototype model outputs.

---

# 18. AI EXPLANATION

Create:

## WHY NETRIXA FLAGGED THIS EVENT

Show evidence cards:

✓ Industrial facility nearby

✓ Industrial land-use context

✓ Thermal intensity above baseline

✓ Historical deviation detected

✓ Spatial behaviour changed

✓ Satellite evidence available

Then show:

```text
Primary contributing factors

Industrial context        HIGH
Thermal anomaly           HIGH
Historical deviation      HIGH
Spatial change            MEDIUM
Persistence pattern       MEDIUM
```

This is the explainable AI layer.

---

# 19. UNKNOWN CLASS

Never force every event into a category.

Support:

```text
UNKNOWN / INSUFFICIENT EVIDENCE
```

If confidence is below the configurable threshold, classify as Unknown and recommend human review.

---

# 20. PRIORITY CENTER

Route:

`/priority`

This should be a major feature.

Header:

PRIORITY CENTER

Subtitle:

Ranked thermal events requiring operator attention.

Create a table:

```text
Priority
Event
Classification
Location
Risk
Confidence
Detected
Recommended Action
```

Example:

```text
01   Potential Industrial Fire   Critical   Investigate
02   Industrial Fire             High       Verify
03   Abnormal Thermal Source     High       Monitor
04   Persistent Source           Medium     Observe
05   Agricultural Burning        Low        No Action
```

Allow sorting and filtering.

---

# 21. RISK ENGINE

Implement a transparent prototype risk engine.

Initial formula:

```text
risk_score =
0.30 * thermal_anomaly_score
+
0.20 * industrial_proximity_score
+
0.15 * historical_deviation_score
+
0.15 * spatial_change_score
+
0.10 * persistence_score
+
0.10 * classification_confidence_score
```

Normalize to 0–100.

Risk levels:

```text
0–25     LOW
26–50    MEDIUM
51–75    HIGH
76–100   CRITICAL
```

Make weights configurable.

Clearly label this as a prototype scoring model until validated.

---

# 22. ALERT SYSTEM

Route:

`/alerts`

Display:

Critical alerts

High-priority alerts

Resolved alerts

Create alert cards.

Example:

```text
CRITICAL ALERT

Potential Industrial Fire

Event NTX-IND-00241

Risk Score: 94

Reason:
Thermal intensity significantly above
historical baseline near industrial facility.

Recommended Action:
Immediate investigation.
```

Do not alert on every thermal detection.

The alert system should prioritize significant deviations.

---

# 23. FACILITIES PAGE

Route:

`/facilities`

Show:

* Facility name
* Facility type
* Coordinates
* Thermal activity
* Current status
* Persistent source status
* Risk events nearby

Facility types:

* Refinery
* Petrochemical
* Thermal Power Plant
* Steel Plant
* Mining
* LNG Terminal
* Other Industrial Facility

---

# 24. FACILITY DETAIL

Clicking a facility should show:

```text
FACILITY

Name
Type
Location

THERMAL PROFILE

30-day activity
90-day activity
Historical baseline

CURRENT STATUS

Normal
Watch
Abnormal
Critical
```

Show all nearby thermal events.

---

# 25. REPORTS

Route:

`/reports`

Create a report generator.

Report should contain:

* Event ID
* Location
* Time
* Classification
* Confidence
* Risk score
* Thermal analysis
* Historical behaviour
* Facility information
* AI explanation
* Recommended action

Allow:

Generate Report

Download PDF

---

# 26. HISTORICAL INTELLIGENCE PAGE

Route:

`/history`

Show:

* Thermal event timeline
* Persistent locations
* Recurring hotspots
* Abnormal events
* Historical baselines

Charts:

* Events by day
* Events by classification
* Industrial events over time
* Risk distribution
* Persistent sources

---

# 27. FILTER SYSTEM

Global filters:

```text
Date Range
State
District
Classification
Risk Level
Facility Type
Confidence
Persistence
```

Filters must update:

* Map
* KPIs
* Event list
* Charts
* Priority queue

---

# 28. SEARCH

Global search should support:

* Event ID
* Facility name
* Coordinates
* State
* District

Example:

Search:

`NTX-IND-00241`

returns event.

Search:

`Refinery`

returns relevant facilities/events.

---

# 29. BACKEND DATABASE

Create PostGIS models.

## thermal_events

Fields:

```text
id
event_id
latitude
longitude
geometry
acquisition_date
acquisition_time
brightness_temperature
frp
confidence
satellite
instrument
source
created_at
```

## facilities

```text
id
facility_id
name
facility_type
latitude
longitude
geometry
source
```

## historical_observations

```text
id
event_location_id
observation_date
intensity
frp
confidence
geometry
```

## event_analysis

```text
id
event_id
classification
confidence
risk_score
risk_level
persistence_score
anomaly_score
historical_deviation
industrial_proximity
spatial_change_score
explanation
recommended_action
created_at
```

## alerts

```text
id
event_id
severity
title
message
status
created_at
resolved_at
```

---

# 30. BACKEND API

Create REST APIs.

## Dashboard

```text
GET /api/dashboard/summary
```

Return:

```json
{
  "total_events": 12482,
  "industrial_events": 836,
  "potential_industrial_fires": 47,
  "critical_events": 12,
  "persistent_sources": 124
}
```

## Thermal events

```text
GET /api/events
GET /api/events/{event_id}
```

Support query parameters:

```text
date_from
date_to
classification
risk_level
state
facility_type
```

## Map

```text
GET /api/map/events
GET /api/map/facilities
```

Return GeoJSON.

## Analysis

```text
POST /api/events/{event_id}/analyze
```

## Historical

```text
GET /api/events/{event_id}/history
```

## Priority

```text
GET /api/priority
```

## Facilities

```text
GET /api/facilities
GET /api/facilities/{facility_id}
```

## Alerts

```text
GET /api/alerts
POST /api/alerts/{id}/resolve
```

## Reports

```text
POST /api/reports/events/{event_id}
```

---

# 31. GEOJSON

All geospatial endpoints should support GeoJSON.

Example:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [88.36, 22.57]
  },
  "properties": {
    "event_id": "NTX-IND-00241",
    "risk": "CRITICAL",
    "risk_score": 94,
    "classification": "Potential Industrial Fire"
  }
}
```

---

# 32. FIRMS INGESTION

Create a service:

```text
backend/app/services/firms_service.py
```

Responsibilities:

* Fetch FIRMS data when API credentials are available
* Parse thermal events
* Validate fields
* Normalize coordinates
* Store events
* Prevent duplicates
* Record ingestion time

Use environment variables.

```text
FIRMS_API_KEY=
```

Never hard-code API keys.

---

# 33. DEMO MODE

This is extremely important.

The application MUST work without external APIs.

Create:

```text
DEMO_MODE=true
```

When enabled:

* Load seeded realistic data
* Show India map
* Show industrial facilities
* Show historical observations
* Show classifications
* Show risk scores
* Show alerts

The entire SIH demonstration must work offline after startup.

---

# 34. DEMO DATA

Create at least:

### 150–300 thermal events

Spread across India.

Include:

* Industrial
* Agricultural
* Forest
* Mining
* Persistent industrial
* Unknown

Create at least:

### 30 industrial facilities

Types:

* Refinery
* Power Plant
* Steel
* Mining
* LNG
* Petrochemical

Create at least:

### 20 high-risk events

Create at least:

### 5 critical events

Create at least:

### 10 persistent thermal sources

The data should be internally consistent.

---

# 35. THREE HERO DEMO EVENTS

Seed three especially convincing events.

## DEMO EVENT 1

Normal refinery thermal source.

Expected:

```text
Classification:
Persistent Industrial Thermal Source

Risk:
LOW

Historical behaviour:
Stable/persistent

Action:
Observe
```

## DEMO EVENT 2

Agricultural thermal anomaly.

Expected:

```text
Classification:
Agricultural Burning

Risk:
LOW

Action:
No immediate action
```

## DEMO EVENT 3

Abnormal industrial event.

Expected:

```text
Classification:
Potential Industrial Fire

Risk:
CRITICAL

Historical deviation:
HIGH

Industrial proximity:
HIGH

Action:
Immediate investigation
```

These three events should be easy to find during a presentation.

---

# 36. AI SERVICE

Create:

```text
backend/app/ml/classifier.py
```

Implement a clean interface:

```python
class ThermalClassifier:

    def predict(self, features):
        ...

    def explain(self, features):
        ...
```

Use a trained model if available.

Otherwise provide a deterministic prototype classifier based on features.

Do NOT fake model accuracy.

Return:

```json
{
  "classification": "Potential Industrial Fire",
  "confidence": 0.87,
  "probabilities": {},
  "explanation": []
}
```

---

# 37. FEATURE ENGINEERING

Create:

```text
backend/app/ml/features.py
```

Generate:

```text
thermal_intensity
frp
confidence
facility_distance
industrial_context
land_cover
historical_mean
historical_std
historical_deviation
persistence
recurrence
spatial_change
```

Create reusable functions.

---

# 38. TEMPORAL ENGINE

Create:

```text
backend/app/services/temporal_service.py
```

Calculate:

* Event frequency
* Persistence
* Recurrence
* Historical average
* Historical standard deviation
* Current deviation
* Trend

Return:

```json
{
  "persistence": "HIGH",
  "recurrence": 18,
  "historical_mean": 52,
  "current_value": 118,
  "z_score": 3.2,
  "abnormal": true
}
```

---

# 39. GEOSPATIAL ENGINE

Create:

```text
backend/app/geospatial/context.py
```

For every event calculate:

* Nearest industrial facility
* Facility distance
* Industrial land-use context
* Nearby infrastructure
* Land-cover category
* Administrative region

Use PostGIS spatial queries.

---

# 40. SATELLITE EVIDENCE

Design the architecture for satellite imagery.

For the prototype:

* Allow satellite image metadata
* Allow image preview URLs
* Allow before/after image comparison
* Create a satellite evidence panel

Do not fabricate actual satellite evidence.

If no live imagery is available, display:

```text
Satellite evidence unavailable
```

or use clearly labeled demo imagery.

---

# 41. HUMAN-IN-THE-LOOP

Every event should support:

```text
Confirm Classification
Mark False Positive
Needs Investigation
Unknown
```

Store analyst feedback.

API:

```text
POST /api/events/{event_id}/feedback
```

This feedback can later be used for model improvement.

---

# 42. CONFIGURATION

Create:

```text
backend/.env.example
```

Variables:

```text
DATABASE_URL=
FIRMS_API_KEY=
DEMO_MODE=true
RISK_THRESHOLD_LOW=25
RISK_THRESHOLD_MEDIUM=50
RISK_THRESHOLD_HIGH=75
```

---

# 43. ERROR HANDLING

Frontend:

* Loading skeletons
* Empty states
* API error states
* Retry buttons
* Offline/demo fallback

Backend:

* Structured error responses
* Logging
* Input validation
* Database error handling

---

# 44. SECURITY

Implement:

* Environment variables for secrets
* CORS configuration
* Pydantic validation
* No API keys in frontend
* No secrets committed to Git
* Basic rate limiting architecture
* Sanitized user inputs

---

# 45. PERFORMANCE

Optimize:

* Map marker clustering
* GeoJSON payloads
* Database spatial indexes
* Pagination
* API caching
* Lazy-loaded pages
* Debounced search

Create PostGIS indexes for:

```text
geometry
acquisition_date
classification
risk_level
```

---

# 46. RESPONSIVE DESIGN

Desktop is the primary target.

Also support:

* Laptop
* Tablet
* Smaller screens

The GIS dashboard should remain usable on smaller screens.

---

# 47. SYSTEM STATUS

Display:

```text
DATA PIPELINE       ● ONLINE
GIS ENGINE          ● ONLINE
AI ENGINE           ● ONLINE
DATABASE            ● ONLINE
SATELLITE FEED      ● DEMO / LIVE
```

Use actual backend health checks.

API:

```text
GET /api/health
```

---

# 48. DEMO MODE BANNER

If demo mode is enabled, subtly show:

```text
DEMO ENVIRONMENT
```

Do not make it visually dominant.

---

# 49. LANDING / LOGIN

Do not create an unnecessary marketing landing page.

Open directly into the intelligence dashboard.

If authentication is implemented, use a minimal professional operator login.

For SIH prototype demonstration, a demo-access button can bypass authentication.

---

# 50. MICROINTERACTIONS

Add:

* Event pulse on map
* Hover tooltip
* Smooth panel transitions
* Risk badge animation for critical events
* Chart transitions
* Skeleton loaders
* Toast notifications

Avoid excessive animations.

---

# 51. ACCESSIBILITY

Use:

* Semantic HTML
* Keyboard navigation
* Accessible buttons
* ARIA labels
* Sufficient contrast
* Focus states

---

# 52. README

Create a comprehensive README containing:

1. Project overview
2. Problem statement
3. Architecture
4. Technology stack
5. Local setup
6. Docker setup
7. Environment variables
8. Demo mode
9. API documentation
10. Database schema
11. AI architecture
12. Geospatial architecture
13. Future enhancements

Include exact commands:

```bash
docker compose up --build
```

---

# 53. DOCKER

Create Docker Compose with:

```text
frontend
backend
postgres
```

Configure PostGIS.

Application should start with:

```bash
docker compose up
```

---

# 54. TESTING

Backend tests:

* Risk calculation
* Classification
* Historical analysis
* Geospatial matching
* API validation

Frontend tests:

* Dashboard rendering
* Event selection
* Filters
* Priority table

Create sample test data.

---

# 55. IMPORTANT PRODUCT RULES

Do NOT:

* Claim 99.9% AI accuracy
* Claim exact building-level detection from coarse thermal pixels
* Pretend simulated data is real
* Invent satellite evidence
* Present prototype risk weights as scientifically validated
* Present demo model probabilities as real-world validated confidence

Instead:

* Use confidence-aware language
* Include Unknown
* Include human review
* Label simulated/demo data
* Make the architecture ready for real data

---

# 56. HERO DEMONSTRATION FLOW

The application must support this exact SIH presentation sequence.

### Step 1

Open dashboard.

Say:

> “NETRIXA starts with thousands of satellite thermal detections.”

### Step 2

Show map.

Say:

> “But a hotspot alone does not tell authorities what is happening.”

### Step 3

Click a normal refinery source.

Show:

> Persistent Industrial Thermal Source — LOW RISK

### Step 4

Open historical behaviour.

Show stable recurring activity.

### Step 5

Return to map.

Click abnormal industrial event.

### Step 6

Show:

> Potential Industrial Fire — CRITICAL

### Step 7

Open AI explanation.

Show why the model flagged it.

### Step 8

Open historical analysis.

Show large deviation.

### Step 9

Open Priority Center.

Show that NETRIXA ranks the event above ordinary thermal detections.

### Step 10

Generate incident report.

Final statement:

> “NETRIXA doesn't just tell authorities where the heat is. It tells them what it likely is, whether it is abnormal, how risky it is, and what deserves attention first.”

---

# 57. FINAL UI QUALITY REQUIREMENT

The final interface must look like a serious national geospatial intelligence product.

It should resemble:

* Mission control
* GIS command center
* Satellite intelligence platform
* Disaster response operations center

It must NOT look like:

* Student CRUD application
* Generic admin dashboard
* Basic map project
* Generic AI chatbot
* Cryptocurrency dashboard
* Template website

---

# 58. DEVELOPMENT INSTRUCTION

Build incrementally.

First create:

1. Project structure
2. Database
3. Backend health endpoint
4. Demo data
5. Map
6. Dashboard
7. Event detail
8. Historical analysis
9. AI classification
10. Risk engine
11. Priority Center
12. Alerts
13. Reports
14. Final polish

After each major module, ensure the application still runs.

Do not leave placeholder buttons that appear functional but do nothing.

Every visible action should either work or be clearly marked unavailable.

---

# 59. ACCEPTANCE CRITERIA

The project is complete when:

* The application starts with Docker
* Dashboard loads
* India GIS map loads
* Thermal events appear
* Facilities appear
* Events can be clicked
* Event detail page works
* AI classification works in demo mode
* Historical charts work
* Persistence analysis works
* Risk score works
* Priority Center works
* Alerts work
* Reports work
* Filters work
* Search works
* Demo scenario works offline
* No API secrets are exposed
* No fake accuracy claims exist
* UI looks polished enough for SIH judging

---

# 60. START NOW

Do not merely explain how to build this.

Actually create the application.

Start with the complete project structure, install dependencies, create the database schema, seed the demo data, implement the FastAPI backend, implement the React frontend, and connect the dashboard to the backend.

After completing each stage, verify that it runs before continuing.

The final result must be a functioning full-stack prototype named:

# NETRIXA

**AI-Powered Thermal Intelligence & Early-Warning System**

Build it as a serious SIH 2026 prototype for Problem Statement 26162.
