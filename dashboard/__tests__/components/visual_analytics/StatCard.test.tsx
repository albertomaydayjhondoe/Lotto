/**
 * @jest-environment jsdom
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { StatCard } from '@/components/visual_analytics';
import { Video, TrendingUp, TrendingDown } from 'lucide-react';

describe('StatCard', () => {
  it('should render title and value', () => {
    render(<StatCard title="Total Clips" value={1234} />);

    expect(screen.getByText('Total Clips')).toBeInTheDocument();
    expect(screen.getByText('1234')).toBeInTheDocument();
  });

  it('should render subtitle when provided', () => {
    render(
      <StatCard title="Total Clips" value={1234} subtitle="Last 30 days" />
    );

    expect(screen.getByText('Last 30 days')).toBeInTheDocument();
  });

  it('should render icon when provided', () => {
    const { container } = render(
      <StatCard title="Total Clips" value={1234} icon={Video} />
    );

    // Icon is rendered
    const iconElement = container.querySelector('svg');
    expect(iconElement).toBeInTheDocument();
  });

  it('should render upward trend indicator', () => {
    render(
      <StatCard
        title="Total Clips"
        value={1234}
        trend={{ value: 12.5, direction: 'up' }}
      />
    );

    expect(screen.getByText('+12.5%')).toBeInTheDocument();
  });

  it('should render downward trend indicator', () => {
    render(
      <StatCard
        title="Total Clips"
        value={1234}
        trend={{ value: 5.2, direction: 'down' }}
      />
    );

    expect(screen.getByText('-5.2%')).toBeInTheDocument();
  });

  it('should apply blue color variant', () => {
    const { container } = render(
      <StatCard title="Clips" value={100} color="blue" />
    );

    expect(container.querySelector('.text-blue-600')).toBeInTheDocument();
  });

  it('should apply green color variant', () => {
    const { container } = render(
      <StatCard title="Clips" value={100} color="green" />
    );

    expect(container.querySelector('.text-green-600')).toBeInTheDocument();
  });

  it('should apply yellow color variant', () => {
    const { container } = render(
      <StatCard title="Clips" value={100} color="yellow" />
    );

    expect(container.querySelector('.text-yellow-600')).toBeInTheDocument();
  });

  it('should apply red color variant', () => {
    const { container } = render(
      <StatCard title="Clips" value={100} color="red" />
    );

    expect(container.querySelector('.text-red-600')).toBeInTheDocument();
  });

  it('should apply purple color variant', () => {
    const { container } = render(
      <StatCard title="Clips" value={100} color="purple" />
    );

    expect(container.querySelector('.text-purple-600')).toBeInTheDocument();
  });

  it('should render string values', () => {
    render(<StatCard title="Status" value="Active" />);

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('should handle large numbers', () => {
    render(<StatCard title="Total Views" value={1234567} />);

    expect(screen.getByText('1234567')).toBeInTheDocument();
  });

  it('should render with all props', () => {
    render(
      <StatCard
        title="Total Clips"
        value={1234}
        subtitle="Last 30 days"
        icon={Video}
        trend={{ value: 12.5, direction: 'up' }}
        color="blue"
      />
    );

    expect(screen.getByText('Total Clips')).toBeInTheDocument();
    expect(screen.getByText('1234')).toBeInTheDocument();
    expect(screen.getByText('Last 30 days')).toBeInTheDocument();
    expect(screen.getByText('+12.5%')).toBeInTheDocument();
  });

  it('should handle zero value', () => {
    render(<StatCard title="Clips" value={0} />);

    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('should handle negative values', () => {
    render(<StatCard title="Balance" value={-50} />);

    expect(screen.getByText('-50')).toBeInTheDocument();
  });

  it('should handle decimal values', () => {
    render(<StatCard title="Avg Score" value={85.5} />);

    expect(screen.getByText('85.5')).toBeInTheDocument();
  });
});
