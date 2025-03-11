'use client';

import { useState } from "react";
import Boton from "./boton";
import Profile from "./profile";

export default function Page() {
    const [isLoggedIn, setIsLoggenIN] = useState(false);
    return (
        <main className="flex flex-col items-center justify-center min-h-screen py-2">
            <h1 className="text-6xl">HYPERTUBE</h1>
            {isLoggedIn ? (
                <Profile />
            ) : (
                <p className="text-2xl">Inicia sesión para ver tu perfil</p>
            )}
            <Boton 
                onClick={() => setIsLoggenIN(!isLoggedIn)}
                className={`${isLoggedIn ? "bg-red-500 hover:bg-red-700" : "bg-green-500 hover:bg-green-700"}`}
            >
                {isLoggedIn ? "Cerrar sesión" : "Iniciar sesión"}
            </Boton>
        </main>
    );
}