import React from 'react';
import { BadgeVariant, BadgeSize } from '@/lib/types';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md'
}: BadgeProps) {
  // Base styles
  const baseStyles = 'rounded-full inline-flex items-center justify-center font-medium';

  // Variant styles
  const variantStyles: Record<BadgeVariant, string> = {
    default: 'bg-gray-800 text-gray-100',
    success: 'bg-green-900 text-green-100',
    warning: 'bg-primary-900 text-primary-100'
  };

  // Size styles
  const sizeStyles: Record<BadgeSize, string> = {
    sm: 'px-3 py-1 text-xs',
    md: 'px-3 py-1 text-sm'
  };

  const combinedClassName = `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]}`.trim();

  return (
    <span className={combinedClassName}>
      {children}
    </span>
  );
}
