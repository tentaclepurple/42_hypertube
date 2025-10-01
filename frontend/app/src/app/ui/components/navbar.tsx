'use client';

import { useState } from 'react';
import { useAuth } from '../../context/authcontext';
import { useRouter } from 'next/navigation';
import { LogOutIcon } from "lucide-react";
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
                <div className="flex items-center gap-6">
                    {!isAuthenticated ? (
                        <>
                            <button onClick={() => router.push('/login')} className="hover:text-gray-300">{t("navbar.login")}</button>
                            <button onClick={() => router.push('/register')} className="hover:text-gray-300">{t("navbar.register")}</button>
                        </>
                    ) : (
                        <div className="relative">
                            <button
                                onClick={toggleMenu}
                                className="flex items-center gap-2 hover:opacity-80 transition-opacity duration-200"
                            >
                                <Image
                                    src={user?.profile_picture || "/default-avatar.png"}
                                    alt="avatar"
                                    width={40}
                                    height={40}
                                    className="rounded-full border border-gray-600"
                                />
                            </button>
                            {isOpen && (
                                <div className="absolute right-0 mt-2 w-56 bg-black rounded-lg shadow-lg border border-gray-700 z-50">
                                    <div className="px-4 py-3 border-b border-gray-700">
                                        <Link 
                                            href="/profile" 
                                            className="cursor-pointer hover:text-gray-300 font-medium"
                                            title='Edit Profile'
                                            onClick={closeMenu}
                                        >
                                            {user?.username}
                                        </Link>
                                    </div>
                                    <button
                                        onClick={() => { router.push('/search'); closeMenu(); }}
                                        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors duration-200"
                                    >
                                        {t("navbar.search")}
                                    </button>
                                    <button
                                        onClick={() => { router.push('/movies'); closeMenu(); }}
                                        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors duration-200"
                                    >
                                        {t("navbar.movies")}
                                    </button>
                                    <button
                                        onClick={() => { router.push('/favorites'); closeMenu(); }}
                                        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors duration-200"
                                    >
                                        {t("navbar.favorites")}
                                    </button>
                                    <button
                                        onClick={() => { router.push('/view_progress'); closeMenu(); }}
                                        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors duration-200"
                                    >
                                        {t("navbar.watching")}
                                    </button>
                                    <button
                                        onClick={() => { router.push('/api'); closeMenu(); }}
                                        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors duration-200"
                                    >
                                        API
                                    </button>
                                    
                                    <div className="border-t border-gray-700 mt-2 pt-2">
                                        <div className="px-4 py-2 text-gray-400 text-sm font-medium">
                                            {t("navbar.language") || "Language"}
                                        </div>
                                        {Object.values(languages).map((lang) => (
                                            <button
                                                key={lang.code}
                                                onClick={() => changeLanguage(lang.code)}
                                                className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-700 transition-colors duration-200 ${
                                                    currentLanguage.code === lang.code ? 'bg-gray-700' : ''
                                                }`}
                                            >
                                                <span className="text-lg">{lang.flag}</span>
                                                <span className="text-sm">{lang.name}</span>
                                            </button>
                                        ))}
                                    </div>

                                    <div className="border-t border-gray-700 mt-2 pt-2">
                                        <button 
                                            onClick={() => { logout(); closeMenu(); }}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 text-red-400 hover:text-red-500 hover:bg-gray-700 transition-colors duration-200"
                                            title='Logout'
                                        >
                                            <LogOutIcon size={20} />
                                            {t("navbar.logout")}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
}

