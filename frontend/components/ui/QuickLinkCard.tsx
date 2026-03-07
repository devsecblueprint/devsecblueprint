import React from 'react';

export interface QuickLinkCardProps {
  icon: React.ReactNode;
  label: string;
  onClick?: () => void;
  href?: string;
  external?: boolean;
  ariaLabel?: string;
}

export function QuickLinkCard({
  icon,
  label,
  onClick,
  href,
  external = false,
  ariaLabel
}: QuickLinkCardProps) {
  // Base styles with minimum touch target size (44x44px), hover effects
  const baseStyles = `
    flex flex-col items-center justify-center gap-3
    min-h-[44px] min-w-[44px] p-6
    bg-white dark:bg-gray-900
    border border-gray-200 dark:border-gray-800
    rounded-2xl shadow-lg
    transition-all duration-200
    hover:scale-105 hover:shadow-xl
    hover:bg-gray-50 dark:hover:bg-gray-800
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
    cursor-pointer
  `.trim().replace(/\s+/g, ' ');

  // Icon wrapper ensures minimum 24px size
  const iconStyles = 'text-2xl min-w-[24px] min-h-[24px] text-gray-700 dark:text-gray-300';

  // Label styles
  const labelStyles = 'text-sm font-medium text-gray-900 dark:text-gray-100 text-center';

  // Determine the aria-label
  const accessibleLabel = ariaLabel || label;

  // If href is provided, render as a link
  if (href) {
    const linkProps = external
      ? {
          target: '_blank',
          rel: 'noopener noreferrer'
        }
      : {};

    return (
      <a
        href={href}
        className={baseStyles}
        aria-label={accessibleLabel}
        {...linkProps}
      >
        <div className={iconStyles}>{icon}</div>
        <span className={labelStyles}>{label}</span>
      </a>
    );
  }

  // Otherwise, render as a button
  return (
    <button
      type="button"
      onClick={onClick}
      className={baseStyles}
      aria-label={accessibleLabel}
    >
      <div className={iconStyles}>{icon}</div>
      <span className={labelStyles}>{label}</span>
    </button>
  );
}
