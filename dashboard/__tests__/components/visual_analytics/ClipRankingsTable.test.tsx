/**
 * @jest-environment jsdom
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ClipRankingsTable } from '@/components/visual_analytics';
import type { ClipRanking } from '@/lib/visual_analytics/types';

describe('ClipRankingsTable', () => {
  const mockData: ClipRanking[] = [
    {
      rank: 1,
      clip_id: 'clip-123456789',
      score: 95.5,
      duration_seconds: 120,
    },
    {
      rank: 2,
      clip_id: 'clip-987654321',
      score: 89.2,
      duration_seconds: 90,
    },
    {
      rank: 3,
      clip_id: 'clip-abcdefghi',
      score: 85.0,
      duration_seconds: 150,
    },
  ];

  it('should render table with clips', () => {
    render(<ClipRankingsTable data={mockData} />);

    expect(screen.getByText('Rank')).toBeInTheDocument();
    expect(screen.getByText('Clip ID')).toBeInTheDocument();
    expect(screen.getByText('Score')).toBeInTheDocument();
    expect(screen.getByText('Duration')).toBeInTheDocument();
  });

  it('should render all clip rows', () => {
    render(<ClipRankingsTable data={mockData} />);

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('should render clip IDs', () => {
    render(<ClipRankingsTable data={mockData} />);

    expect(screen.getByText(/clip-123456789/)).toBeInTheDocument();
    expect(screen.getByText(/clip-987654321/)).toBeInTheDocument();
    expect(screen.getByText(/clip-abcdefghi/)).toBeInTheDocument();
  });

  it('should render scores', () => {
    render(<ClipRankingsTable data={mockData} />);

    expect(screen.getByText('95.5')).toBeInTheDocument();
    expect(screen.getByText('89.2')).toBeInTheDocument();
    expect(screen.getByText('85.0')).toBeInTheDocument();
  });

  it('should format duration correctly (MM:SS)', () => {
    render(<ClipRankingsTable data={mockData} />);

    expect(screen.getByText('02:00')).toBeInTheDocument(); // 120 seconds
    expect(screen.getByText('01:30')).toBeInTheDocument(); // 90 seconds
    expect(screen.getByText('02:30')).toBeInTheDocument(); // 150 seconds
  });

  it('should render trophy icon for rank 1', () => {
    const { container } = render(<ClipRankingsTable data={mockData} />);

    const trophyIcons = container.querySelectorAll('.text-yellow-500');
    expect(trophyIcons.length).toBeGreaterThan(0);
  });

  it('should limit rows based on maxRows prop', () => {
    const manyClips: ClipRanking[] = Array.from({ length: 20 }, (_, i) => ({
      rank: i + 1,
      clip_id: `clip-${i}`,
      score: 90 - i,
      duration_seconds: 120,
    }));

    render(<ClipRankingsTable data={manyClips} maxRows={5} />);

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.queryByText('6')).not.toBeInTheDocument();
  });

  it('should handle empty data', () => {
    render(<ClipRankingsTable data={[]} />);

    expect(screen.getByText('Rank')).toBeInTheDocument();
    expect(screen.getByText('Clip ID')).toBeInTheDocument();
  });

  it('should handle single clip', () => {
    const singleClip: ClipRanking[] = [
      {
        rank: 1,
        clip_id: 'clip-single',
        score: 100,
        duration_seconds: 60,
      },
    ];

    render(<ClipRankingsTable data={singleClip} />);

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText(/clip-single/)).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('01:00')).toBeInTheDocument();
  });

  it('should render progress bar for scores', () => {
    const { container } = render(<ClipRankingsTable data={mockData} />);

    const progressBars = container.querySelectorAll('.bg-purple-500');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  it('should format duration with leading zeros', () => {
    const clips: ClipRanking[] = [
      {
        rank: 1,
        clip_id: 'clip-1',
        score: 90,
        duration_seconds: 5, // Should be 00:05
      },
      {
        rank: 2,
        clip_id: 'clip-2',
        score: 85,
        duration_seconds: 65, // Should be 01:05
      },
    ];

    render(<ClipRankingsTable data={clips} />);

    expect(screen.getByText('00:05')).toBeInTheDocument();
    expect(screen.getByText('01:05')).toBeInTheDocument();
  });

  it('should handle long clip IDs by truncating', () => {
    const clips: ClipRanking[] = [
      {
        rank: 1,
        clip_id: 'clip-very-long-id-that-should-be-truncated-abcdefghijk',
        score: 90,
        duration_seconds: 120,
      },
    ];

    const { container } = render(<ClipRankingsTable data={clips} />);

    const clipIdCell = container.querySelector('.truncate');
    expect(clipIdCell).toBeInTheDocument();
  });

  it('should render default maxRows (10)', () => {
    const manyClips: ClipRanking[] = Array.from({ length: 20 }, (_, i) => ({
      rank: i + 1,
      clip_id: `clip-${i}`,
      score: 90 - i,
      duration_seconds: 120,
    }));

    render(<ClipRankingsTable data={manyClips} />);

    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.queryByText('11')).not.toBeInTheDocument();
  });

  it('should handle scores with different precisions', () => {
    const clips: ClipRanking[] = [
      { rank: 1, clip_id: 'c1', score: 95, duration_seconds: 60 },
      { rank: 2, clip_id: 'c2', score: 90.5, duration_seconds: 60 },
      { rank: 3, clip_id: 'c3', score: 87.123, duration_seconds: 60 },
    ];

    render(<ClipRankingsTable data={clips} />);

    expect(screen.getByText('95')).toBeInTheDocument();
    expect(screen.getByText('90.5')).toBeInTheDocument();
    expect(screen.getByText(/87\.1/)).toBeInTheDocument();
  });
});
