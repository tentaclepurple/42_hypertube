"use client";

import { useEffect, useState } from "react";
import { useAuth, User } from "../context/authcontext";
import { Pencil } from "lucide-react";

export default function Profile() {
  const { logout } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState <string | null>(null);
  const [isEditing, setEditing] = useState(false);
  const [formData, setFormData] = useState({});

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
          setFormData({
            first_name: data.first_name || "",
            last_name: data.last_name || "",
            email: data.email || "",
            birth_year: data.birth_year || "",
            gender: data.gender || "",
          });
          setIsLoading(false);
      })
      .catch((err) => {
          console.error('Error fetching user data:', err);
          setIsLoading(false);
      });
  }, []);

  const handleChange = (e: { target: { name: any; value: any; }; }) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSave = () => {
      const token = localStorage.getItem('authToken');
      fetch('http://localhost:8000/api/v1/users/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
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
        setEditing(false);
      })
      .catch((err) => {
        console.error('Error updating user data:', err);
      });
    }

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
              <div className="relative">
                <div className="flex items-center">
                  <h1 className="text-3xl font-bold">{user.username}</h1>
                  <button
                    onClick={() => setEditing(true)} 
                    className="ml-5 text-gray-400 hover:text-white" title="Edit profile">
                      <Pencil className="h-5 w-5 text-white" />
                  </button>
                </div>
                <p className="text-gray-400 mt-1">{user?.first_name} {user?.last_name}</p>
                <p className="text-gray-400 mt-1">{user?.email}</p>
                <p className="text-gray-400 mt-1">Year of birth: {user.birth_year || "N/A"}</p>
                <p className="text-gray-400 mt-1 ">Gender: {user.gender || "N/A"}</p>
              </div>
            </div>

            {isEditing && (
              <div className="mt-6">
                <h2 className="text-2xl font-bold mb-4">Edit Profile</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input 
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleChange}
                      placeholder="First Name"
                      className="p-2 bg-gray-700 text-white rounded"
                    />
                    <input 
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleChange}
                      placeholder="Last Name"
                      className="p-2 bg-gray-700 text-white rounded"
                    />
                    <input 
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="Email"
                      className="p-2 bg-gray-700 text-white rounded"
                    />
                    <input 
                      type="number"
                      name="birth_year"
                      value={formData.birth_year}
                      onChange={handleChange}
                      placeholder="Year of Birth"
                      className="p-2 bg-gray-700 text-white rounded"
                    />
                    <input 
                      type="text" 
                      name="gender"
                      value={formData.gender}
                      onChange={handleChange}
                      placeholder="Gender"
                      className="p-2 bg-gray-700 text-white rounded"
                    />
                  </div>
                  <div className="mt-4">
                    <button 
                      onClick={handleSave}
                      className="bg-blue-500 px-4 py-2 rounded text-white hover:bg-blue-600">
                        Save
                    </button>
                    <button 
                      onClick={() => setEditing(false)} 
                      className="ml-2 bg-gray-500 px-4 py-2 rounded text-white hover:bg-gray-600">
                        Cancel
                      </button>
                  </div>
              </div>
            )}
          </div>
      )}
    </div>
  );
}