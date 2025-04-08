"use client";

import { useState } from "react";
import { Send } from "lucide-react"
import  Link  from "next/link";
import { parsedError } from "../ui/error/parsedError";
import { useAuth } from "../context/authcontext";


export default function ForgotPassword() {
    const [ email, setEmail ] = useState("");
    const [ loading, setLoading ] = useState(false);
    const [ error, setError ] = useState<string[] | null>(null);
    const [ success, setSuccess ] = useState(false);
    const { logout } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await fetch("http://localhost:8000/api/v1/auth/forgot-password", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ email }),
            });

            if (!response.ok) {
                if (response.status === 401) logout();
                const errorData = parsedError(await response.json());
                return Promise.reject(errorData);
            }
            setSuccess(true);
        } catch (err) {
            setError(err as string[]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center">
            <div className="max-w-md mt-auto p-6">
                {loading && (
                    <div className="text-center mt-4 py-2">
                        <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
                        <p className="mt-2">Sending email...</p>
                    </div>
                )}
                {error && (
                    <div className="text-center mt-4 py-2">
                        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                            {error}
                        </div>
                    </div>
                )}
                {success ? (
                    <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                        <p className="text-center">Email sent successfully! Check your inbox.</p>
                        <Link href="/login" className="text-blue-500 hover:underline">
                            Go to Login
                        </Link>
                    </div>
                ) : (
                    <>
                        <form onSubmit={handleSubmit} className="mb-6 mt-6">
                            <div className="space-y-4">
                                <label htmlFor="email" className="block text-sm font-medium mb-1">
                                    Email
                                </label>
                                <div className="flex rounded overflow-hidden border border-gray-300">
                                    <input
                                        type="email"
                                        id="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="w-full p-2 outline-none"
                                        placeholder="Enter your email"
                                    />
                                    <button
                                        type="submit"
                                        className="bg-blue-600 text-white px-4 py-2 hover:bg-blue-700 transition duration-200 flex items-center justify-center disabled:opacity-50"
                                        disabled={loading}
                                        title="Send email"
                                    >
                                        {loading ? "Sending..." : (<Send size={16}/>)}
                                    </button>
                                </div>
                                <p className="text-sm text-gray-500">
                                    Remembered your password?{" "}
                                    <Link href="/login" className="text-blue-500 hover:underline">
                                        Login
                                    </Link>
                                </p>
                            </div>
                        </form>
                    </>
                )}
            </div>
        </div>
    );
}