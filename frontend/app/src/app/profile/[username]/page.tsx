"use client";
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useAuth, User } from '../../context/authcontext';
import { Star, MessageCircle, Calendar, UserIcon } from 'lucide-react';
import { parsedError } from '../../ui/error/parsedError';

export default function UserPublicProfile() {
    const { token, logout } = useAuth();
    const { username } = useParams();
    const [userProfile, setUserProfile] = useState<User | null>(null);
    const [error, setError] = useState<string[] | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    useEffect(() => {
        fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/users/${username}`, {
            method: 'GET',
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
        .then(async (response) => {
            if (!response.ok) {
            if (response.status === 401) logout();
            const text = parsedError(await response.json());
            return Promise.reject(text);
            }
            return response.json();
        })
        .then((data) => {
            setUserProfile(data);
            setIsLoading(false);
        })
        .catch((err) => {
            setError(err);
            setIsLoading(false);
        });
    }, [username]);

    if (error) {
        return (
          <div className="p-6 bg-dark-900 text-white min-h-screen">
            <div className="text-center mt-4 py-2">
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error.map((err, index) => (
                  <div key={index}>{err}</div>
                ))}
              </div>
            </div>
          </div>
        );
      }
    
    if (isLoading) {
        return (
          <div className="p-6 bg-dark-900 text-white min-h-screen">
            <div className="text-center mt-4 py-2">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
              <p className="mt-2">Loading user profile...</p>
            </div>
          </div>
        );
      }

    if (!userProfile) {
        return (
          <div className="p-6 bg-dark-900 text-white min-h-screen">
            <div className="text-center mt-4 py-2">
              <p className="text-lg">User profile not found.</p>
            </div>
          </div>
        );
      }
    
    return (
        <div className="p-6 bg-dark-900 text-white min-h-screen">
            <div className="max-w-screen-lg mx-auto">
                <div className="flex flex-col md:flex-row items-center space-x-4 mb-8">
                    <img
                    src={userProfile?.profile_picture || '/default-avatar.png'}
                    alt={userProfile.username}
                    className="w-32 h-32 rounded-full border-4 border-gray-600 mb-4 md:mb-0"
                    />
                    <div>
                    <h1 className="text-3xl font-bold">{userProfile.username}</h1>
                    {(userProfile.first_name || userProfile.last_name) && (
                        <p className="text-gray-400 mt-1">
                        {userProfile.first_name} {userProfile.last_name}
                        </p>
                    )}
                    {userProfile.birth_year && (
                        <div className="flex items-center mt-2 text-gray-400">
                        <Calendar className="h-4 w-4 mr-2" />
                        <span>Born in {userProfile.birth_year}</span>
                        </div>
                    )}
                    {userProfile.gender && (
                        <div className="flex items-center mt-1 text-gray-400">
                        <UserIcon className="h-4 w-4 mr-2" />
                        <span className="capitalize">{userProfile.gender}</span>
                        </div>
                    )}
                    </div>
                </div>
            </div>
        </div>
    );
}


