# Product Launch Planner - Admin Panel

This is the admin panel frontend for the Product Launch Planner application. It's built with React, TypeScript, and Tailwind CSS.

## Features

- 📊 Real-time dashboard with analytics
- 👥 User management
- 🚀 Project tracking
- 💰 Plan management
- 🤖 Prompt management
- 📝 Recipe management
- ⚙️ System settings

## Tech Stack

- React 18 with TypeScript
- Vite for fast development and building
- TailwindCSS for styling
- React Router for navigation
- React Query for data fetching
- Chart.js for analytics
- Headless UI for accessible components

## Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── layout/       # Layout components (Header, Sidebar)
│   └── ui/          # UI components (buttons, cards, etc.)
├── contexts/         # React contexts (auth, theme, etc.)
├── hooks/           # Custom React hooks
├── pages/           # Page components
├── services/        # API services
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Development Guidelines

- Follow the component structure in `src/components`
- Use TypeScript for type safety
- Follow the established styling patterns with Tailwind CSS
- Write unit tests for critical components
- Document complex components and utilities

## API Integration

The admin panel communicates with the FastAPI backend. All API calls should:

- Use the `services` directory for API functions
- Handle errors appropriately
- Include proper authentication
- Use React Query for caching and state management

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

MIT
