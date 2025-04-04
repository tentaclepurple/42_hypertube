'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '../context/authcontext';
import { parsedError } from '../ui/error/parsedError';
import Link from 'next/link';
import { Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/navigation';

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
  
  useEffect(() => {
    // Verificar si hay un mensaje de error en la URL
    const errorParam = searchParams.get('error');
    if (errorParam) {
      setError(decodeURIComponent(errorParam));
    }
  }, [searchParams]);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const loginData = { username, password };
    console.log('Sending JSON:', loginData);

    try {
      const formData = new URLSearchParams()
      formData.append('grant_type', 'password');
      formData.append('username', username);
      formData.append('password', password);
      formData.append('scope', '');

      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
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
      setError(error as string);
    }finally {
      setLoading(false);
    } 
  }

  // IMPORTANTE: Usar redirección directa en lugar de fetch
  const handleLogin = (provider: string) => {
    // NO usar fetch, sino redirección directa
    window.location.href = `http://localhost:8000/api/v1/auth/oauth/${provider}`;
  };

  return (
    <div className="text-white max-w-screen-lg mx-auto p-6">
      <div className="max-w-md mx-auto">
        {loading && (
          <div className="text-center mb-4 py-2">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
            <p className="mt-2">Loading...</p>
          </div>
        )}
        {error || errorS && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="mt-6 mb-6">
          <div className="space-y-4">
            <div>
              <label htmlFor='username' className="block text-sm font-medium mb-1">
                Username
              </label>
              <input
                type='text'
                id='username'
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                required
              />
            </div>
            <div>
              <label htmlFor='password' className="block text-sm font-medium mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id='password'
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
                {loading ? 'Logging in...' : 'Login'}
              </button>
              <p className='text-blue-600 hover:underline ml-4'>
                Forgot your password?
              </p>
            </div>
          </div>
        </form>
        
        <div className="space-y-3 max-w-xs mx-auto mt-20"> 
          <button
            onClick={() => handleLogin('42')}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded transition duration-200"
          >
            Login with 42
          </button>
          
          <button
            onClick={() => handleLogin('google')}
            className="w-full py-2 px-4 bg-red-600 hover:bg-red-700 text-white rounded transition duration-200"
          >
            Login with Google
          </button>
          
          <button
            onClick={() => handleLogin('github')}
            className="w-full py-2 px-4 bg-gray-700 hover:bg-gray-800 text-white rounded transition duration-200"
          >
            Login with GitHub
          </button>
        </div>
        
        <div className="text-center mt-10">
          <p className="text-gray-400">
            Don't have an account? <Link href="/register" className="text-blue-400 hover:text-blue-300">Register here</Link>
          </p>
        </div>
      </div>
    </div>
  );
}