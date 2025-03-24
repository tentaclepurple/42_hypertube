"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../context/authcontext";

export default function Profile() {
  const { logout } = useAuth();
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState <string | null>(null);

  useEffect(() => {
      const token = localStorage.getItem('authToken');
      fetch('http://localhost:8000/api/v1/users/me', {
          method: 'GET',
          headers: {
              Authorization: `Bearer ${token}`,
          },
      })
      .then(async (response) => {
          if (!response.ok) {
            if (response.status === 401) logout();
            const text = await response.text();
            setError(text);
            throw new Error(`Server error: Status ${response.status}, ${text}`);
          }
          return response.json();
      })
      .then((data) => {
          setUser(data);
          setIsLoading(false);
      })
      .catch((err) => {
          console.error('Error fetching user data:', err);
          setIsLoading(false);
      });
  }, []);
  return (
    < div className=" p-6 bg-dark-900 text-white min-h-screen " >
      {isLoading && (
        <div className="text-center mt-4 py-2">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
            <p className="mt-2">Loading profile...</p>
        </div>
      )}
      {error && (
        <div className="text-center mt-4 py-2">
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
            </div>
        </div>
      )}

      {!isLoading && !error && user && (
        <div className="max-w-screen-lg mx-auto p-6">
            <div className="flex flex-col md:flex-row items-center space-x-4">
              <img
                src={user?.profile_picture || '/default-avatar.png'}
                alt={user.username}
                className="w-32 h-32 rounded-full border-4 border-gray-600 mb-4 md:mb-0"
              />
              <div>
                <h1 className="text-3xl font-bold">{user.username}</h1>
                <p className="text-gray-400 mt-1">{user?.first_name} {user?.last_name}</p>
                <p className="text-gray-400 mt-1">{user?.email}</p>
                <p className="text-gray-400 mt-1">Year of birth: {user.birth_year || "N/A"}</p>
                <p className="text-gray-400 mt-1 ">Gender: {user.gender || "N/A"}</p>
              </div>
            </div>
          </div>
      )}
    </div>
  );
}