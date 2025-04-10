"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Eye, EyeOff, Check } from "lucide-react";
import Link from "next/link";
import { parsedEditError } from "../ui/error/parsedError";
import { useAuth } from "../context/authcontext";

export default function ResetPassword() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const token = searchParams.get("token");
    const { logout } = useAuth();
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string[] | null>(null);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (!token) {
            setError(["Invalid token"]);
        }
    }, [token]);

    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        if (newPassword !== confirmPassword) {
            setError(["Passwords do not match"]);
            setLoading(false);
            return;
        }

        try {
            const response = await fetch("http://localhost:8000/api/v1/auth/reset-password", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ token, new_password: newPassword }),
            });

            if (!response.ok) {
                if (response.status === 401) logout();
                const errorData = parsedEditError(await response.json());
                throw errorData;
            }
            setSuccess(true);
            setTimeout(() => {
                router.push("/login");
            }, 3000);
        } catch (err) {
            setError(Array.isArray(err) ? err : Object.values(err as Record<string, string>));
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="flex items-center justify-center ">
            <div className="max-w-md mt-auto p-6">
                {loading && (
                    <div className="text-center mt-4 py-2">
                        <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
                        <p className="mt-2">Processing...</p>
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
                        <Check className="inline mr-2" />
                        Password reset successfully. Redirecting to login...
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                                New Password
                            </label>
                            <div className="mt-1 relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    id="newPassword"
                                    name="newPassword"
                                    autoComplete="off"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="block w-full p-2 border border-gray-300 rounded-md"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={togglePasswordVisibility}
                                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400"
                                >
                                    {showPassword ? <EyeOff /> : <Eye />}
                                </button>
                            </div>
                        </div>
                        <div>
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                                Confirm Password
                            </label>
                            <input
                                type={showPassword ? "text" : "password"}
                                id="confirmPassword"
                                name="confirmPassword"
                                autoComplete="off"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="block w-full p-2 border border-gray-300 rounded-md"
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition duration-200"
                        >
                            Reset Password
                        </button>
                    </form>
                )}
                <div className="mt-4 text-center">
                    <p className="text-sm text-gray-500">
                        Remembered your password?{" "}
                        <Link href="/login" className="text-blue-500 hover:underline">
                            Login
                        </Link>
                    </p>
                </div>
            </div>   
        </div>
    )
}
