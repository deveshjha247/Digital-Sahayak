import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { AuthProvider, useAuth } from './context/AuthContext';

// Components
import Navbar from './components/Navbar';
import WhatsAppFAB from './components/WhatsAppFAB';

// Pages
import HomePage from './pages/HomePage';
import JobsPage from './pages/JobsPage';
import JobDetailPage from './pages/JobDetailPage';
import YojanaPage from './pages/YojanaPage';
import YojanaDetailPage from './pages/YojanaDetailPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';
import PaymentSuccessPage from './pages/PaymentSuccessPage';
import ProfilePreferencesPage from './pages/ProfilePreferencesPage';
import RecommendationsPage from './pages/RecommendationsPage';
import ContentDraftsPage from './pages/ContentDraftsPage';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

// Layout with Navbar
const MainLayout = ({ children }) => {
  return (
    <>
      <Navbar />
      {children}
      <WhatsAppFAB />
    </>
  );
};

// Auth Layout (no navbar)
const AuthLayout = ({ children }) => {
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes with Navbar */}
      <Route path="/" element={<MainLayout><HomePage /></MainLayout>} />
      <Route path="/jobs" element={<MainLayout><JobsPage /></MainLayout>} />
      <Route path="/jobs/:id" element={<MainLayout><JobDetailPage /></MainLayout>} />
      <Route path="/yojana" element={<MainLayout><YojanaPage /></MainLayout>} />
      <Route path="/yojana/:id" element={<MainLayout><YojanaDetailPage /></MainLayout>} />
      
      {/* Auth Routes without Navbar */}
      <Route path="/login" element={<AuthLayout><LoginPage /></AuthLayout>} />
      <Route path="/register" element={<AuthLayout><RegisterPage /></AuthLayout>} />
      
      {/* Protected Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <MainLayout><DashboardPage /></MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute>
          <MainLayout><ProfilePreferencesPage /></MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/recommendations" element={
        <ProtectedRoute>
          <MainLayout><RecommendationsPage /></MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/admin" element={
        <ProtectedRoute>
          <MainLayout><AdminPage /></MainLayout>
        </ProtectedRoute>
      } />
      <Route path="/payment-success" element={
        <ProtectedRoute>
          <MainLayout><PaymentSuccessPage /></MainLayout>
        </ProtectedRoute>
      } />
      
      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-center" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
