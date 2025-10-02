'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '../context/authcontext';
import { parsedError } from '../ui/error/parsedError';
import Link from 'next/link';
import { Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorS, setErrorS] = useState<string[] | null>(null);
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const router = useRouter();
  const { t } = useTranslation();

  useEffect(() => {
    const errorParam = searchParams.get('error');
    if (errorParam) {
      setError(decodeURIComponent(errorParam));
    }
  }, [searchParams]);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const errorMap: Record<string, string> = {
    "Invalid username or password": "login.errors.invalidCredentials",
    "Error processing authentication data": "login.errors.processingData",
    "Data of authentication incomplete": "login.errors.incompleteData",
  };
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setErrorS(null);
    setLoading(true);

    try {
      const formData = new URLSearchParams()
      formData.append('grant_type', 'password');
      formData.append('username', username);
      formData.append('password', password);
      formData.append('scope', '');

      const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      if (!response.ok) {
        const errorData = parsedError(await response.json());
        setErrorS(errorData);
        throw new Error(errorData.join(', '));
      }
      
      const data = await response.json();
      
      login(data.access_token, data.user);
      router.push('/');
    } catch (error) {
      setErrorS(error instanceof Error ? [error.message] : [String(error)]);
    } finally {
      setLoading(false);
    } 
  }

  const handleLogin = (provider: string) => {
    window.location.href = `${process.env.NEXT_PUBLIC_URL}/api/v1/auth/oauth/${provider}`;
  };

  return (
    <div className="text-white max-w-md mx-auto p-6 ">
      {loading && (
        <div className="text-center mb-4 py-2">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded space-y-1">
          {t(errorMap[error]) || error}
        </div>
      )}
      {errorS && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded space-y-1">
          {errorS.map((err, index) => (
            <div key={index}>{err}</div>
          ))}
        </div>
      )}
      <form onSubmit={handleSubmit} className="mt-6 mb-6">
        <div className="space-y-4">
          <div>
            <label htmlFor='username' className="block text-sm font-medium mb-1">
              {t("login.username")}
            </label>
            <input
              type='text'
              id='username'
              name='username'
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded"
              required
            />
          </div>
          <div>
            <label htmlFor='password' className="block text-sm font-medium mb-1">
              {t("login.password")}
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                id='password'
                name='password'
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                required
              />
              <button 
                type="button" 
                className="absolute right-2 top-2"
                onClick={togglePasswordVisibility}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20}/>}
              </button>
            </div>
          </div>
          <div className='flex items-center justify-center'>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition duration-200"
            >
              {loading ? t("login.loggingIn") : t("login.submit")}
            </button>
            <p className='text-blue-600 hover:underline ml-4'>
              <Link href="/forgot-password">{t("login.forgotPassword")}</Link>
            </p>
          </div>
        </div>
      </form>
      
      <div className="space-y-3 max-w-xs mx-auto mt-20"> 
        <button
          onClick={() => handleLogin('42')}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded transition duration-200"
        >
          {t("login.42Login")}
        </button>
        
        <button
          onClick={() => handleLogin('google')}
          className="w-full py-2 px-4 bg-red-600 hover:bg-red-700 text-white rounded transition duration-200"
        >
          {t("login.googleLogin")}
        </button>
        
        <button
          onClick={() => handleLogin('github')}
          className="w-full py-2 px-4 bg-gray-700 hover:bg-gray-800 text-white rounded transition duration-200"
        >
          {t("login.githubLogin")}
        </button>
      </div>
      
      <div className="text-center mt-10">
        <p className="text-gray-400">
          {t("login.noAccount")} <Link href="/register" className="text-blue-400 hover:text-blue-300">{t("login.registerHere")}</Link>
        </p>
      </div>
    </div>
  );
}