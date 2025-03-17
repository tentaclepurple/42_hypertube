'use client';

import { useState } from 'react';
import { useAuth } from '../../context/authcontext';
import { useRouter } from 'next/navigation';
import { Menu, X } from "lucide-react";
import Image from 'next/image';

export default function Navbar() {
    const { user, logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const router = useRouter();
    const isAuth = !!user;
    
    const toggleMenu = () => setIsOpen(!isOpen);
    const closeMenu = () => setIsOpen(false);
    
    return (
        <nav className='bg-dark-900 text-white p-4'>
            <div className='container mx-auto flex justify-between items-center'>
                {/* Logo */}
                <div
                    className="text-2xl font-bold cursor-pointer"
                    onClick={() => {router.push('/'); closeMenu()}}
                >
                    HYPERTUBE
                </div>
                
                {/* CONTENIDO PARA PANTALLAS GRANDES */}
                <div className="hidden md:flex items-center gap-6">
                    {!isAuth ? (
                        <>
                            <button onClick={() => router.push('/login')} className="hover:text-gray-300">Login</button>
                            <button onClick={() => router.push('/register')} className="hover:text-gray-300">Register</button>
                        </>
                    ) : (
                        <div className="flex items-center gap-4">
                            <Image
                                src={user.profile_picture || "/default-avatar.png"}
                                alt="avatar"
                                width={40}
                                height={40}
                                className="rounded-full border border-gray-600"
                            />
                            <span>{user.username}</span>
                            <button onClick={() => {logout(); closeMenu();}} className="text-red-400 hover:text-red-500">
                                Logout
                            </button>
                        </div>
                    )}
                </div>
                
                {/* Botón de hamburguesa (solo visible en móvil) */}
                <button onClick={toggleMenu} className="md:hidden">
                    {isOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>
            
            {/* Menú desplegable para móvil */}
            {isOpen && (
                <div className="md:hidden flex flex-col bg-gray-800 mt-2 p-4 rounded-lg">
                    {!isAuth ? (
                        <>
                            <button 
                                onClick={() => { router.push('/login'); closeMenu(); }} 
                                className="py-2 hover:text-gray-300"
                            >
                                Login
                            </button>
                            <button 
                                onClick={() => { router.push('/register'); closeMenu(); }} 
                                className="py-2 hover:text-gray-300"
                            >
                                Register
                            </button>
                        </>
                    ) : (
                        <>
                            <div className="flex items-center gap-3 py-2">
                                <Image
                                    src={user.profile_picture || "/default-avatar.png"}
                                    alt="avatar"
                                    width={40}
                                    height={40}
                                    className="rounded-full border border-gray-600"
                                />
                                <span>{user.username}</span>
                            </div>
                            <button 
                                onClick={() => { logout(); closeMenu(); }} 
                                className="py-2 text-red-400 hover:text-red-500"
                            >
                                Logout
                            </button>
                        </>
                    )}
                </div>
            )}
        </nav>
    );
}

