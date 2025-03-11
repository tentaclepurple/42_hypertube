"use client"

import Link from "next/link";
import { useState } from "react";
import { userUserContext } from "../../context/usercontext";
import { user as defaultUser } from "../../profile/profile";

export default function Navbar() {
    const { user, logout, login } = userUserContext();
    const [menuOpen, setMenuOpen] = useState(false);

    return (
        <nav className="bg-gray-800 p-4">
            <div className="container mx-auto flex justify-between items-center">
                <Link legacyBehavior href="/" className="text-2xl font-bold">
                    HYPERTUBE
                </Link>
                {/* Ícono de hamburguesa para mostrar el menú */}
                <button
                    className="text-white text-2xl md:hidden"
                    onClick={() => setMenuOpen(!menuOpen)}
                >
                    ☰
                </button>
                {/* Menú de usuario */}
                {menuOpen && (
                    <div className="absolute rigth-0 mt-2 w-48 bg-white texte-black rounded shadow-lg md:hidden">
                        {user ? (
                            <>
                                <div className="p-2">
                                    <img
                                        src = {user.avatar}
                                        alt="Avatar"
                                        className="w-10 h-10 rounded-full border-2 border-white"
                                    />
                                    <p className="p-2 text-sm">{user.name}</p>
                                    <Link href="/profile" className="block w-full text-left p-2 hover:bg-gray-200">
                                        Profile
                                    </Link>
                                </div>
                                <button
                                    onClick={() => { logout(); setMenuOpen(false); }}
                                    className="block w-full text-left p-2 hover:bg-gray-200"
                                >
                                    Logout
                                </button>
                            </>
                        ) : (
                            <div className="p-2 space-y-2">
                                <button
                                    onClick={() =>{login(defaultUser); setMenuOpen(false)}}
                                    className="block w-full text-left p-2  bg-green-500 hover:bg-green-600 text-white rounded"
                                >
                                    Login
                                </button>
                                <Link
                                    href="/register"
                                    className="block w-full text-left p-2 hover:bg-gray-200"
                                >
                                    Register
                                </Link>
                            </div>
                        )}
                    </div>
                )}
                {/* Si hay usuario, mostramos el menu formato desktop */}
                <div className="hidden md:flex items-center space-x-4">
                    {user ? (
                        <>
                            <Link href="/profile" className="text-white text-sm">
                                {user.name}
                            </Link>
                            <img
                                src={user.avatar}
                                alt="Avatar"
                                className="w-10 h-10 rounded-full border-2 border-white"
                            />
                            <button
                                onClick={logout}
                                className="text-sm text-red-500 hover:text-red-700"
                            >
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={() =>{login(defaultUser); setMenuOpen(false)}}
                                className="bg-green-500 px-3 py-1 rounded text-white"
                            >
                                Login
                            </button>
                            <Link href="/register" className="text-sm hover:underline">Register</Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
}