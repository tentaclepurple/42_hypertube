"use client";

import { useEffect, useState } from "react";
import { useAuth, User } from "../context/authcontext";
import { Pencil } from "lucide-react";
import { parsedError, parsedEditError } from "../ui/error/parsedError";

export default function Profile() {
  const { logout } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState <string[] | null>(null);
  const [editError, setEditError] = useState <string[] | null>(null);
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
          const text = parsedError(await response.json());
          return Promise.reject(text);
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
        setError(err);
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
      setIsLoading(true);
      setEditError(null);
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
          const data = parsedEditError(await response.json());
          return Promise.reject(data);
        }
        return response.json();
      })
      .then((data) => {
        setUser(data);
        setEditing(false);
      })
      .catch((err) => {
        setEditError(err);
      })
      .finally(() => {
        setIsLoading(false);
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
      {error && !isEditing && (
        <div className="text-center mt-4 py-2">
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
            </div>
        </div>
      )}
      {!isLoading && !error && user && (
        <div className="max-w-screen-lg mx-auto p-6">
          {(!isEditing ? (  
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
          ):(
            <div className="mt-6">
              <h2 className="text-2xl font-bold mb-4">Edit Profile</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-300 mb-1">
                      First Name
                    </label>
                    <input 
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleChange}
                      placeholder="First Name"
                      className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.first_name ? 'border border-red-500' : ''}`}
                      />
                  </div>
                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-300 mb-1">
                      Last Name
                    </label>
                    <input 
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleChange}
                      placeholder="Last Name"
                      className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.last_name ? 'border border-red-500' : ''}`}
                      />
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">
                      Email
                    </label>
                    <input 
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="Email"
                      className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.email ? 'border border-red-500' : ''}`}
                      />
                  </div>
                  <div>
                    <label htmlFor="birth_year" className="block text-sm font-medium text-gray-300 mb-1">
                      Year of Birth
                    </label>
                    <input 
                      type="number"
                      name="birth_year"
                      value={formData.birth_year}
                      onChange={handleChange}
                      placeholder="Year of Birth"
                      min={1900}
                      max={new Date().getFullYear()}
                      className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.birth_year ? 'border border-red-500' : ''}`}
                      />
                  </div>
                  <div>
                    <label htmlFor="gende" className="block text-sm font-medium text-gray-300 mb-1">
                      Gender
                    </label>
                    <select 
                      name="gender"
                      value={formData.gender}
                      onChange={handleChange}
                      className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.gender ? 'border border-red-500' : ''}`} 
                      >
                      <option value="" disabled>Select Gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="non-binary">Non-binary</option>
                      <option value="prefer-not-to-say">Prefer not to say</option>  
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
                <div className="mt-4">
                  <button 
                    onClick={handleSave}
                    className="bg-blue-500 px-4 py-2 rounded text-white hover:bg-blue-600">
                      Save
                  </button>
                  <button 
                    onClick={() => {setEditing(false), setEditError(null)}}
                    className="ml-2 bg-gray-500 px-4 py-2 rounded text-white hover:bg-gray-600">
                      Cancel
                    </button>
                {editError && (
                  <div className="mt-4 mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                    {Object.entries(editError).map(([field, message]) => (
                      <p key={field}>
                        <strong>{field}:</strong> {message}
                      </p>
                    ))}
                  </div>
                )}
                </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}