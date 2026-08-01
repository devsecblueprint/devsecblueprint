import React from 'react';
import { render, screen } from '@testing-library/react';
import { ProgressRing } from '@/components/dashboard/ProgressRing';

describe('ProgressRing', () => {
  it('renders with default props', () => {
    render(<ProgressRing percentage={50} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toBeInTheDocument();
    expect(progressbar).toHaveAttribute('aria-valuenow', '50');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  it('displays the percentage text label', () => {
    render(<ProgressRing percentage={75} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('clamps percentage below 0 to 0', () => {
    render(<ProgressRing percentage={-20} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('clamps percentage above 100 to 100', () => {
    render(<ProgressRing percentage={150} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '100');
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('handles NaN by treating as 0', () => {
    render(<ProgressRing percentage={NaN} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('handles Infinity by clamping to 100', () => {
    render(<ProgressRing percentage={Infinity} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('renders SVG with correct dimensions for custom size', () => {
    const { container } = render(<ProgressRing percentage={50} size={120} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '120');
    expect(svg).toHaveAttribute('height', '120');
  });

  it('applies custom className', () => {
    render(<ProgressRing percentage={50} className="my-custom-class" />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar.className).toContain('my-custom-class');
  });

  it('calculates correct stroke-dashoffset for 0%', () => {
    const size = 80;
    const strokeWidth = 8;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;

    const { container } = render(<ProgressRing percentage={0} />);
    const circles = container.querySelectorAll('circle');
    const progressCircle = circles[1];
    expect(progressCircle).toHaveAttribute('stroke-dashoffset', String(circumference));
  });

  it('calculates correct stroke-dashoffset for 100%', () => {
    const { container } = render(<ProgressRing percentage={100} />);
    const circles = container.querySelectorAll('circle');
    const progressCircle = circles[1];
    expect(progressCircle).toHaveAttribute('stroke-dashoffset', '0');
  });

  it('rounds displayed percentage for fractional values', () => {
    render(<ProgressRing percentage={33.7} />);
    expect(screen.getByText('34%')).toBeInTheDocument();
  });
});
