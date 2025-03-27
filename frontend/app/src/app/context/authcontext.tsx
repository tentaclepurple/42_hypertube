'use client';
 
 import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
 import { useRouter } from 'next/navigation';
 
 export interface User {
   id: string;
   email: string;
   username: string;
   first_name?: string;
   last_name?: string;
   profile_picture?: string;
   birth_year?: number;
   gender?: string;
 }
 
 interface AuthContextType {
   user: User | null;
   isLoading: boolean;
   login: (token: string, userData: User) => void;
   logout: () => void;
   updateUser: (userData: Partial<User>) => void;
   isAuthenticated: boolean;
 }
 
 const AuthContext = createContext<AuthContextType | undefined>(undefined);
 
 export function AuthProvider({ children }: { children: ReactNode }) {
   const [user, setUser] = useState<User | null>(null);
   const [isLoading, setIsLoading] = useState(true);
   const router = useRouter();
 
   useEffect(() => {
     // Check if user is logged in on mount
     const token = localStorage.getItem('authToken');
     const storedUser = localStorage.getItem('user');
     
     if (token && storedUser) {
       try {
         setUser(JSON.parse(storedUser));
       } catch (error) {
         console.error('Error parsing user data:', error);
         localStorage.removeItem('authToken');
         localStorage.removeItem('user');
       }
     }
     
     setIsLoading(false);
   }, []);
 
   const login = (token: string, userData: User) => {
     localStorage.setItem('authToken', token);
     localStorage.setItem('user', JSON.stringify(userData));
     setUser(userData);
   };
 
   const logout = () => {
     // Hacer una petición al backend para invalidar el token
     const token = localStorage.getItem('authToken');
     if (token) {
       fetch('http://localhost:8000/api/v1/auth/logout', {
         method: 'POST',
         headers: {
           'Authorization': `Bearer ${token}`,
         },
       }).catch(error => console.error('Error during logout:', error));
     }
     
     // Limpieza local
     localStorage.removeItem('authToken');
     localStorage.removeItem('user');
     setUser(null);
     router.push('/login');
   };

   const updateUser = (userData: Partial<User>) => {
      setUser((prevUser) => {
        if (!prevUser) return null;
        const newUser = { ...prevUser, ...userData };

        localStorage.setItem('user', JSON.stringify(newUser));

        return newUser;
      });
    };
 
   return (
     <AuthContext.Provider 
       value={{ 
         user, 
         isLoading, 
         login, 
         logout,
         updateUser,
         isAuthenticated: !!user 
       }}
     >
       {children}
     </AuthContext.Provider>
   );
 }
 
 export function useAuth() {
   const context = useContext(AuthContext);
   if (context === undefined) {
     throw new Error('useAuth must be used within an AuthProvider');
   }
   return context;
 }