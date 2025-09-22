'use client';

import { useState } from 'react';
import { useAuth } from '../../context/authcontext';
import { useRouter } from 'next/navigation';
import { Menu, X, LogOutIcon, ChevronDown } from "lucide-react";
import Image from 'next/image';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

const languages = {
    en: {
        name: 'English',
        flag: '🇬🇧',
        code: 'en'
    },
    es: {
        name: 'Español',
        flag: '🇪🇸',
        code: 'es'
    }
};

export default function Navbar() {
    const { user, isAuthenticated, logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
    const router = useRouter();
    const toggleMenu = () => setIsOpen(!isOpen);
    const closeMenu = () => setIsOpen(false);
    const { t, i18n } = useTranslation();
    
    const currentLanguage = languages[i18n.language as keyof typeof languages] || languages.en;
    
    const changeLanguage = (lng: string) => {
        i18n.changeLanguage(lng);
        setIsLanguageDropdownOpen(false);
    };

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
                            <div className="relative">
                                <button
                                    onClick={toggleMenu}
                                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors duration-200"
                                >
                                    <Menu size={24} />
                                </button>
                                {isOpen && (
                                    <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-50">
                                        <button
                                            onClick={() => { router.push('/favorites'); closeMenu(); }}
                                            className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors duration-200 first:rounded-t-lg"
                                        >
                                            {t("navbar.favorites")}
                                        </button>
                                        <button
                                            onClick={() => { router.push('/view_progress'); closeMenu(); }}
                                            className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors duration-200"
                                        >
                                            {t("navbar.viewProgress")}
                                        </button>
                                        <button 
                                            onClick={() => {logout(); closeMenu();}}
                                            className="flex justify-center items-center w-full text-red-400 hover:text-red-500 py-3"
                                            title='Logout'
                                        >
                                            <LogOutIcon size={20} />
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                    <div className="relative">
                        <button
                            onClick={() => setIsLanguageDropdownOpen(!isLanguageDropdownOpen)}
                            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors duration-200"
                        >
                            <span className="text-lg">{currentLanguage.flag}</span>
                            <span className="text-sm font-medium">{currentLanguage.code.toUpperCase()}</span>
                            <ChevronDown 
                                size={16} 
                                className={`transform transition-transform duration-200 ${
                                    isLanguageDropdownOpen ? 'rotate-180' : ''
                                }`}
                            />
                        </button>
                        
                        {isLanguageDropdownOpen && (
                            <div className="absolute right-0 mt-2 w-40 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-50">
                                {Object.values(languages).map((lang) => (
                                    <button
                                        key={lang.code}
                                        onClick={() => changeLanguage(lang.code)}
                                        className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors duration-200 first:rounded-t-lg last:rounded-b-lg ${
                                            currentLanguage.code === lang.code ? 'bg-gray-700' : ''
                                        }`}
                                    >
                                        <span className="text-lg">{lang.flag}</span>
                                        <span className="text-sm">{lang.name}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
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
                    <div className="border-t border-gray-700 mt-4 pt-4">
                        <div className="text-gray-400 text-sm mb-2">{t("navbar.language") || "Language"}:</div>
                        {Object.values(languages).map((lang) => (
                            <button
                                key={lang.code}
                                onClick={() => changeLanguage(lang.code)}
                                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-200 ${
                                    currentLanguage.code === lang.code 
                                        ? 'bg-gray-700 text-white' 
                                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                                }`}
                            >
                                <span className="text-lg">{lang.flag}</span>
                                <span className="text-sm">{lang.name}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </nav>
    );
}

