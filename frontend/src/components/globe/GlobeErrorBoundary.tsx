"use client";

import { Component } from "react";
import type { ReactNode } from "react";

/**
 * Error boundary that catches the luma.gl WebGL initialization race condition.
 *
 * On first render, luma.gl's ResizeObserver can fire before the WebGL device
 * is ready, causing "Cannot read properties of undefined (reading
 * 'maxTextureDimension2D')". This boundary catches that error and retries
 * the render after a short delay, by which point the device is initialized.
 */
export class GlobeErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch() {
    // Retry after a short delay — the WebGL device will be ready.
    setTimeout(() => this.setState({ hasError: false }), 100);
  }

  render() {
    if (this.state.hasError) return null;
    return this.props.children;
  }
}
