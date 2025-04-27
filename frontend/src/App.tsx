import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import FreeTrial from './pages/FreeTrial';
import Dashboard from './pages/Dashboard';
import Prompts from './pages/Prompts';
import Projects from './pages/Projects';
import ProjectDetails from './pages/ProjectDetails';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Recipes from './pages/Recipes';
import Users from './pages/Users';
import Settings from './pages/Settings';

// Create a component for the AppRoutes
const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        {/* Root Route */}
        <Route path="/" element={<Home />} />

        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/free-trial" element={<FreeTrial />} />

        {/* Base Protected Routes (Available to all authenticated users) */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects"
          element={
            <ProtectedRoute>
              <Projects />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id"
          element={
            <ProtectedRoute>
              <ProjectDetails />
            </ProtectedRoute>
          }
        />

        {/* Admin Only Routes */}
        <Route
          path="/prompts"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Prompts />
            </ProtectedRoute>
          }
        />
        <Route
          path="/products"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Products />
            </ProtectedRoute>
          }
        />
        <Route
          path="/products/detail/:id"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <ProductDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/recipes"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Recipes />
            </ProtectedRoute>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Users />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Settings />
            </ProtectedRoute>
          }
        />
        
        {/* Catch-all Route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
};

export default App;
