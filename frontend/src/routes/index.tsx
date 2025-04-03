import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import Login from '../pages/Login';
import Home from '../pages/Home';
import Dashboard from '../pages/Dashboard';
import Projects from '../pages/Projects';
import Users from '../pages/Users';
import Plans from '../pages/Plans';
import Prompts from '../pages/Prompts';
import Recipes from '../pages/Recipes';
import Settings from '../pages/Settings';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return !isAuthenticated ? children : <Navigate to="/dashboard" />;
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <Home />,
  },
  {
    path: '/login',
    element: (
      <PublicRoute>
        <Login />
      </PublicRoute>
    ),
  },
  {
    path: '/',
    element: (
      <PrivateRoute>
        <Layout />
      </PrivateRoute>
    ),
    children: [
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'projects',
        element: <Projects />,
      },
      {
        path: 'users',
        element: <Users />,
      },
      {
        path: 'plans',
        element: <Plans />,
      },
      {
        path: 'prompts',
        element: <Prompts />,
      },
      {
        path: 'recipes',
        element: <Recipes />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
]);

export default function Routes() {
  return <RouterProvider router={router} />;
} 