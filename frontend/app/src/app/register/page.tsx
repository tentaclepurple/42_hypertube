'use client';

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { parsedError, parsedEditError } from "../ui/error/parsedError";

export default function Register() {
  const [ formData, setFormData ] = useState({
    email: "",
    username:"",
    password: "",
    confirm_password: "",
    first_name: "",
    last_name: ""
  });

  const [ error, setError ] = useState({
    email: "",
    username: "",
    password: "",
    confirm_password: "",
    first_name: "",
    last_name: "",
    general: ""
  });

  const [ showPassword, setShowPassword ] = useState(false);
  const [ showConfirmPassword, setShowConfirmPassword ] = useState(false);
  const [ loading, setLoading ] = useState(false);
  const [ success, setSuccess ] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setError({
      email: "",
      username: "",
      password: "",
      confirm_password: "",
      first_name: "",
      last_name: "",
      general: ""
    });

    if(formData.password !== formData.confirm_password) {
      setError((prev) => ({ ...prev, confirm_password: "Passwords do not match." }));
      return;
    }

    setLoading(true);
    try{
      const { confirm_password, ...data } = formData; // Exclude confirm_password from the data sent to the backend

      const response = await fetch("http://localhost:8000/api/v1/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if(!response.ok) {
        const data = parsedEditError(await response.json());
        console.log("DATOS: ", data);
        setError((prev) => ({ ...prev, ...data,}));
        return;
      }
      setSuccess(true);
      setFormData({
        email: "",
        username: "",
        password: "",
        confirm_password: "",
        first_name: "",
        last_name: ""
      });
    } catch (error) {
      setError((prev) => ({ ...prev, general: "Something went wrong. Please try again." }));
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword((prev) => !prev);
  };

    return (
      <div className="p-6 bg-dark-900 text-white">
        <div className="max-w-screen-lg mx-auto p-6">
          {loading && (
            <div className="text-center mb-4 py-2">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
              <p className="mt-2">Loading...</p>
            </div>
          )}

          {success && (
            <div className="text-center mt-4 py-2">
              <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                Registration successful! You can now <a href="/login" className="text-blue-600 hover:underline">log in</a>.
              </div>
            </div>
          )}

          {error.general && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  name="first_name"
                  id="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className={`w-full p-2 border rounded ${error.first_name ? "border-red-500" : "border-gray-300"}`}
                  placeholder="First Name"
                />
                {error.first_name && <p className="text-red-500 text-sm mt-1">{error.first_name}</p>}
              </div>
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  name="last_name"
                  id="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className={`w-full p-2 border rounded ${error.last_name ? "border-red-500" : "border-gray-300"}`}
                  placeholder="Last Name"
                />
                {error.last_name && <p className="text-red-500 text-sm mt-1">{error.last_name}</p>}
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  id="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`w-full p-2 border rounded ${error.email ? "border-red-500" : "border-gray-300"}`}
                  placeholder="you@email.com"
                />
                {error.email && <p className="text-red-500 text-sm mt-1">{error.email}</p>}
              </div>
              <div>
                <label htmlFor="username" className="block text-sm font-medium mb-1">
                  Username
                </label>
                <input
                  type="text"
                  name="username"
                  id="username"
                  value={formData.username}
                  onChange={handleChange}
                  className={`w-full p-2 border rounded ${error.username ? "border-red-500" : "border-gray-300"}`}
                  placeholder="Username"
                />
                {error.username && <p className="text-red-500 text-sm mt-1">{error.username}</p>}
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-medium mb-1">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    id="password"
                    value={formData.password}
                    onChange={handleChange}
                    className={`w-full p-2 border rounded ${error.password ? "border-red-500" : "border-gray-300"}`}
                    placeholder="Password minimum 8 characters"
                  />
                  <button
                    type="button"
                    onClick={togglePasswordVisibility}
                    className="absolute right-2 top-2"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {error.password && <p className="text-red-500 text-sm mt-1">{error.password}</p>}
              </div>
              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirm_password"
                    id="confirm_password"
                    value={formData.confirm_password}
                    onChange={handleChange}
                    className={`w-full p-2 border rounded ${error.confirm_password ? "border-red-500" : "border-gray-300"}`}
                    placeholder="Confirm Password"
                  />
                  <button
                    type="button"
                    onClick={toggleConfirmPasswordVisibility}
                    className="absolute right-2 top-2"
                  >
                    {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {error.confirm_password && <p className="text-red-500 text-sm mt-1">{error.confirm_password}</p>}
              </div>
              <div className="col-span-1 sm:col-span-2 flex justify-center">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-500 px-4 py-2 rounded text-white hover:bg-blue-600"
                >
                  {loading ? "Registering..." : "Register"}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    );
  }