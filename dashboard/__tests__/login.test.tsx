import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import LoginPage from '@/app/login/page'
import { auth } from '@/lib/auth'

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

jest.mock('@/lib/auth')

describe('Login Page', () => {
  it('renders login form', () => {
    render(<LoginPage />)

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows error on invalid credentials', async () => {
    ;(auth.login as jest.Mock).mockReturnValue(null)

    render(<LoginPage />)

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'wrong' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrong' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('successful login with valid credentials', async () => {
    ;(auth.login as jest.Mock).mockReturnValue('mock-token-123')
    ;(auth.setToken as jest.Mock).mockImplementation(() => {})

    render(<LoginPage />)

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'admin' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: '1234' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(auth.setToken).toHaveBeenCalledWith('mock-token-123')
    })
  })
})
