'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Something went wrong
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          We couldn't load the curriculum page. Please try again.
        </p>
        <button
          onClick={reset}
          className="px-6 py-3 bg-primary-400 text-gray-900 rounded-lg font-semibold hover:bg-primary-500 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
