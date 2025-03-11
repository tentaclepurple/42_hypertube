"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface User {
    name: string;
    avatar: string;
    imageSize: number;
}

interface UserContextType {
    user: User | null;
    login: (user: User) => void;
    logout: () => void;
}


const UserContext = createContext<UserContextType | undefined>(undefined);

export function userUserContext() {
    const context = useContext(UserContext);
    if (!context) {
        throw new Error('useUserContext must be used inside a UserProvider');
    }
    return context;
}

export function UserProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null >(null);

    const login = (user : User) => setUser(user);
    const logout = () => setUser(null);

    return (
        <UserContext.Provider value={{ user, login, logout }}>
            {children}
        </UserContext.Provider>
    );
}
