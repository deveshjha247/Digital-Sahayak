# Digital Sahayak - Government Schemes & Job Portal

A comprehensive platform connecting citizens with government schemes and job opportunities through intelligent matching powered by AI.

## Features

### 🎯 Core Functionalities
- **Yojana Discovery**: Browse and search government schemes (Yojanas)
- **Job Listings**: Explore available job opportunities
- **AI Job Matching**: Intelligent job recommendations based on user profile
- **Admin Dashboard**: Manage schemes and jobs content
- **User Authentication**: Secure login and registration
- **Profile Management**: User preferences and profile settings

### 🛠️ Tech Stack

**Frontend**
- React.js with modern component architecture
- Tailwind CSS for styling
- Shadcn UI components for consistent design
- React Router for navigation

**Backend**
- Python Flask server
- OpenAI GPT API for AI-powered matching
- RESTful API architecture

**Tools & Libraries**
- Node.js for frontend build process
- Webpack for module bundling
- Git for version control

## Project Structure

```
Digital-Sahayak/
├── frontend/              # React.js application
│   ├── public/           # Static assets
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── context/      # Context API (Auth)
│   │   ├── hooks/        # Custom React hooks
│   │   └── lib/          # Utility functions
│   └── plugins/          # Webpack and build plugins
├── backend/              # Python Flask server
│   ├── server.py        # Main application
│   └── requirements.txt  # Python dependencies
├── memory/              # Documentation and PRD
└── tests/              # Test files
```

## Getting Started

### Prerequisites
- Node.js (v14+)
- Python 3.8+
- npm or yarn

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python server.py
```

## Environment Variables

Create a `.env` file in the backend directory:

```
OPENAI_API_KEY=your_openai_key_here
FLASK_ENV=development
```

## Pages & Routes

- **Home**: Landing page with scheme and job highlights
- **Login/Register**: User authentication
- **Yojana Page**: Browse government schemes
- **Jobs Page**: View available job listings
- **Job Details**: Detailed job information with AI matching
- **Dashboard**: User dashboard with recommendations
- **Admin Page**: Content management for schemes and jobs
- **Profile**: User profile and preferences

## Development Notes

- The project uses Context API for state management (Authentication)
- UI components are built with Shadcn and styled with Tailwind CSS
- Backend provides RESTful endpoints for data management
- AI matching uses OpenAI's GPT models for intelligent recommendations

## Contributors

This project is a collaborative effort by:
- **Devesh Kumar Jha** (@deveshkumarjha1)
- **Devesh Jha** (@deveshjha247)

We welcome contributions from the community!

## License

This project is developed for public benefit.
