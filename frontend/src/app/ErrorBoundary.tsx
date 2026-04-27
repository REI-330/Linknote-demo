import { Component, type ErrorInfo, type ReactNode } from "react";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  error: Error | null;
  errorInfo: ErrorInfo | null;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    error: null,
    errorInfo: null,
  };

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("LinkNote frontend crashed", error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground p-6">
        <div className="max-w-xl w-full space-y-4">
          <h1 className="text-2xl font-bold">前端发生运行时错误</h1>
          <p className="text-muted-foreground">
            {this.state.error.message || "Unknown error"}
          </p>
          {this.state.errorInfo?.componentStack && (
            <pre className="p-4 rounded-lg bg-muted text-xs overflow-auto max-h-64 whitespace-pre-wrap">
              {this.state.errorInfo.componentStack}
            </pre>
          )}
          <div className="flex gap-3">
            <button
              className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
              type="button"
              onClick={() => window.location.reload()}
            >
              刷新页面
            </button>
            <button
              className="px-4 py-2 rounded-md border text-sm font-medium hover:bg-muted transition-colors"
              type="button"
              onClick={() => window.history.back()}
            >
              返回上页
            </button>
          </div>
        </div>
      </div>
    );
  }
}
