/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  LoadingSkeleton,
  LoadingState,
  ErrorState,
  EmptyState,
  NoPermissionState,
} from '@/components/visual_analytics';

describe('States Components', () => {
  describe('LoadingSkeleton', () => {
    it('should render loading skeleton', () => {
      const { container } = render(<LoadingSkeleton />);

      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('should render with custom height', () => {
      const { container } = render(<LoadingSkeleton height={200} />);

      const skeleton = container.querySelector('.h-\\[200px\\]');
      expect(skeleton).toBeInTheDocument();
    });
  });

  describe('LoadingState', () => {
    it('should render default loading message', () => {
      render(<LoadingState />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('should render custom loading message', () => {
      render(<LoadingState message="Loading analytics data..." />);

      expect(screen.getByText('Loading analytics data...')).toBeInTheDocument();
    });

    it('should render spinner icon', () => {
      const { container } = render(<LoadingState />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('ErrorState', () => {
    it('should render default error message', () => {
      render(<ErrorState />);

      expect(screen.getByText('An error occurred')).toBeInTheDocument();
      expect(
        screen.getByText('Unable to load data. Please try again.')
      ).toBeInTheDocument();
    });

    it('should render custom error message', () => {
      render(<ErrorState message="Network error" />);

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should render retry button', () => {
      render(<ErrorState />);

      const retryButton = screen.getByRole('button', { name: /try again/i });
      expect(retryButton).toBeInTheDocument();
    });

    it('should call onRetry when retry button is clicked', () => {
      const onRetry = jest.fn();
      render(<ErrorState onRetry={onRetry} />);

      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('should not render retry button when onRetry is not provided', () => {
      render(<ErrorState />);

      const retryButton = screen.queryByRole('button', { name: /try again/i });
      expect(retryButton).not.toBeInTheDocument();
    });

    it('should render AlertCircle icon', () => {
      const { container } = render(<ErrorState />);

      const icon = container.querySelector('.text-red-500');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('EmptyState', () => {
    it('should render default empty message', () => {
      render(<EmptyState />);

      expect(screen.getByText('No data available')).toBeInTheDocument();
      expect(
        screen.getByText('There is no data to display at this time.')
      ).toBeInTheDocument();
    });

    it('should render custom empty message', () => {
      render(<EmptyState message="No clips found" />);

      expect(screen.getByText('No clips found')).toBeInTheDocument();
    });

    it('should render action button when provided', () => {
      const action = {
        label: 'Create New',
        onClick: jest.fn(),
      };

      render(<EmptyState action={action} />);

      const actionButton = screen.getByRole('button', { name: /create new/i });
      expect(actionButton).toBeInTheDocument();
    });

    it('should call action.onClick when action button is clicked', () => {
      const action = {
        label: 'Create New',
        onClick: jest.fn(),
      };

      render(<EmptyState action={action} />);

      const actionButton = screen.getByRole('button', { name: /create new/i });
      fireEvent.click(actionButton);

      expect(action.onClick).toHaveBeenCalledTimes(1);
    });

    it('should not render action button when not provided', () => {
      render(<EmptyState />);

      const actionButton = screen.queryByRole('button');
      expect(actionButton).not.toBeInTheDocument();
    });

    it('should render Inbox icon', () => {
      const { container } = render(<EmptyState />);

      const icon = container.querySelector('.text-gray-400');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('NoPermissionState', () => {
    it('should render no permission message', () => {
      render(<NoPermissionState />);

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(
        screen.getByText(
          'You do not have permission to view this analytics section.'
        )
      ).toBeInTheDocument();
    });

    it('should render custom no permission message', () => {
      render(<NoPermissionState message="Admin access required" />);

      expect(screen.getByText('Admin access required')).toBeInTheDocument();
    });

    it('should render Shield icon', () => {
      const { container } = render(<NoPermissionState />);

      const icon = container.querySelector('.text-orange-500');
      expect(icon).toBeInTheDocument();
    });

    it('should render contact message', () => {
      render(<NoPermissionState />);

      expect(
        screen.getByText(/please contact your administrator/i)
      ).toBeInTheDocument();
    });
  });

  describe('Integration tests', () => {
    it('should render LoadingState then ErrorState', () => {
      const { rerender } = render(<LoadingState />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      rerender(<ErrorState message="Failed to load" />);
      expect(screen.getByText('Failed to load')).toBeInTheDocument();
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    it('should render LoadingState then EmptyState', () => {
      const { rerender } = render(<LoadingState />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      rerender(<EmptyState message="No results" />);
      expect(screen.getByText('No results')).toBeInTheDocument();
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    it('should render different states sequentially', () => {
      const { rerender } = render(<LoadingState />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      rerender(<ErrorState />);
      expect(screen.getByText('An error occurred')).toBeInTheDocument();

      const onRetry = jest.fn();
      rerender(<LoadingState />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      rerender(<EmptyState />);
      expect(screen.getByText('No data available')).toBeInTheDocument();
    });
  });
});
