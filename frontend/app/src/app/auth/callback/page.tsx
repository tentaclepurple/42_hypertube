// frontend/app/src/app/auth/callback/page.tsx

'use client';

import { useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '../../context/authcontext';
import { useTranslation } from 'react-i18next';

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const processAuth = useRef(false);
  const { t } = useTranslation();

  useEffect(() => {
    if (processAuth.current) return;

    const token = searchParams.get('access_token');
    const userParam = searchParams.get('user');
    const error = searchParams.get('error');

    if (error) {
      router.push(`/login?error=${error}`);
      return;
    }
    
    if (token && userParam) {
      try {
        const userData = JSON.parse(decodeURIComponent(userParam));
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData));
        processAuth.current = true;
        login(token, userData);
        router.push('/');
      } catch (err) {
        router.push('/login?error=Error+processing+authentication+data');
      }
    } else {
      router.push('/login?error=Data+of+authentication+incomplete');
    }
  }, [searchParams, router, login]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-4">{t("login.processing")}</h2>
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
      </div>
    </div>
  );
}