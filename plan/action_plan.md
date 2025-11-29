# Action Plan Checklist - HealthSync AI

## Phase 0: Infrastructure Setup
- [ ] **Project Initialization**
    - [ ] Initialize Git repository
    - [ ] Create project structure (`apps/web`, `packages/api`, `storage`)
    - [ ] Setup Python 3.11 environment & `requirements.txt`
- [ ] **Database Setup**
    - [ ] Setup MongoDB connection (Motor/Pymongo)
    - [ ] Setup DuckDB integration (install `duckdb`)

## Phase 1: Backend Foundation (FastAPI)
- [ ] **Authentication**
    - [ ] Implement User Model (MongoDB)
    - [ ] Implement JWT Login/Signup Endpoints
- [ ] **Data Ingestion Pipeline**
    - [ ] Create `POST /api/v1/ingest` endpoint
    - [ ] Implement Zip file upload handling
    - [ ] Implement Unzip logic to `storage/{user_id}/`
    - [ ] Verify DuckDB can query the uploaded CSVs

## Phase 2: AI Brain (MCP Server)
- [ ] **MCP Tools Implementation**
    - [ ] Implement `health_schema` tool (Read CSV headers)
    - [ ] Implement `health_query` tool (Execute SQL on DuckDB)
    - [ ] Implement `get_user_context` tool (Read MongoDB user profile)
- [ ] **MCP Server Configuration**
    - [ ] Setup MCP Server using Python SDK
    - [ ] Configure stdio transport
    - [ ] Test connectivity with Claude Desktop

## Phase 3: Web Frontend (React + Vite)
- [ ] **Setup & UI**
    - [ ] Initialize React + Vite + TailwindCSS project
    - [ ] Setup Routing (React Router)
- [ ] **Authentication UI**
    - [ ] Create Login Page
    - [ ] Create Signup Page
- [ ] **Dashboard Features**
    - [ ] Create Data Upload Component (File input)
    - [ ] Create Chat Interface (Message list, Input)
    - [ ] Implement Chart Rendering (Recharts) for AI responses

## Phase 4: Integration & Polish
- [ ] **Integration**
    - [ ] Connect Frontend Chat to Backend API
    - [ ] Save Chat History to MongoDB
- [ ] **Verification**
    - [ ] Test full flow: Login -> Upload -> Chat -> Graph
    - [ ] Record Demo Video
- [ ] **Deployment (AWS)**
    - [ ] Setup EC2 Instance (Ubuntu)
    - [ ] Configure Security Groups (Allow ports 80, 443, 8000)
    - [ ] Deploy Backend (Docker/Systemd)
    - [ ] Deploy Frontend (S3 + CloudFront or Nginx on EC2)
