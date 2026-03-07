'use client';

import { useEffect, useState } from 'react';

interface AuthLoadingScreenProps {
  message?: string;
}

export function AuthLoadingScreen({ message = 'Authenticating...' }: AuthLoadingScreenProps) {
  const [dots, setDots] = useState('');
  const [isVisible, setIsVisible] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    // Ensure component only renders on client
    setIsMounted(true);
    
    // Trigger fade-in animation
    const fadeTimer = setTimeout(() => setIsVisible(true), 10);

    const interval = setInterval(() => {
      setDots(prev => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);

    return () => {
      clearTimeout(fadeTimer);
      clearInterval(interval);
    };
  }, []);

  // Don't render anything until mounted on client
  if (!isMounted) {
    return null;
  }

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-950 to-black transition-opacity duration-500 ${
      isVisible ? 'opacity-100' : 'opacity-0'
    }`}>
      {/* Animated background grid */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0" style={{
          backgroundImage: `
            linear-gradient(rgba(251, 191, 36, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(251, 191, 36, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
          animation: 'grid-move 20s linear infinite'
        }} />
      </div>

      {/* Main content */}
      <div className="relative z-10 text-center">
        {/* Animated shield icon */}
        <div className="relative mb-8 inline-block">
          {/* Outer rotating ring */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-32 h-32 border-4 border-amber-500/30 rounded-full animate-spin-slow" 
                 style={{ animationDuration: '3s' }} />
          </div>
          
          {/* Middle pulsing ring */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-24 h-24 border-4 border-amber-400/40 rounded-full animate-pulse" />
          </div>

          {/* Shield icon */}
          <div className="relative w-32 h-32 flex items-center justify-center">
            <svg 
              className="w-16 h-16 text-amber-500 animate-pulse-slow" 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path 
                fillRule="evenodd" 
                d="M10 1.944A11.954 11.954 0 012.166 5C2.056 5.649 2 6.319 2 7c0 5.225 3.34 9.67 8 11.317C14.66 16.67 18 12.225 18 7c0-.682-.057-1.35-.166-2.001A11.954 11.954 0 0110 1.944zM11 14a1 1 0 11-2 0 1 1 0 012 0zm0-7a1 1 0 10-2 0v3a1 1 0 102 0V7z" 
                clipRule="evenodd" 
              />
            </svg>
          </div>

          {/* Scanning line effect */}
          <div className="absolute inset-0 flex items-center justify-center overflow-hidden rounded-full">
            <div 
              className="w-full h-1 bg-gradient-to-r from-transparent via-amber-400 to-transparent animate-scan"
              style={{ 
                animation: 'scan 2s ease-in-out infinite',
                transform: 'translateY(-50%)'
              }}
            />
          </div>
        </div>

        {/* Text */}
        <h2 className="text-2xl font-bold text-white mb-2">
          {message}
        </h2>
        <p className="text-amber-400 font-mono text-sm">
          Securing your session{dots}
        </p>

        {/* Progress indicators */}
        <div className="mt-8 flex justify-center space-x-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 bg-amber-500 rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>

      {/* CSS animations */}
      <style jsx>{`
        @keyframes grid-move {
          0% {
            transform: translate(0, 0);
          }
          100% {
            transform: translate(50px, 50px);
          }
        }

        @keyframes scan {
          0%, 100% {
            transform: translateY(-100%);
            opacity: 0;
          }
          50% {
            transform: translateY(0);
            opacity: 1;
          }
        }

        @keyframes pulse-slow {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.6;
          }
        }

        .animate-pulse-slow {
          animation: pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .animate-spin-slow {
          animation: spin 3s linear infinite;
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
