"use client";

import React from "react";

interface BotonProps {
    onClick: () => void;
    children: React.ReactNode;
    className?: string; 
}

export default function Boton({ onClick, children, className }: BotonProps) {
    return ( 
        <button onClick={onClick}
            className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition ${className}`}>
            {children}
        </button>
    );
}