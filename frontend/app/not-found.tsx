import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-gray-900 dark:text-white">404</h1>
        </div>
        
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Page Not Found
        </h2>
        
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          The page you're looking for doesn't exist or has been moved.
          Let's get you back on track.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-yellow-500 hover:bg-yellow-600 transition-colors"
          >
            Go Home
          </Link>
          
          <Link
            href="/courses"
            className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 dark:border-gray-700 text-base font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Browse Courses
          </Link>
        </div>
        
        <div className="mt-12 text-sm text-gray-500 dark:text-gray-500">
          <p>Looking for something specific?</p>
          <p className="mt-2">
            Check out our{' '}
            <Link href="/faq" className="text-yellow-500 hover:text-yellow-600 underline">
              FAQ
            </Link>
            {' '}or{' '}
            <a 
              href="https://discord.gg/enMmUNq8jc" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-yellow-500 hover:text-yellow-600 underline"
            >
              join our Discord
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
