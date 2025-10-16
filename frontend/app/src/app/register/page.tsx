'use client';

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { parsedEditError } from "../ui/error/parsedError";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();

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
      setError((prev) => ({ ...prev, confirm_password: `${t("register.errors.confirmPassword")}` }));
      return;
    }

    setLoading(true);
    try{
      const data = { ...formData };

      const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if(!response.ok) {
        const data = parsedEditError(await response.json());
        setError((prev) => ({ ...prev, ...data,}));
        throw data;
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
    } catch {
      setError((prev) => ({ ...prev, general: `${t("register.errors.general")}` }));
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
    <div className="p-6 max-w-screen-lg mx-auto bg-dark-900 text-white">
      {loading && (
        <div className="text-center mb-4 py-2">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
          <p className="mt-2">{t("register.loading")}</p>
        </div>
      )}

      {success && (
        <div className="text-center mt-4 py-2">
          <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
            {t("register.success")} <a href="/login" className="text-blue-600 hover:underline">{t("register.login")}</a>.
          </div>
        </div>
      )}

      {error.general && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-center">
          {error.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="first_name" className="block text-sm font-medium mb-1">
              {t("profile.firstName")}
            </label>
            <input
              type="text"
              name="first_name"
              id="first_name"
              value={formData.first_name}
              onChange={handleChange}
              className={`w-full p-2 border rounded ${error.first_name ? "border-red-500" : "border-gray-300"}`}
              placeholder={t("profile.firstName")}
              autoComplete="on"
            />
            {error.first_name && <p className="text-red-500 text-sm mt-1">{t("register.errors.firstName")}</p>}
          </div>
          <div>
            <label htmlFor="last_name" className="block text-sm font-medium mb-1">
              {t("profile.lastName")}
            </label>
            <input
              type="text"
              name="last_name"
              id="last_name"
              value={formData.last_name}
              onChange={handleChange}
              className={`w-full p-2 border rounded ${error.last_name ? "border-red-500" : "border-gray-300"}`}
              placeholder={t("profile.lastName")}
              autoComplete="on"
            />
            {error.last_name && <p className="text-red-500 text-sm mt-1">{t("register.errors.lastName")}</p>}
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              {t("profile.email")}
            </label>
            <input
              type="email"
              name="email"
              id="email"
              value={formData.email}
              onChange={handleChange}
              className={`w-full p-2 border rounded ${error.email ? "border-red-500" : "border-gray-300"}`}
              placeholder={t("register.emailPlaceholder")}
              autoComplete="on"
            />
            {error.email && <p className="text-red-500 text-sm mt-1">{t("register.errors.email")}</p>}
          </div>
          <div>
            <label htmlFor="username" className="block text-sm font-medium mb-1">
              {t("login.username")}
            </label>
            <input
              type="text"
              name="username"
              id="username"
              value={formData.username}
              onChange={handleChange}
              className={`w-full p-2 border rounded ${error.username ? "border-red-500" : "border-gray-300"}`}
              placeholder={t("login.username")}
              autoComplete="on"
            />
            {error.username && <p className="text-red-500 text-sm mt-1">{t("register.errors.username")}</p>}
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              {t("login.password")}
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                id="password"
                value={formData.password}
                onChange={handleChange}
                className={`w-full p-2 border rounded ${error.password ? "border-red-500" : "border-gray-300"}`}
                placeholder={t("register.passPlaceholder")}
                autoComplete="off"
              />
              <button
                type="button"
                onClick={togglePasswordVisibility}
                className="absolute right-2 top-2"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            {error.password && <p className="text-red-500 text-sm mt-1">{t("register.errors.password")}</p>}
          </div>
          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium mb-1">
              {t("register.confirmPassword")}
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                name="confirm_password"
                id="confirm_password"
                value={formData.confirm_password}
                onChange={handleChange}
                className={`w-full p-2 border rounded ${error.confirm_password ? "border-red-500" : "border-gray-300"}`}
                placeholder={t("register.confirmPassword")}
                autoComplete="off"
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
              {loading ? t("register.registering") : t("register.register")}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}