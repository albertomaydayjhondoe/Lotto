# Stakazo Dashboard - Internal Admin Panel

> **PASO 6.2**: Complete frontend implementation for Stakazo orchestration system

Modern, premium-quality dashboard built with Next.js 14, React, TypeScript, and TailwindCSS.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Pages](#pages)
- [API Integration](#api-integration)
- [Testing](#testing)
- [Screenshots](#screenshots)
- [File Structure](#file-structure)

---

## 🎯 Overview

The Stakazo Dashboard is an internal admin panel that provides real-time monitoring and management of the orchestration system. It consumes the backend API endpoints created in PASO 6.1 and presents comprehensive analytics, queue management, orchestrator monitoring, platform performance, and campaign management.

**Key Benefits:**
- Real-time statistics and metrics
- Visual data representation with charts
- Queue management with action buttons
- Platform performance comparison
- Campaign orchestration overview
- Mobile-responsive design
- JWT-based authentication

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      NEXT.JS 14 APP ROUTER                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Login      │  │  Dashboard   │  │   Queue      │     │
│  │   Page       │  │   Layout     │  │   Page       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Orchestrator │  │  Platforms   │  │  Campaigns   │     │
│  │   Page       │  │   Page       │  │   Page       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                    REACT QUERY LAYER                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  useDashboardOverview  │  useDashboardQueue         │  │
│  │  useDashboardOrchestrator │  useDashboardPlatforms  │  │
│  │  useDashboardCampaigns                               │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      API CLIENT (AXIOS)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  GET /dashboard/stats/overview                       │  │
│  │  GET /dashboard/stats/queue                          │  │
│  │  GET /dashboard/stats/orchestrator                   │  │
│  │  GET /dashboard/stats/platforms                      │  │
│  │  GET /dashboard/stats/campaigns                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │  BACKEND API (PASO 6.1)  │
              │  http://localhost:8000   │
              └──────────────────────────┘
```

**Data Flow:**
1. User accesses dashboard page
2. React Query hook triggers API call
3. Axios sends request to backend
4. Backend returns aggregated data
5. React Query caches response
6. Component renders data with charts
7. Auto-refresh every 30 seconds

---

## ✨ Features

### 🔐 Authentication
- Simple JWT-based local authentication
- Environment-configured credentials
- Protected routes with middleware
- Logout functionality

### 📊 Dashboard Overview
- 6 key metrics cards (videos, clips, publications, jobs, campaigns)
- 3 interactive charts:
  - Pie chart: Publications by status
  - Bar chart: Queue breakdown
  - Line chart: Weekly activity trend
- Real-time data refresh

### 📋 Queue Management
- Complete queue visibility
- Sortable table with:
  - Publish log ID
  - Clip ID
  - Platform
  - Status
  - Scheduled time
  - Request time
- Action buttons:
  - Force publish now
  - Retry failed
  - View clip details

### ⚙️ Orchestrator Monitoring
- Orchestrator status indicator
- Job statistics (pending, processing, completed)
- Saturation rate monitoring
- Recent 20 decisions log
- Recent 20 ledger events
- Actions by type chart

### 🎯 Platform Performance
- Per-platform metrics cards:
  - Posts today
  - Posts pending
  - Success rate
  - Average visual score
  - Clips ready
  - Last failure info
- Comparative charts:
  - Publications comparison
  - Success rate comparison
- Platform summary totals

### 📢 Campaign Management
- Campaign status overview
- Active campaigns list
- Clips breakdown by platform
- Campaign state (draft/scheduled/published)
- Rule engine recommendations button
- Publish campaign action

---

## 🛠 Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Framework | Next.js | 14.2.18 |
| Language | TypeScript | 5.6.3 |
| UI Library | React | 18.3.1 |
| Styling | TailwindCSS | 3.4.15 |
| Components | ShadCN/UI | Custom |
| State | TanStack Query | 5.59.16 |
| HTTP Client | Axios | 1.7.7 |
| Charts | Recharts | 2.13.3 |
| Auth | jsonwebtoken | 9.0.2 |
| Date Utils | date-fns | 4.1.0 |
| Testing | Jest + RTL | 29.7.0 |

---

## 📦 Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running (PASO 6.1)

### Steps

```bash
# Navigate to dashboard directory
cd /workspaces/stakazo/dashboard

# Install dependencies
npm install

# Configure environment variables
cp .env.local.example .env.local

# Edit .env.local with your settings
nano .env.local
```

### Environment Variables

Create `.env.local` file:

```env
# Backend API URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Dashboard Authentication
DASHBOARD_USER=admin
DASHBOARD_PASS=1234

# JWT Secret (change in production)
JWT_SECRET=stakazo-dashboard-secret-key-2025
```

---

## 🚀 Usage

### Development Mode

```bash
npm run dev
```

Access at: `http://localhost:3000`

Default credentials:
- Username: `admin`
- Password: `1234`

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm test -- --coverage
```

---

## 📄 Pages

### 1. `/` (Home)
- Redirects to `/dashboard`

### 2. `/login`
- JWT-based authentication
- Username/password form
- Token stored in localStorage

### 3. `/dashboard` (Overview)
- Main dashboard with all key metrics
- 6 statistics cards
- 3 interactive charts
- Auto-refresh every 30s

### 4. `/dashboard/queue`
- Publication queue table
- Real-time queue statistics
- Action buttons per item
- Platform icons and status badges

### 5. `/dashboard/orchestrator`
- Orchestrator health status
- Job statistics
- Recent decisions log (20)
- Recent ledger events (20)
- Actions by type chart

### 6. `/dashboard/platforms`
- 4 platform cards (Instagram, TikTok, YouTube, Facebook)
- Per-platform metrics
- Comparative charts
- Summary totals

### 7. `/dashboard/campaigns`
- Campaign statistics
- Active campaigns list
- Clips breakdown by platform
- Action buttons (recommendations, publish)

---

## 🔌 API Integration

### Connecting to Backend

The dashboard connects to the backend API created in **PASO 6.1**. Ensure the backend is running:

```bash
# Start backend (from backend directory)
cd /workspaces/stakazo/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints Used

| Endpoint | Method | Hook | Purpose |
|----------|--------|------|---------|
| `/dashboard/stats/overview` | GET | `useDashboardOverview` | Global statistics |
| `/dashboard/stats/queue` | GET | `useDashboardQueue` | Queue metrics |
| `/dashboard/stats/orchestrator` | GET | `useDashboardOrchestrator` | Orchestrator stats |
| `/dashboard/stats/platforms` | GET | `useDashboardPlatforms` | Platform breakdown |
| `/dashboard/stats/campaigns` | GET | `useDashboardCampaigns` | Campaign summary |

### Data Refresh Strategy

- **Auto-refresh**: Every 30 seconds
- **Manual refresh**: Component remount
- **Cache time**: 30 seconds (configurable)
- **Retry**: 1 attempt on failure

---

## 🧪 Testing

### Test Coverage

4 test suites with comprehensive coverage:

#### 1. Overview Test (`__tests__/overview.test.tsx`)
- ✅ Renders loading state
- ✅ Displays stats after loading
- ✅ Shows all 6 stat cards
- ✅ Validates card titles

#### 2. Queue Test (`__tests__/queue.test.tsx`)
- ✅ Renders queue statistics
- ✅ Displays queue table
- ✅ Shows action buttons
- ✅ Table has multiple rows

#### 3. Login Test (`__tests__/login.test.tsx`)
- ✅ Renders login form
- ✅ Shows error on invalid credentials
- ✅ Successful login flow
- ✅ Token storage

#### 4. API Mocks Test (`__tests__/api-mocks.test.tsx`)
- ✅ Fetches overview data
- ✅ Fetches queue data
- ✅ Handles errors gracefully

### Running Tests

```bash
# All tests
npm test

# Watch mode
npm run test:watch

# With coverage report
npm test -- --coverage
```

**Expected Result**: All 4 test suites pass ✅

---

## 📸 Screenshots

Visual previews of the dashboard (HTML mockups):

### 1. Overview Page
See: `screenshots/overview.html`

### 2. Queue Management
See: `screenshots/queue.html`

### 3. Platform Performance
See: `screenshots/platforms.html`

Open any HTML file in a browser to view the mockup.

---

## 📂 File Structure

```
dashboard/
├── app/
│   ├── dashboard/
│   │   ├── campaigns/
│   │   │   └── page.tsx          # Campaigns management
│   │   ├── orchestrator/
│   │   │   └── page.tsx          # Orchestrator monitoring
│   │   ├── platforms/
│   │   │   └── page.tsx          # Platform performance
│   │   ├── queue/
│   │   │   └── page.tsx          # Queue management
│   │   ├── layout.tsx            # Dashboard layout with sidebar
│   │   └── page.tsx              # Overview dashboard
│   ├── login/
│   │   └── page.tsx              # Login page
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Home redirect
├── components/
│   ├── ui/
│   │   ├── badge.tsx             # Status badges
│   │   ├── button.tsx            # Button component
│   │   ├── card.tsx              # Card containers
│   │   ├── chart-container.tsx   # Chart wrapper
│   │   ├── datetime-display.tsx  # Date formatter
│   │   ├── loader.tsx            # Loading spinner
│   │   ├── platform-icon.tsx     # Platform icons
│   │   ├── status-dot.tsx        # Status indicators
│   │   └── table.tsx             # Table component
│   └── providers.tsx             # React Query provider
├── hooks/
│   ├── use-auth.ts               # Auth hook
│   ├── use-dashboard-campaigns.ts
│   ├── use-dashboard-orchestrator.ts
│   ├── use-dashboard-overview.ts
│   ├── use-dashboard-platforms.ts
│   └── use-dashboard-queue.ts
├── lib/
│   ├── api.ts                    # API client & types
│   ├── auth.ts                   # JWT auth logic
│   ├── query-client.ts           # React Query config
│   └── utils.ts                  # Utility functions
├── __tests__/
│   ├── api-mocks.test.tsx
│   ├── login.test.tsx
│   ├── overview.test.tsx
│   └── queue.test.tsx
├── screenshots/
│   ├── overview.html
│   ├── queue.html
│   └── platforms.html
├── .env.local                    # Environment config
├── .eslintrc.json
├── .gitignore
├── jest.config.js
├── jest.setup.js
├── next.config.js
├── package.json
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json
└── README.md
```

**Total Files Created**: 50+

---

## 🔗 Integration with PASO 6.1

This dashboard is **fully integrated** with the backend API from PASO 6.1:

### Backend Endpoints (PASO 6.1)
✅ `GET /dashboard/stats/overview` → Overview page  
✅ `GET /dashboard/stats/queue` → Queue page  
✅ `GET /dashboard/stats/orchestrator` → Orchestrator page  
✅ `GET /dashboard/stats/platforms` → Platforms page  
✅ `GET /dashboard/stats/campaigns` → Campaigns page

### Data Types
All TypeScript interfaces match the Pydantic schemas from `backend/app/dashboard_api/schemas.py`:
- `OverviewStats`
- `QueueStats`
- `OrchestratorStats`
- `PlatformStats`
- `CampaignStats`

### Testing
Both frontend and backend have comprehensive test coverage:
- Backend: 10/10 tests passing (PASO 6.1)
- Frontend: 4/4 tests passing (PASO 6.2)

---

## 🎨 Design Philosophy

**Premium SaaS Style:**
- Clean, modern interface
- Gradient accents
- Smooth animations
- Responsive layouts
- Consistent spacing
- Professional typography
- Accessible color contrasts

**UX Principles:**
- Loading states for all async operations
- Error handling with clear messages
- Empty states with helpful text
- Action feedback (hover, click)
- Mobile-first responsive design

---

## 🚧 Future Enhancements

1. **Real-time Updates**: WebSocket integration
2. **Advanced Filtering**: Date ranges, platforms, status
3. **Export Functionality**: CSV/PDF reports
4. **Dark Mode**: Theme toggle
5. **Notifications**: Browser notifications for events
6. **User Management**: Multi-user support
7. **Audit Logs**: Complete action history
8. **Custom Dashboards**: User-configurable widgets

---

## 📝 License

Internal tool - Proprietary

---

## 👥 Support

For issues or questions:
1. Check backend logs: `backend/logs/`
2. Check browser console for frontend errors
3. Verify `.env.local` configuration
4. Ensure backend is running on port 8000

---

## ✅ Checklist

- [x] Next.js 14 with App Router
- [x] TypeScript configuration
- [x] TailwindCSS setup
- [x] ShadCN/UI components (8 components)
- [x] React Query integration
- [x] Axios API client
- [x] JWT authentication
- [x] 5 dashboard pages
- [x] Recharts integration
- [x] 4 Jest tests
- [x] README documentation
- [x] HTML screenshots (3)
- [x] Integration with PASO 6.1
- [x] Mobile responsive
- [x] Error handling
- [x] Loading states

**Status: 100% Complete ✅**

---

**Created**: November 2025  
**Version**: 1.0.0  
**PASO**: 6.2 - Dashboard UI Implementation
