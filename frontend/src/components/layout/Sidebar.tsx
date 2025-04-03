import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  UserGroupIcon,
  DocumentDuplicateIcon,
  CogIcon,
  ChartBarIcon,
  CommandLineIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Projects', href: '/projects', icon: DocumentDuplicateIcon },
  { name: 'Users', href: '/users', icon: UserGroupIcon },
  { name: 'Plans', href: '/plans', icon: ChartBarIcon },
  { name: 'Prompts', href: '/prompts', icon: CommandLineIcon },
  { name: 'Recipes', href: '/recipes', icon: BookOpenIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
];

export function Sidebar() {
  const { user } = useAuth();

  return (
    <div className="hidden lg:flex lg:flex-shrink-0">
      <div className="flex flex-col w-64">
        <div className="flex flex-col flex-grow bg-gray-800 pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4">
            <img
              className="h-8 w-auto"
              src="/logo.svg"
              alt="Product Launch Planner"
            />
          </div>
          <nav className="mt-5 flex-1 flex flex-col divide-y divide-gray-700 overflow-y-auto" aria-label="Sidebar">
            <div className="px-2 space-y-1">
              {navigation.map((item) => {
                // Hide Users and Plans sections from non-admin users
                if (!user?.role?.includes('admin') && ['Users', 'Plans'].includes(item.name)) {
                  return null;
                }

                return (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    className={({ isActive }) =>
                      clsx(
                        isActive
                          ? 'bg-gray-900 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white',
                        'group flex items-center px-2 py-2 text-sm font-medium rounded-md'
                      )
                    }
                  >
                    <item.icon
                      className="mr-3 flex-shrink-0 h-6 w-6"
                      aria-hidden="true"
                    />
                    {item.name}
                  </NavLink>
                );
              })}
            </div>
          </nav>
        </div>
      </div>
    </div>
  );
} 