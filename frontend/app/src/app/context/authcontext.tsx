'use client';
 
 import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
 import { useRouter } from 'next/navigation';
 import { Comment } from '../movies/types/comment';
 
 export interface User {
   id: string;
   email?: string;
   username: string;
   first_name?: string;
   last_name?: string;
   profile_picture?: string;
   birth_year?: number;
   gender?: string;
   comments: Comment[];
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

 const setSecureCookie = (name: string, value: string, maxAge: number = 86400) => {
   const cookieOptions = [
     `${name}=${value}`,
     `path=/`,
     `max-age=${maxAge}`,
     `samesite=strict`
   ];

   if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
     cookieOptions.push('secure');
   }

   document.cookie = cookieOptions.join('; ');
 };

 const removeCookie = (name: string) => {
   const cookieOptions = [
     `${name}=`,
     `path=/`,
     `expires=Thu, 01 Jan 1970 00:00:00 GMT`,
     `samesite=strict`
   ];

   if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
     cookieOptions.push('secure');
   }

   document.cookie = cookieOptions.join('; ');
 };
 
 export function AuthProvider({ children }: { children: ReactNode }) {
   const [user, setUser] = useState<User | null>(null);
   const [token, setToken] = useState<string | null>(null);
   const [isLoading, setIsLoading] = useState(true);
   const router = useRouter();
 
   useEffect(() => {
     const token = localStorage.getItem('token');
     const storedUser = localStorage.getItem('user');
     if (token && storedUser) {
       try {
         setToken(token);
         setUser(JSON.parse(storedUser));
         setSecureCookie('access_token', token);
         
       } catch (error) {
         console.error('Error parsing user data:', error);
         localStorage.removeItem('token');
         localStorage.removeItem('user');
         removeCookie('access_token');
       }
     }
     
     setIsLoading(false);
   }, []);
 
   const login = (token: string, userData: User) => {
     localStorage.setItem('token', token);
     localStorage.setItem('user', JSON.stringify(userData));

     setSecureCookie('access_token', token);
     
     setUser(userData);
     setToken(token);
   };
 
   const logout = () => {
     const token = localStorage.getItem('token');
     if (token) {
       fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/auth/logout`, {
         method: 'POST',
         headers: {
           'Authorization': `Bearer ${token}`,
         },
       }).catch(error => console.error('Error during logout:', error));
     }
     localStorage.removeItem('token');
     localStorage.removeItem('user');

     removeCookie('access_token');

     setUser(null);
     setToken(null);
     router.push('/login');
   };

   const updateUser = (userData: Partial<User>) => {
      setUser((prevUser) => {
        if (!prevUser) return null;
        const newUser = { ...prevUser, ...userData };

        if (localStorage.getItem('user')) {
          localStorage.setItem('user', JSON.stringify(newUser));
        }

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