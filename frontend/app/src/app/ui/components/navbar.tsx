'use client';

import { useState } from 'react';
import { useAuth } from '../../context/authcontext';
import { useRouter } from 'next/navigation';
import { Menu, X, LogOutIcon } from "lucide-react";
import Image from 'next/image';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';


export default function Navbar() {
    const { user, isAuthenticated, logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const router = useRouter();
    const toggleMenu = () => setIsOpen(!isOpen);
    const closeMenu = () => setIsOpen(false);

    const { t } = useTranslation();

    return (
        <nav className='bg-dark-900 text-white p-4'>
            <div className='container mx-auto flex justify-between items-center bottom-0 left-0 right-0'>
                <div
                    className="text-2xl font-bold cursor-pointer"
                    onClick={() => {router.push('/'); closeMenu()}}
                >
                    HYPERTUBE
                </div>
                <div className="hidden md:flex items-center gap-6">
                    {!isAuthenticated ? (
                        <>
                            <button onClick={() => router.push('/login')} className="hover:text-gray-300">{t("navbar.login")}</button>
                            <button onClick={() => router.push('/register')} className="hover:text-gray-300">{t("navbar.register")}</button>
                        </>
                    ) : (
                        <div className="flex items-center gap-4">
                            <button onClick={() => router.push('/api')} className="hover:text-gray-300 text-xl py-2 px-4">
                                API
                            </button>
                            <button onClick={() => router.push('/movies')} className="hover:text-gray-300 text-xl py-2 px-4">
                                {t("navbar.movies")}
                            </button>
                            <button onClick={() => router.push('/search')} className="hover:text-gray-300 text-xl py-2 px-4">
                                {t("navbar.search")}
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
            <button onClick={toggleMenu} className="md:hidden">
                {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            </div>
            {isOpen && (
                <div className="md:hidden flex flex-col bg-black-800 mt-2 p-4 rounded-lg">
                    {!isAuthenticated ? (
                        <>
                            <button 
                                onClick={() => { router.push('/login'); closeMenu(); }} 
                                className="py-2 hover:text-gray-300"
                            >
                                {t("navbar.login")}
                            </button>
                            <button 
                                onClick={() => { router.push('/register'); closeMenu(); }} 
                                className="py-2 hover:text-gray-300"
                            >
                                {t("navbar.register")}
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
                            <button onClick={() => {router.push('/api'); closeMenu();}} className="text-white-400 hover:text-white-500">
                                API
                            </button>
                            <button onClick={() => {router.push('/search'); closeMenu();}} className="text-white-400 hover:text-white-500">
                                {t("navbar.search")}
                            </button>
                            <button onClick={() => {router.push('/movies'); closeMenu();}} className="text-white-400 hover:text-white-500 py-2">
                                {t("navbar.movies")}
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

