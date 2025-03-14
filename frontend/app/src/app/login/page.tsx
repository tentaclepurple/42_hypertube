"use client";

import { useState } from "react";

export default function Login() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleLogin = async () => {
      setLoading(true);
      setError(null);
      try{
        const response = await fetch("http://localhost:8000/api/v1/auth/oauth/42", {
          method: "GET",
          credentials: "include",
          headers: {
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error("Failed to login");
        }
        const data = await response.json();
        console.log("Auth Response:", data);
      } catch (err) {
        setError("Failed to login");
        console.error(err);
      } finally {
        setLoading(false);
      }
  };

  return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white">
          <h1 className="text-3xl font-bold mb-4">Login with 42</h1>
          <button 
              onClick={handleLogin} 
              className="bg-blue-500 hover:bg-blue-600 px-6 py-2 rounded text-white"
              disabled={loading}
          >
              {loading ? "Logging in..." : "Login with 42"}
          </button>
          {error && <p className="text-red-500 mt-2">{error}</p>}
      </div>
  );
}