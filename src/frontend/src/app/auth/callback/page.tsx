'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/api/client';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setUser, setToken } = useAuthStore();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');

        if (!code) {
          setError('No authorization code received');
          setIsLoading(false);
          return;
        }

        // Exchange code for tokens
        const response = await apiClient.githubCallback(code, state || '');

        if (response.data) {
          const { user, access_token, token_type } = response.data;

          // Store tokens
          setToken(access_token);
          localStorage.setItem('access_token', access_token);

          // Store user
          setUser(user);
          localStorage.setItem('user', JSON.stringify(user));

          // Redirect to home
          setTimeout(() => {
            router.push('/');
          }, 500);
        } else {
          setError(response.error || 'Authentication failed');
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Callback error:', err);
        setError('An error occurred during authentication');
        setIsLoading(false);
      }
    };

    handleCallback();
  }, [router, searchParams, setUser, setToken]);

  if (error) {
    return (
      <div className="auth-container">
        <div className="auth-box">
          <div className="auth-header">
            <h1>Authentication Failed</h1>
          </div>
          <div className="auth-content">
            <div className="error-message">
              <p>{error}</p>
            </div>
            <button
              onClick={() => router.push('/auth')}
              className="github-button"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-box">
        <div className="auth-header">
          <h1>Cloud OS</h1>
          <p>Authenticating...</p>
        </div>
        <div className="auth-content">
          <div className="loading-spinner" />
          <p>Please wait while we complete your authentication</p>
        </div>
      </div>
    </div>
  );
}
