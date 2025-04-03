import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import StatsCard from '../components/StatsCard';
import Chart from '../components/Chart';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Sample data for charts
  const projectData = [
    { name: 'Jan', projects: 4 },
    { name: 'Feb', projects: 6 },
    { name: 'Mar', projects: 8 },
    { name: 'Apr', projects: 5 },
    { name: 'May', projects: 7 },
    { name: 'Jun', projects: 9 },
  ];

  const userData = [
    { name: 'Jan', users: 10 },
    { name: 'Feb', users: 15 },
    { name: 'Mar', users: 20 },
    { name: 'Apr', users: 25 },
    { name: 'May', users: 30 },
    { name: 'Jun', users: 35 },
  ];

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-700">
          Welcome back, {user?.first_name}! Here's what's happening with your projects.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="Total Projects"
          value="24"
          icon="fas fa-project-diagram"
          color="text-primary-600"
          trend={{ value: '+12%', isPositive: true }}
        />
        <StatsCard
          title="Active Users"
          value={isAdmin ? "156" : "1"}
          icon="fas fa-users"
          color="text-green-600"
          trend={{ value: '+8%', isPositive: true }}
        />
        <StatsCard
          title="Completed Tasks"
          value="89"
          icon="fas fa-check-circle"
          color="text-blue-600"
          trend={{ value: '+5%', isPositive: true }}
        />
        <StatsCard
          title="Pending Tasks"
          value="12"
          icon="fas fa-clock"
          color="text-yellow-600"
          trend={{ value: '-3%', isPositive: true }}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Chart
          title="Projects Overview"
          data={projectData}
          dataKey="projects"
          color="#0ea5e9"
        />
        {isAdmin && (
          <Chart
            title="User Growth"
            data={userData}
            dataKey="users"
            color="#10b981"
          />
        )}
      </div>
    </Layout>
  );
};

export default Dashboard; 