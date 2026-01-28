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

### Backend (FastAPI + MongoDB)
- ✅ User authentication (JWT-based)
- ✅ Job alerts CRUD with categories (Railway, SSC, UPSC, Bank, Police, etc.)
- ✅ Yojana CRUD with categories (Welfare, Education, Agriculture, Housing, etc.)
- ✅ Application management system
- ✅ Cashfree payment integration (Production mode)
- ✅ WhatsApp webhook endpoints (MOCK mode)
- ✅ Admin dashboard with stats
- ✅ Document upload endpoints

### Frontend (React + shadcn/ui)
- ✅ Landing page with hero, features, stats sections
- ✅ Job listings page with search/filter
- ✅ Yojana listings page with search/filter
- ✅ Job/Yojana detail pages with apply functionality
- ✅ User registration/login
- ✅ User dashboard with applications
- ✅ Admin dashboard for managing content
- ✅ WhatsApp FAB on all pages
- ✅ Payment success/failure pages
- ✅ Mobile responsive design

### Design System
- ✅ Sahayak Saffron (Primary), Ashoka Navy (Secondary), Kisan Green (Accent)
- ✅ Outfit + Noto Sans fonts with Hindi support
- ✅ Ticket-style job cards
- ✅ WhatsApp green integration

### Integrations
- ✅ Cashfree Payment Gateway (PRODUCTION)
- ✅ WhatsApp Cloud API (MOCK - ready for real integration)

---

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] WhatsApp Cloud API real integration with user's Meta credentials
- [ ] Web scraping module for auto-fetching jobs from Sarkari Result, etc.
- [ ] OTP-based phone verification

### P1 (High Priority)
- [ ] AI-assisted form auto-fill (GitHub Copilot SDK)
- [ ] Document verification and storage
- [ ] Bulk application processing for operators
- [ ] Result/notification system
- [ ] Email notifications

### P2 (Medium Priority)
- [ ] Multi-language support (regional languages)
- [ ] Browser extension for auto-fill
- [ ] Mobile app (React Native)
- [ ] API for CSCs/Cyber Cafes

### P3 (Nice to Have)
- [ ] AI chatbot for assistance
- [ ] Voice-based assistance
- [ ] Offline mode support

---

## Next Tasks List
1. Configure WhatsApp Cloud API with real credentials
2. Build web scraper for government job portals
3. Implement OTP verification for registration
4. Add document upload with preview
5. Create operator bulk processing interface
6. Add result/admit card alert system

---

## Technical Stack
- **Backend**: FastAPI, MongoDB, Motor (async)
- **Frontend**: React 19, shadcn/ui, Tailwind CSS
- **Payment**: Cashfree (Production)
- **Messaging**: WhatsApp Cloud API (MOCK)
- **Hosting**: Digital Ocean Droplet

## Admin Credentials
- Phone: 6200184827
- Password: admin123
