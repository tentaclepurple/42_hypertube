'use client';

import { useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '../../context/authcontext';

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const processAuth = useRef(false);

  useEffect(() => {

    if (processAuth.current) return;
    // Obtener parámetros de la URL
    const token = searchParams.get('access_token');
    const userParam = searchParams.get('user');
    const error = searchParams.get('error');

    if (error) {
      console.log('Error en la autenticación:', error);
      router.push(`/login?error=${error}`);
      return;
    }
    
    if (token && userParam) {
      try {
        // Decodificar y parsear los datos del usuario
        const userData = JSON.parse(decodeURIComponent(userParam));
        
        // Guardar token en localStorage
        localStorage.setItem('token', token);
        
        // Guardar datos del usuario en localStorage
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Marcar que se está procesando la autenticación
        processAuth.current = true;

        // Autenticar al usuario
        login(token, userData);
        
        console.log('Autenticación exitosa:', userData);
        
        // Redirigir a la página principal
        router.push('/');
      } catch (err) {
        console.log('Error procesando datos de autenticación:', err);
        router.push('/login?error=Error+procesando+datos+de+autenticación');
      }
    } else {
      router.push('/login?error=Datos+de+autenticación+incompletos');
    }
  }, [searchParams, router, login]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-4">Procesando inicio de sesión...</h2>
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
      </div>
    </div>
  );
}