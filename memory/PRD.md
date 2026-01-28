# Digital Sahayak - Product Requirements Document

## Original Problem Statement
Digital Sahayak - India's First AI-Assisted "One-Click" Job & Yojana Apply Ecosystem. An automated system for government job alerts, yojana (scheme) applications with WhatsApp integration, Cashfree payment (₹20 service fee), and document management.

## User Personas
1. **Rural/Semi-urban Youth (18-40)**: Seeking government jobs, limited digital literacy
2. **Low-income Families**: Looking for government welfare schemes
3. **CSC Operators/Cyber Cafe Owners**: Processing bulk applications
4. **Admin/Operators**: Managing job/yojana listings and applications

## Core Requirements (Static)
- Job alerts from government sources
- Yojana (scheme) listings
- WhatsApp-based alerts and application assistance
- Payment collection (₹20 service fee + govt fees)
- Document storage (DigiLocker style)
- Hindi + English language support
- Mobile-first responsive design

---

## What's Been Implemented (December 2025)

### Phase 1: MVP (Completed)
- ✅ User authentication (JWT-based)
- ✅ Job alerts CRUD with categories (Railway, SSC, UPSC, Bank, Police, etc.)
- ✅ Yojana CRUD with categories (Welfare, Education, Agriculture, Housing, etc.)
- ✅ Application management system
- ✅ Cashfree payment integration (Production mode)
- ✅ WhatsApp webhook endpoints (MOCK mode)
- ✅ Admin dashboard with stats
- ✅ Document upload endpoints
- ✅ Landing page, Job/Yojana pages with filters
- ✅ User dashboard with applications

### Phase 2: AI & Scraper (Completed - December 2025)
- ✅ **Web Scraper** for sarkariresult.com and fastjobsearchers.com
  - Background task processing
  - Auto-categorization of jobs
  - State detection
  - Duplicate prevention
- ✅ **AI Job Matching** with OpenAI
  - Education level matching (10th, 12th, Graduate, PG)
  - Age-appropriate job filtering
  - State-based job recommendations
  - Category preferences
  - Match score calculation (0-100%)
  - AI-generated reasons in Hindi
- ✅ **Profile Preferences Page** (/profile)
  - Education level selector
  - State selector
  - Age input
  - Category preferences with checkboxes
- ✅ **AI Recommendations Page** (/recommendations)
  - Match score badges
  - AI-generated match reasons
  - User profile summary
  - Refresh functionality

### Phase 3: Custom URLs & Content Management (Completed - December 2025)
- ✅ **SEO-Friendly Custom URLs**
  - Slug generation from title (e.g., /br/bpsc-70th-combined-exam-2025)
  - State prefix support (br/, jh/, up/, etc.)
  - Unique slug enforcement
  - Both ID and slug access for jobs/yojana
- ✅ **Content Draft Queue System**
  - Scraped content saved to draft queue for review
  - Admin can edit content before publishing
  - AI Rewrite feature for copyright-safe content
  - Meta description and highlights support
  - Publish workflow from drafts to live
- ✅ **Content Drafts Page** (/admin/content-drafts)
  - View pending/published drafts
  - Edit dialog with all fields
  - AI Rewrite button
  - Publish and Delete actions
- ✅ **Enhanced Job/Yojana Models**
  - slug, meta_description, highlights fields
  - source_url for reference
  - is_rewritten flag
  - content_type (job, result, admit_card, syllabus)

### Phase 5: Backend Refactoring & Modular Architecture (Completed - January 2026)
- ✅ **Modular Directory Structure**
  - `config/` - Centralized configuration (settings.py, database.py)
  - `models/` - All Pydantic schemas organized
  - `routes/` - Separate route files by feature (auth, jobs, yojana, applications, payments, AI, scraper, whatsapp, forms)
  - `services/` - Business logic (hybrid_matching.py, form_intelligence.py)
  - `middleware/` - Authentication and utilities
  - `utils/` - Helper functions
- ✅ **Hybrid Matching Engine** (`services/hybrid_matching.py`)
  - **Rule-based Matching**: Education, age, state, category field mappings
  - **Heuristic Scoring**: Pattern-based with learned weights
  - **Log-based Learning**: Learns from user actions (applied, ignored, saved)
  - **Confidence Scoring**: Match scores with Hindi + English explanations
  - Field mappings for Indian context (10th, 12th, Graduate, Bihar, UP, etc.)
- ✅ **Clean Architecture**
  - Separation of concerns
  - Easy to test and maintain
  - Scalable for future growth
  - Each route file < 200 lines
- ✅ **Database Abstraction**
  - Singleton pattern for connections
  - Clean startup/shutdown
  - Easy to switch implementations

### Phase 6: Form Intelligence System (Completed - January 2026)
- ✅ **Smart Field Classification** (`services/form_intelligence.py`)
  - Auto-detects 15+ field types (name, email, phone, Aadhar, PAN, etc.)
  - Hindi + English label support
  - Regex patterns for Indian documents
  - ML enhancement for ambiguous cases (optional)
- ✅ **Error Prediction Engine**
  - Pre-submission validation
  - Format checks (phone, email, Aadhar, PAN, pincode)
  - Pattern detection (capitalization, spaces, unusual patterns)
  - ML-based contextual error detection (optional)
  - Severity levels: high/medium/low
- ✅ **Auto-fill Suggestions**
  - Smart form completion from user profile
  - Field-to-profile mapping
  - Confidence scoring
- ✅ **Portal Training System**
  - Learns from historical form datasets
  - Portal-specific pattern recognition
  - Improves accuracy over time
  - Stores learned patterns in MongoDB
- ✅ **Form Intelligence API Endpoints**
  - `/forms/classify-field` - Classify single field
  - `/forms/predict-errors` - Validate entire form
  - `/forms/auto-fill` - Get suggestions
  - `/forms/smart-form-fill` - Complete intelligence
  - `/forms/train` - Train on datasets (Admin)
  - `/forms/validate-batch` - Batch validation
  - `/forms/training-stats` - Analytics (Admin)

### Phase 7: Apply AI Engine v1 - Productization (Completed - January 2026)
- ✅ **Versioned API** (`/api/v1/`)
  - Production-ready API for external use
  - Authentication with API keys
  - Credit-based usage tracking
  - Rate limiting per plan
- ✅ **API Key Management**
  - JWT bearer token authentication
  - Credit system (free/paid plans)
  - Usage analytics
  - Expiration handling
- ✅ **Monetization Ready**
  - Free tier: 1,000 calls/month
  - Startup: 50,000 calls/month ($49/month)
  - Business: 500,000 calls/month ($199/month)
  - Enterprise: Unlimited (custom pricing)
- ✅ **Apply AI Engine v1 Endpoints**
  - `POST /api/v1/match/job` - Job matching (1 credit)
  - `POST /api/v1/match/scheme` - Scheme matching (1 credit)
  - `POST /api/v1/match/batch` - Batch matching
  - `POST /api/v1/forms/classify` - Field classification (0.1 credit)
  - `POST /api/v1/forms/validate` - Form validation (1 credit)
  - `POST /api/v1/forms/autofill` - Auto-fill (0.5 credit)
  - `POST /api/v1/forms/smart-fill` - Complete form AI (2 credits)
  - `POST /api/v1/learn/feedback` - Learning feedback (free)
  - `GET /api/v1/analytics/usage` - Usage stats
  - `GET /api/v1/health` - Health check
- ✅ **Documentation**
  - Complete API documentation
  - Code examples (Python, JavaScript, cURL)
  - SaaS deployment guide
  - Monetization strategy

### Phase 4: Self-Learning AI System (Completed - January 2026)
- ✅ **Core AI Learning Engine** (`ai_learning_system.py`)
  - Learns from external AI responses (GitHub Copilot, ChatGPT, etc.)
  - Analyzes strengths/weaknesses and generates improved responses
  - Stores all learnings in MongoDB for continuous improvement
  - Calculates improvement scores (0-100%)
- ✅ **Project Context Understanding**
  - Automatically analyzes project structure (server.py, routes, models)
  - Understands Digital Sahayak domain (jobs, schemes, Indian govt systems)
  - Reads dependencies and tech stack
  - Context-aware responses specific to the project
- ✅ **Web Search Integration**
  - Real-time web search using DuckDuckGo (no API key required)
  - Search results caching (1 hour)
  - Webpage content extraction
  - Integrated into AI responses for current information
- ✅ **Smart Response Generation**
  - Uses past learnings for better outputs
  - Project-context aware
  - Optional web search for real-time data
  - Confidence scoring based on learnings applied
- ✅ **Batch Learning & Pattern Recognition**
  - Compare multiple AI responses simultaneously
  - Identify best practices automatically
  - Project-specific insights extraction
- ✅ **Enhanced Job Matching**
  - Learns from external AI suggestions
  - Web search for job eligibility criteria
  - Improved match reasoning in Hindi
- ✅ **AI Learning API Endpoints** (8 new endpoints)
  - `/ai/learn-from-external` - Learn from any AI
  - `/ai/generate-smart` - Context-aware generation
  - `/ai/web-search` - Search the web
  - `/ai/analyze-project` - Project structure analysis
  - `/ai/project-context` - Get AI's knowledge
  - `/ai/learning-stats` - Statistics dashboard
  - `/ai/batch-compare` - Multi-AI comparison
  - `/ai/improve-job-matching` - Better recommendations
- ✅ **AI Learning UI** (/ai-learning)
  - Learn from AI tab with web search option
  - Smart generation with confidence scores
  - Web search interface
  - Learning statistics dashboard
  - Analysis visualization (strengths/weaknesses)

### Design System
- ✅ Sahayak Saffron (Primary), Ashoka Navy (Secondary), Kisan Green (Accent)
- ✅ Outfit + Noto Sans fonts with Hindi support
- ✅ Ticket-style job cards
- ✅ WhatsApp green integration

### Integrations
- ✅ Cashfree Payment Gateway (PRODUCTION)
- ✅ WhatsApp Cloud API (MOCK - ready for real integration)
- ✅ OpenAI GPT API (OPTIONAL - only for advanced features, not required)
- ✅ DuckDuckGo Web Search (OPTIONAL - for real-time information)
- ✅ Custom AI Engine (PRIMARY - built from scratch, no dependencies)

### Database Collections
- ✅ users, jobs, yojana, applications, payments
- ✅ content_drafts (for scraper queue)
- ✅ ai_learning_history (stores all AI learnings)
- ✅ ai_improvements (batch learning patterns)
- ✅ ai_project_context (project structure analysis)
- ✅ ai_web_search_cache (cached search results)
- ✅ matching_logs (user behavior tracking)
- ✅ matching_rules (dynamic rule weights)
- ✅ matching_heuristics (learned patterns)
- ✅ ml_patterns (success patterns)
- ✅ form_training_data (portal learnings)
- ✅ api_keys (Apply AI Engine authentication)
- ✅ api_usage (API usage tracking)

---

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] WhatsApp Cloud API real integration with user's Meta credentials
- [ ] Automated scraping scheduler (cron job every 6 hours)
- [ ] OTP-based phone verification
- [ ] Apply AI Engine v1 SaaS beta launch
- [ ] API key management dashboard

### P1 (High Priority)
- [ ] Document verification and storage with preview
- [ ] Bulk application processing for operators
- [ ] Result/notification system
- [ ] Email notifications
- [ ] Python & JavaScript SDKs for Apply AI Engine
- [ ] Customer portal for API users

### P2 (Medium Priority)
- [ ] Multi-language support (10+ regional languages)
- [ ] Browser extension for auto-fill
- [ ] Mobile app (React Native)
- [ ] API for CSCs/Cyber Cafes
- [ ] Voice input support
- [ ] OCR for form fields (image-based detection)
- [ ] GraphQL API for Apply AI Engine
- [ ] White-label solution for enterprises

### Phase 8: SaaS Launch & Scale
- [ ] **Beta Launch** 
  - Select partner onboarding
  - Free beta access with limits
  - Feedback collection
- [ ] **Public Launch** 
  - Open API access
  - Payment gateway for subscriptions
  - Marketing campaign
  - Support infrastructure
- [ ] **Scale Phase** 
  - Enterprise features
  - White-label options
  - Regional data centers
  - Advanced analytics dashboard
- 
---

## Next Tasks List
1. Configure WhatsApp Cloud API with real credentials, httpx (web requests)
- **Frontend**: React 19, shadcn/ui, Tailwind CSS
- **Payment**: Cashfree (Production)
- **Messaging**: WhatsApp Cloud API (MOCK)
- **AI**: OpenAI GPT API (GPT-3.5-turbo)
- **Search**: DuckDuckGo HTML search
- **Self-Learning AI**: Custom implementation with project context awareness
- **Hosting**: Digital Ocean Droplet

## Key Features Summary
1. **Job & Yojana Management**: Complete CRUD with admin controls
2. **Hybrid AI Matching**: Rule + Heuristics + ML + Log Learning
3. **Form Intelligence**: Field classification, error prediction, auto-fill
4. **Web Scraping**: Automated job scraping with draft queue
5. **Content Management**: SEO-friendly URLs, meta descriptions
6. **Payment Integration**: Cashfree for service fees
7. **WhatsApp Alerts**: Notification system (MOCK ready)
8. **Custom AI Engine**: Built from scratch, no external dependencies
9. **Behavioral Learning**: Learns from user interactions
10. **Apply AI Engine v1**: Productized API ready for SaaS
11. **Modular Architecture**: Scalable, maintainable codebase

## Digital Sahayak AI Capabilities (Custom Built)
- **Hybrid Matching**: Combines rules, heuristics, and learning
- **No External Dependencies**: Works without OpenAI/ChatGPT
- **Indian Context**: Optimized for Aadhar, PAN, Hindi, regional data
- **Behavioral Learning**: Learns from user actions (applied/ignored/saved)
- **Form Intelligence**: 15+ field types, error prediction, auto-fill
- **Pattern Recognition**: Success patterns from user behavior
- **Confidence Scoring**: Match scores with explanations
- **Portal Training**: Learns from government portal datasets
- **Continuous Improvement**: Gets smarter with every interaction
- **API Ready**: Productized as Apply AI Engine v1 for SaaS
---

## Technical Stack
- **Backend**: FastAPI (modular architecture), MongoDB, Motor (async), BeautifulSoup (scraping)
- **AI Engine**: Custom Digital Sahayak AI (no external AI dependencies)
  - Hybrid Matching Engine (Rule + Heuristics + ML + Log Learning)
  - Form Intelligence System (Field classification, error prediction)
  - Behavioral learning from user interactions
- **Frontend**: React 19, shadcn/ui, Tailwind CSS
- **Payment**: Cashfree (Production)
- **Messaging**: WhatsApp Cloud API (MOCK)
- **Optional**: OpenAI GPT API (for advanced features only, not required for core functionality)
- **Hosting**: Digital Ocean Droplet

## Admin Credentials
- Phone: 6200184827
- Password: admin123
