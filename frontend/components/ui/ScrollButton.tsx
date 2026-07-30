'use client';

import React from 'react';
import { Button } from '@/components/ui/Button';
import { ButtonVariant, ButtonSize } from '@/lib/types';

export interface ScrollButtonProps {
  targetId: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
  className?: string;
}

/**
 * ScrollButton component that smoothly scrolls to a target element on click.
 * Wraps the Button component and adds smooth scroll behavior.
 *
 * @param targetId - The ID of the target element to scroll to
 * @param variant - Visual style passed to Button
 * @param size - Size variant passed to Button
 * @param children - Button content
 * @param className - Additional CSS classes
 */
export function ScrollButton({
  targetId,
  variant = 'primary',
  size = 'md',
  children,
  className,
}: ScrollButtonProps) {
  const handleClick = () => {
    document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <Button
      variant={variant}
      size={size}
      className={className}
      onClick={handleClick}
    >
      {children}
    </Button>
  );
}
