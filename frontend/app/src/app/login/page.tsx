'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function Login() {
  const [error, setError] = useState<string | null>(null);
  const searchParams = useSearchParams();
  
  useEffect(() => {
    // Verificar si hay un mensaje de error en la URL
    const errorParam = searchParams.get('error');
    if (errorParam) {
      setError(decodeURIComponent(errorParam));
    }
  }, [searchParams]);

  // IMPORTANTE: Usar redirección directa en lugar de fetch
  const handleLogin = (provider: string) => {
    // Redireccionar directamente al endpoint OAuth del backend
    window.location.href = `http://localhost:8000/api/v1/auth/oauth/${provider}`;
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center">
      <div className="w-full max-w-md space-y-8 p-8 bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-6">HYPERTUBE</h1>
          
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}
        </div>
        
        <div className="space-y-4">
          <button
            onClick={() => handleLogin('42')}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded transition duration-200"
          >
            Iniciar sesión con 42
          </button>
          
          <button
            onClick={() => handleLogin('google')}
            className="w-full py-2 px-4 bg-red-600 hover:bg-red-700 text-white rounded transition duration-200"
          >
            Iniciar sesión con Google
          </button>
          
          <button
            onClick={() => handleLogin('github')}
            className="w-full py-2 px-4 bg-gray-700 hover:bg-gray-800 text-white rounded transition duration-200"
          >
            Iniciar sesión con GitHub
          </button>
        </div>
      </div>
    </main>
  );
}