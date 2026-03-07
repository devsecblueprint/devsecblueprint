# The DevSec Blueprint - Frontend

A modern, clean Next.js application for The DevSec Blueprint learning platform with GitHub OAuth authentication and progress tracking.

## Features

- 🎨 Clean, professional UI with light/dark theme support
- 🔐 GitHub OAuth authentication via AWS Lambda
- 📊 Progress tracking with DynamoDB backend
- 📝 Markdown-based content system
- 🎯 Fully responsive design
- ♿ Accessibility-focused components

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Access to the backend API Gateway URL

### Environment Setup

1. Copy the example environment file:

```bash
cp .env.example .env.local
```

2. Update `.env.local` with your API Gateway URL:

```bash
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com
```

> **Note**: The API URL should NOT include a trailing slash.

### Installation

Install dependencies:

```bash
npm install
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Building for Production

Build the application:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `NEXT_PUBLIC_API_URL` | API Gateway base URL | Yes | `https://api.example.com` |

## Project Structure

```
frontend/
├── app/                    # Next.js app router pages
│   ├── dashboard/         # Dashboard page (protected)
│   ├── learn/             # Learning content pages
│   ├── login/             # Login page
│   └── layout.tsx         # Root layout with providers
├── components/            # React components
│   ├── layout/           # Layout components (Navbar, Footer, Sidebar)
│   ├── ui/               # Reusable UI components
│   └── features/         # Feature-specific components
├── lib/                   # Utilities and hooks
│   ├── api.ts            # API client
│   ├── hooks/            # Custom React hooks
│   │   ├── useAuth.ts    # Authentication hook
│   │   └── useProgress.ts # Progress tracking hook
│   ├── types.ts          # TypeScript types
│   └── constants.ts      # App constants
├── content/              # Markdown content files
├── public/               # Static assets
└── styles/               # Global styles
```

## Authentication Flow

1. User clicks "Login with GitHub" on `/login`
2. Redirects to API Gateway `/auth/github/start`
3. Lambda redirects to GitHub OAuth
4. User authorizes on GitHub
5. GitHub redirects to `/auth/github/callback`
6. Lambda sets HttpOnly JWT cookie
7. Lambda redirects to `/dashboard`
8. Frontend verifies session via `/me` endpoint

## API Integration

The frontend communicates with the backend Lambda function via API Gateway:

- `GET /auth/github/start` - Initiate OAuth flow
- `GET /auth/github/callback` - Handle OAuth callback
- `GET /me` - Verify authentication
- `PUT /progress` - Save user progress

All API calls automatically include credentials (cookies) for authentication.

## Development

### Adding New Content

1. Create a markdown file in `content/{learning-path}/{topic}/`
2. Add frontmatter with required fields
3. Run `npm run generate` to create TSX pages
4. Content will be available at `/learn/{path}/{topic}/{section}`

### Using Authentication

```typescript
import { useAuth } from '@/lib/hooks/useAuth';

function MyComponent() {
  const { isAuthenticated, isLoading, userId, logout } = useAuth();
  
  if (isLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <div>Please log in</div>;
  
  return <div>Welcome, user {userId}!</div>;
}
```

### Saving Progress

```typescript
import { useProgress } from '@/lib/hooks/useProgress';

function LearningPage() {
  const { saveProgress, isSaving } = useProgress();
  
  const handleNext = async () => {
    const success = await saveProgress('page-id');
    if (success) {
      // Navigate to next page
    }
  };
  
  return <button onClick={handleNext} disabled={isSaving}>Next</button>;
}
```

## Troubleshooting

### Authentication Issues

- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check that cookies are enabled in your browser
- Ensure API Gateway has CORS configured for your domain
- Check browser console for error messages

### Progress Not Saving

- Verify you are logged in (check `/me` endpoint)
- Check network tab for failed API calls
- Ensure JWT cookie is being sent with requests
- Verify DynamoDB table permissions

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs)

## License

MIT
