import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { KpiCard } from '@/app/admin/components/KpiCard';

describe('KpiCard', () => {
  it('renders value with amber accent color', () => {
    render(<KpiCard label="Total Users" value={1234} />);
    const valueEl = screen.getByText('1234');
    expect(valueEl).toBeInTheDocument();
    expect(valueEl).toHaveClass('text-amber-500');
  });

  it('renders label text', () => {
    render(<KpiCard label="Active Learners" value={42} />);
    expect(screen.getByText('Active Learners')).toBeInTheDocument();
  });

  it('renders sublabel when provided', () => {
    render(
      <KpiCard label="Sessions" value={10} sublabel="Unique users online" />
    );
    expect(screen.getByText('Unique users online')).toBeInTheDocument();
  });

  it('does not render sublabel when not provided', () => {
    const { container } = render(<KpiCard label="Sessions" value={10} />);
    const sublabelEl = container.querySelector('.text-xs');
    expect(sublabelEl).toBeNull();
  });

  it('renders loading skeletons when isLoading is true', () => {
    const { container } = render(
      <KpiCard label="Total Users" value={0} isLoading={true} />
    );
    expect(container.querySelector('[aria-busy="true"]')).toBeInTheDocument();
    // Should not render the actual value
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('accepts string values', () => {
    render(<KpiCard label="Completion Rate" value="85%" />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  describe('when clickable', () => {
    it('calls onClick handler when clicked', () => {
      const onClick = jest.fn();
      render(<KpiCard label="Sessions" value={5} onClick={onClick} />);
      const card = screen.getByRole('button');
      fireEvent.click(card);
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('has role=button and is focusable', () => {
      const onClick = jest.fn();
      render(<KpiCard label="Sessions" value={5} onClick={onClick} />);
      const card = screen.getByRole('button');
      expect(card).toHaveAttribute('tabindex', '0');
    });

    it('activates on Enter key', () => {
      const onClick = jest.fn();
      render(<KpiCard label="Sessions" value={5} onClick={onClick} />);
      const card = screen.getByRole('button');
      fireEvent.keyDown(card, { key: 'Enter' });
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('activates on Space key', () => {
      const onClick = jest.fn();
      render(<KpiCard label="Sessions" value={5} onClick={onClick} />);
      const card = screen.getByRole('button');
      fireEvent.keyDown(card, { key: ' ' });
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('has minimum 44x44px touch target classes', () => {
      const onClick = jest.fn();
      render(<KpiCard label="Sessions" value={5} onClick={onClick} />);
      const card = screen.getByRole('button');
      expect(card.className).toContain('min-h-[44px]');
      expect(card.className).toContain('min-w-[44px]');
    });

    it('has hover ring and cursor-pointer classes', () => {
      const onClick = jest.fn();
      render(<KpiCard label="Sessions" value={5} onClick={onClick} />);
      const card = screen.getByRole('button');
      expect(card.className).toContain('hover:ring-2');
      expect(card.className).toContain('cursor-pointer');
    });
  });

  describe('when not clickable', () => {
    it('does not have role=button', () => {
      render(<KpiCard label="Total Users" value={100} />);
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('is not focusable', () => {
      const { container } = render(
        <KpiCard label="Total Users" value={100} />
      );
      const card = container.firstElementChild as HTMLElement;
      expect(card).not.toHaveAttribute('tabindex');
    });
  });
});
