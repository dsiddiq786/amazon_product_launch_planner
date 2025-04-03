import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const location = useLocation();

  // Base navigation items available to all users
  const baseNavigation = [
    { name: 'Dashboard', href: '/dashboard', icon: 'fas fa-home' },
    { name: 'Projects', href: '/projects', icon: 'fas fa-project-diagram' },
  ];

  // Admin-only navigation items
  const adminNavigation = [
    { name: 'Prompts', href: '/prompts', icon: 'fas fa-comment-alt' },
    { name: 'Products', href: '/products', icon: 'fas fa-box' },
    { name: 'Recipes', href: '/recipes', icon: 'fas fa-book' },
    { name: 'Users', href: '/users', icon: 'fas fa-users' },
    { name: 'Settings', href: '/settings', icon: 'fas fa-cog' },
  ];

  // Combine navigation items based on user role
  const navigation = user?.role === 'admin' 
    ? [...baseNavigation, ...adminNavigation]
    : baseNavigation;

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 z-20 lg:hidden"
          onClick={onClose}
        ></div>
      )}

      {/* Sidebar */}
      <div
        className={`w-64 bg-white border-r border-gray-200 flex-shrink-0 ${
          isOpen ? '' : 'hidden lg:block'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center h-14 flex-shrink-0 px-4 bg-blue-600">
            <span className="text-white text-base font-semibold">Product Launch Planner</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center px-2 py-1.5 text-sm font-medium rounded-md ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <i className={`${item.icon} mr-2 flex-shrink-0 h-4 w-4 ${
                    isActive ? 'text-blue-700' : 'text-gray-500'
                  }`}></i>
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User Info */}
          <div className="flex-shrink-0 p-3 border-t border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <i className="fas fa-user-circle text-xl text-gray-400"></i>
              </div>
              <div className="ml-2">
                <p className="text-sm font-medium text-gray-700">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500">
                  {user?.email}
                  <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-gray-100">
                    {user?.role === 'admin' ? 'Admin' : 'User'}
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar; 