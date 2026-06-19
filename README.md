# ARES: AI-Powered Incident Response Copilot for Bengaluru Traffic Police

ARES is an AI-powered backend decision-support system designed to help the Bengaluru Traffic Police prioritize traffic incidents, predict operational requirements, allocate resources, and generate diversion maps in real time. 

Designed for speed, simplicity, and ease of demonstration, this backend uses pre-trained Machine Learning models and deterministic rules to deliver instant incident insights.

---

## 🛠️ Technology Stack

* **Web Framework**: FastAPI (Asynchronous, self-documenting REST API)
* **Machine Learning**: Scikit-Learn (Random Forest classifiers for priority and road closure prediction)
* **Database**: SQLite (No ORM, raw SQL for lightweight execution)
* **Nearest Neighbors**: Scikit-Learn KNN (Euclidean distance on coordinates and incident features to find similar incidents)
* **Visualization**: Folium (Dynamic, interactive HTML traffic diversion maps)
* **Testing**: Pytest (Comprehensive unit and API endpoint test suites)

---

## 🚀 Key Features & Pipeline Flow

When an incident is reported, the backend runs a multi-step analytical pipeline:

```
[Incident Coordinates + Cause + Time]
                ↓
     1. Preprocessing & Auto-inference (Corridor, Police Station, Event Type)
                ↓
     2. Road Closure Prediction (Random Forest Model)
                ↓
     3. Priority Assessment (Random Forest Model: HIGH / LOW)
                ↓
     4. Operational Risk Assessment (Dynamic scoring: 0 - 100)
                ↓
     5. Resource Recommendation (Officers, Barricades, Escalation steps)
                ↓
     6. Similar Incident Retrieval (KNN search on historical incidents)
                ↓
     7. Diversion Map Generation (Folium interactive route diversion HTML)
```

1. **Priority & Road Closure Prediction**: Executes pre-trained Random Forest models loaded via `joblib` from `backend/models/`.
2. **Operational Risk Assessment**: Scores incident severity based on traffic peak hours, vehicle types, corridor bottlenecks, and predicted closures.
3. **Resource Recommendation**: Determines the required deployment of traffic police officers, barricades, and standard escalation procedures based on the computed risk.
4. **Similar Incident Retrieval**: Retrieves the top-K historically similar traffic incidents using a KNN model fitted on the preprocessed dataset.
5. **Diversion Visualization**: Auto-generates interactive Folium maps pointing to the incident location, marked with diversion circles and corridor warnings.
6. **Hotspot Analytics**: Aggregates high-frequency incident coordinates and displays risk patterns across major Bengaluru corridors.

### 📊 Risk & Resource Calculation Logic

The resource recommendation engine calculates an operational risk score (capped at 100) using the following scoring points:

* **High Priority** predicted by ML: **+25 points**
* **Road Closure** predicted by ML: **+20 points**
* **Peak Traffic Hours** (8-10 AM or 5-7 PM): **+15 points**
* **Major Incident Type**: **+15 points**
* **Night-time / Low Visibility**: **+10 points**
* **Heavy Vehicle Involved** (Truck/Bus/Tanker): **+10 points**
* **Two-Wheeler Involved**: **+5 points**

The final score translates directly into resource requirements:

| Risk Score | Risk Level | Recommended Officers | Recommended Barricades | Escalation Contact |
| :--- | :--- | :---: | :---: | :--- |
| $\ge$ 50 | 🔴 **HIGH** | **6 Officers** | 4 Barricades | ACP |
| $<$ 50 | 🟢 **LOW** | **2 Officers** | 0 Barricades | Inspector |

*(Additionally, a heavy recovery vehicle/crane is automatically requested if a heavy vehicle is involved).*


---

## 📥 Setup and Installation

### Prerequisites
* Python 3.10+
* Virtual environment (recommended)

### Installation Steps

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a Python virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Running the Backend

Start the development server using Uvicorn:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

* **API Base URL**: `http://localhost:8000`
* **Interactive Swagger Documentation**: `http://localhost:8000/docs` (Use this page to visually test all endpoints!)
* **Alternative Redoc Documentation**: `http://localhost:8000/redoc`

---

## 🔍 How to Test the API

### 1. Running the Automated Tests
Run the entire unit and API testing suite containing 33 tests:

```bash
# From the backend/ folder
python -m pytest -v
```

### 2. Manual Endpoint Testing
The main endpoint designed for the frontend is `/api/report`. It accepts a simplified request containing only the essential details the user provides.

#### **Endpoint**: `POST http://localhost:8000/api/report`
**Sample Request Body**:
```json
{
  "latitude": 13.0400,
  "longitude": 77.5180,
  "event_cause": 14,
  "time": "2026-06-19T15:30:00"
}
```

**What the Backend Does**:
* **Location Resolution**: Computes closest coordinates to auto-match the incident to a Bengaluru Traffic `corridor` and the nearest local `police_station`.
* **Datetime Parsing**: Extracts `hour`, `day_of_week`, and `month` from the `time` string.
* **Feature Imputation**: Automatically infers `event_type` from severity classifications and assigns standard `veh_type` defaults.
* **Pipeline Run**: Feeds these inferred variables into the ML models to output:
  * Resolved location details and distances.
  * Predicted priority (HIGH/LOW) and road closure needs.
  * Operational risk levels and recommendations.
  * Links to the generated interactive diversion map.

---

## 🗺️ Optional: MapmyIndia (Mappls) Integration

If you want to use the live MapmyIndia (Mappls) Places API to find actual, real-world police stations nearby instead of matching from the preprocessed dataset:

1. **Obtain Client Credentials** from the [Mappls Developer Portal](https://developer.mappls.com/).
2. **Configure your environment variables**:
   ```bash
   # Windows (Command Prompt)
   set MAPMYINDIA_CLIENT_ID=your_client_id
   set MAPMYINDIA_CLIENT_SECRET=your_client_secret

   # Windows (PowerShell)
   $env:MAPMYINDIA_CLIENT_ID="your_client_id"
   $env:MAPMYINDIA_CLIENT_SECRET="your_client_secret"
   ```
3. When running the server, `/api/report` will automatically query Mappls for live coordinates. If the API keys are not set, it gracefully falls back to the local nearest-neighbor lookup.

---

## 🚔 Police Station Portal & Retrospective Feedback (Learning Loop)

To support station-level incident queues and post-incident learning, ARES includes a dedicated Station Portal API.

### 1. Police Station Login
Every police station can log in using their numerical code (e.g., `39`). 
* **Endpoint**: `POST /api/portal/login`
* **JSON Body**:
  ```json
  {
    "police_station": 39,
    "password": "station_pass_39"
  }
  ```
  *(Note: For simplicity, the passcode format is `station_pass_<station_id>`)*
* **Response**: Returns a secure session token to authorize future requests.

### 2. Station-Specific Active Queues
Retrieve active or resolved incidents assigned specifically to a given police station.
* **Endpoint**: `GET /api/portal/incidents/{station_id}`
* **Authorization**: Include the session token as a Bearer token in the `Authorization` header.
* **Optional Query Parameters**: `?status=ACTIVE` or `?status=RESOLVED`.

### 3. Post-Incident Retrospective Feedback
When an incident is cleared, the station officer submits a feedback form (post-learning loop) detailing what resources were *actually* needed versus what the model recommended. This stores the true labels in the database, allowing future retraining.
* **Endpoint**: `POST /api/portal/incidents/{incident_id}/feedback`
* **Authorization**: Require `Authorization` header token.
* **JSON Body**:
  ```json
  {
    "actual_officers": 5,
    "actual_barricades": 8,
    "actual_road_closure": 1,
    "actual_priority": 1,
    "feedback_notes": "Heavy rains made a road closure absolutely necessary. Deployed 5 officers."
  }
  ```
* **Effect**: Saves feedback details to the database and transitions the incident `status` from `'ACTIVE'` to `'RESOLVED'` in real-time.