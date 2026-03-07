import React from 'react';
import { ButtonVariant, ButtonSize } from '@/lib/types';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
}

/**
 * Button component with multiple variants and sizes.
 * Ensures minimum 44x44px touch targets for accessibility.
 * 
 * @param variant - Visual style: 'primary' (amber), 'secondary' (gray), or 'ghost' (transparent)
 * @param size - Size variant: 'sm', 'md', or 'lg'
 * @param children - Button content
 * @param className - Additional CSS classes
 * @param props - Standard HTML button attributes
 */
export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  ...props
}: ButtonProps) {
  // Base styles
  const baseStyles = 'rounded-lg font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950';

  // Variant styles
  const variantStyles: Record<ButtonVariant, string> = {
    primary: 'bg-primary-400 text-gray-900 hover:bg-primary-500 focus:ring-primary-400',
    secondary: 'bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-700 focus:ring-gray-400 dark:focus:ring-gray-600',
    ghost: 'bg-transparent text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 focus:ring-gray-400 dark:focus:ring-gray-600',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 disabled:bg-red-400 disabled:cursor-not-allowed'
  };

  // Size styles - ensuring minimum 44x44px touch targets
  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'px-4 py-3 text-sm min-h-[44px]', // Increased padding for 44px minimum
    md: 'px-6 py-3 text-base min-h-[44px]',
    lg: 'px-8 py-4 text-lg min-h-[48px]'
  };

  const combinedClassName = `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`.trim();

  return (
    <button className={combinedClassName} {...props}>
      {children}
    </button>
  );
}
