export interface UserSession {
  userId: string;
  email: string;
  name: string;
}

export class AuthService {
  private session: UserSession | null = null;
  private token: string | null = null;

  public isAuthenticated(): boolean {
    return this.token !== null;
  }

  public getSession(): UserSession | null {
    return this.session;
  }

  public getToken(): string | null {
    return this.token;
  }

  public loginPlaceholder(email: string, name: string): void {
    // Memory-only authentication placeholder for Phase 16.6
    this.token = 'mock-session-token-phase-16-6';
    this.session = {
      userId: 'usr_placeholder',
      email,
      name,
    };
  }

  public logout(): void {
    this.session = null;
    this.token = null;
  }
}

export const authService = new AuthService();
export default authService;
