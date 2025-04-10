'use client';

import { useState } from 'react';
import { useAuth } from '../../context/authcontext';
import { useRouter } from 'next/navigation';
import { Menu, X, LogOutIcon } from "lucide-react";
import Image from 'next/image';
import Link from 'next/link';


export default function Navbar() {
    const { user, isAuthenticated, logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const router = useRouter();
    const toggleMenu = () => setIsOpen(!isOpen);
    const closeMenu = () => setIsOpen(false);

    return (
        <nav className='bg-dark-900 text-white p-4'>
            <div className='container mx-auto flex justify-between items-center bottom-0 left-0 right-0'>
                <div
                    className="text-2xl font-bold cursor-pointer"
                    onClick={() => {router.push('/'); closeMenu()}}
                >
                    HYPERTUBE
                </div>
                {/* CONTENT FOR LARGE SCREENS */}
                <div className="hidden md:flex items-center gap-6">
                    {!isAuthenticated ? (
                        <>
                            <button onClick={() => router.push('/login')} className="hover:text-gray-300">Login</button>
                            <button onClick={() => router.push('/register')} className="hover:text-gray-300">Register</button>
                        </>
                    ) : (
                        <div className="flex items-center gap-4">
                            <button onClick={() => router.push('/movies')} className="hover:text-gray-300 text-xl py-2 px-4">
                                Movies
                            </button>
                            <button onClick={() => router.push('/search')} className="hover:text-gray-300 text-xl py-2 px-4">
                                Search
                            </button>
                            <Image
                                src={user?.profile_picture || "/default-avatar.png"}
                                alt="avatar"
                                width={40}
                                height={40}
                                className="rounded-full border border-gray-600"
                            />
                            <Link 
                                href="/profile" 
                                className="cursor-pointer hover:text-gray-300"
                                title='Edit Profile'
                            >
                                {user?.username}
                            </Link>
                            <button onClick={() => {logout(); closeMenu();}} className="text-red-400 hover:text-red-500" title='Logout'>
                                <LogOutIcon size={20} />
                            </button>
                        </div>
                    )}
                </div>
            {/* Hamburger button (only visible on mobile) */}
            <button onClick={toggleMenu} className="md:hidden">
                {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            </div>
            {/* Mobile drop-down menu */}
            {isOpen && (
                <div className="md:hidden flex flex-col bg-black-800 mt-2 p-4 rounded-lg">
                    {!isAuthenticated ? (
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
                                    src={user?.profile_picture || "/default-avatar.png"}
                                    alt="avatar"
                                    width={40}
                                    height={40}
                                    className="rounded-full border border-gray-600"
                                />
                                <button onClick={() => {router.push('/profile'); closeMenu();}} className="text-white-400 hover:text-white-500">
                                <Link href="/profile"> {user?.username} </Link>
                                </button>
                            </div>
                            <button onClick={() => {router.push('/search'); closeMenu();}} className="text-white-400 hover:text-white-500">
                                Search
                            </button>
                            <button onClick={() => {router.push('/movies'); closeMenu();}} className="text-white-400 hover:text-white-500 py-2">
                                Movies
                            </button>
                            <button 
                                onClick={() => { logout(); closeMenu(); }} 
                                className="text-red-400 hover:text-red-500 flex items-center justify-center py-2"
                                title='Logout'
                            >
                                <LogOutIcon size={20}  />
                            </button>
                        </>
                    )}
                </div>
            )}
        </nav>
    );
}

