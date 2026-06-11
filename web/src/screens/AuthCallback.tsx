/**
 * @file AuthCallback.tsx
 * @description Xử lý redirect từ Google OAuth.
 * Backend redirect về /auth/callback?code=... sau khi user đăng nhập Google.
 * Component này đọc query param `code`, gọi exchangeGoogleCode, cập nhật auth state rồi điều hướng về /.
 * Search tags: AuthCallback | exchangeGoogleCode | Google OAuth callback
 */

import { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '@/services/auth.service';
import { useAuth } from '@/hooks/useAuth';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { checkUserAuth } = useAuth();
  const called = useRef(false); // prevent StrictMode double-invoke

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const code = searchParams.get('code');
    if (!code) {
      navigate('/login', { replace: true });
      return;
    }

    authService.exchangeGoogleCode(code)
      .then(() => checkUserAuth())
      .then(() => navigate('/', { replace: true }))
      .catch(() => navigate('/login', { replace: true }));
  }, []);

  return (
    <div className="fixed inset-0 flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-slate-200 border-t-slate-800 rounded-full animate-spin" />
    </div>
  );
}