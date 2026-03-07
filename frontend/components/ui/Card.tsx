import React from 'react';
import { CardPadding } from '@/lib/types';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: CardPadding;
}

export function Card({
  children,
  className = '',
  padding = 'md'
}: CardProps) {
  // Base styles with rounded-2xl and shadow as per requirements 5.1.4, 5.1.5
  const baseStyles = 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-lg';

  // Padding variants
  const paddingStyles: Record<CardPadding, string> = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  const combinedClassName = `${baseStyles} ${paddingStyles[padding]} ${className}`.trim();

  return (
    <div className={combinedClassName}>
      {children}
    </div>
  );
}
