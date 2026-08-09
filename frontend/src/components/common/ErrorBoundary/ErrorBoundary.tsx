import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error inside ErrorBoundary:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="container py-5 text-center">
          <div className="card border-0 shadow-sm p-5 mx-auto" style={{ maxWidth: '500px' }}>
            <div className="text-danger mb-3">
              <i className="bi bi-exclamation-triangle fs-1"></i>
            </div>
            <h4 className="card-title text-secondary mb-2">Something went wrong</h4>
            <p className="text-muted small mb-4">
              An unexpected rendering error occurred. Please refresh or try again.
            </p>
            <button 
              className="btn btn-primary btn-sm"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
export default ErrorBoundary;
