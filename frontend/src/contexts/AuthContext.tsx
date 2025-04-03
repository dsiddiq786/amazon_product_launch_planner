import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../utils/api';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const validateToken = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Token validation failed:', error);
        localStorage.removeItem('token');
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    validateToken();
  }, []);

  const login = async (data: LoginData) => {
    try {
      const response = await api.post('/auth/login/json', data);
      if (!response.data.access_token) {
        throw new Error('Login failed - no access token received');
      }

      localStorage.setItem('token', response.data.access_token);
      
      // Verify the token by fetching user details
      const userResponse = await api.get('/auth/me');
      setUser(userResponse.data);
      setIsAuthenticated(true);
    } catch (error: any) {
      if (error.response?.status === 422) {
        throw new Error(error.response.data.detail || 'Invalid email or password');
      }
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      const response = await api.post('/auth/register', data);
      if (!response.data.access_token) {
        throw new Error('Registration failed - no access token received');
      }

      localStorage.setItem('token', response.data.access_token);
      
      // Verify the token by fetching user details
      const userResponse = await api.get('/auth/me');
      setUser(userResponse.data);
      setIsAuthenticated(true);
    } catch (error: any) {
      if (error.response?.status === 422) {
        throw new Error(error.response.data.detail || 'Validation error');
      }
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
  };

  // Don't render children until initial auth check is complete
  if (isLoading) {
    return null;
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext; 