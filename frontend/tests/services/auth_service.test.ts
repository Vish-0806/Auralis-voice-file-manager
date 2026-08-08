import { describe, it, expect, beforeEach } from 'vitest';
import { AuthService } from '../../src/services/auth/authService';

describe('AuthService', () => {
  let auth: AuthService;

  beforeEach(() => {
    auth = new AuthService();
  });

  it('should initialize as unauthenticated with no session or token', () => {
    expect(auth.isAuthenticated()).toBe(false);
    expect(auth.getToken()).toBeNull();
    expect(auth.getSession()).toBeNull();
  });

  it('should log in using placeholder and populate session payload', () => {
    auth.loginPlaceholder('user@test.com', 'Test User');
    expect(auth.isAuthenticated()).toBe(true);
    expect(auth.getToken()).toBe('mock-session-token-phase-16-6');
    expect(auth.getSession()).toEqual({
      userId: 'usr_placeholder',
      email: 'user@test.com',
      name: 'Test User',
    });
  });

  it('should clear sessions and tokens on logout', () => {
    auth.loginPlaceholder('user@test.com', 'Test User');
    auth.logout();
    expect(auth.isAuthenticated()).toBe(false);
    expect(auth.getToken()).toBeNull();
    expect(auth.getSession()).toBeNull();
  });
});
