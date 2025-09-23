"use client";

import React, { useEffect, useState } from "react";
import { useAuth, User } from "../context/authcontext";
import { Pencil, Camera, Upload, X, MessageCircle, Trash2, Check, Star } from "lucide-react";
import { parsedError, parsedEditError } from "../ui/error/parsedError";
import Link from "next/link";
import { formatDate, renderStars } from "../ui/comments";
import { useTranslation } from "react-i18next";

interface AvatarUploadProps {
  user: User;
  handleImageChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleUpload: () => void;
  uploading: boolean;
  editError: string[] | null;
  profilePicture: File | null;
  setProfilePicture: (file: File | null) => void;
}

function AvatarUpload({
  user,
  handleImageChange,
  handleUpload,
  uploading,
  editError,
  profilePicture,
  setProfilePicture
}: AvatarUploadProps) {
  const [hover, setHover] = useState(false);
  const [previewURL, setPreviewURL] = useState<string | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    if (profilePicture) {
      const url = URL.createObjectURL(profilePicture);
      setPreviewURL(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewURL(null);
    }
  }, [profilePicture]);

  const handleCancel = () => {
    setProfilePicture(null);
    setPreviewURL(null);
    const input = document.getElementById('avatar-upload') as HTMLInputElement;
    if (input) {
      input.value = '';
    }
  };

  return (
    <div className="flex flex-col items-center">
      <div 
        className="relative group"
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        <img
          src={previewURL || user?.profile_picture || '/default-avatar.png'}
          alt={user?.username || 'User avatar'}
          className="w-32 h-32 rounded-full border-4 border-gray-600 object-cover"
        />
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          className="hidden"
          id="avatar-upload"
          name="avatar-upload"
          disabled={uploading}
        />
        <label
          htmlFor="avatar-upload"
          className={`absolute inset-0 bg-black bg-opacity-50 rounded-full flex items-center justify-center cursor-pointer 
            ${hover ? 'opacity-75' : 'opacity-0'} 
            transition-opacity duration-300 ease-in-out
            ${uploading ? 'pointer-events-none' : ''}`}
          title="Change profile picture"
        >
          <Camera className="h-8 w-8 text-white" />
        </label>
      </div>

      {uploading ? (
        <div className="mt-4 flex items-center justify-center">
          <div className="animate-spin mr-2">
            <Upload className="text-blue-500" />
          </div>
          <span className="text-sm text-gray-400">{t("profile.uploading")}</span>
        </div>
      ) : (
        <>
          {profilePicture && (
            <div className="mt-4 flex flex-col space-y-2 w-full max-w-xs">
              <button
                onClick={handleUpload}
                className="bg-blue-500 text-white px-4 py-2 rounded-md flex items-center justify-center hover:bg-blue-600 transition"
              >
                <Upload className="mr-2 w-5 h-5" />
                {t("profile.upload")}
              </button>
              <button
                onClick={handleCancel}
                className="bg-gray-500 text-white px-4 py-2 rounded-md flex items-center justify-center hover:bg-gray-600 transition"
              >
                <X className="mr-2 w-5 h-5" />
                {t("profile.cancel")}
              </button>
            </div>
          )}
          {editError && editError.length > 0 && (
            <div className="mt-2 text-red-500 text-sm">
              {editError.map((err, index) => (
                <p key={index}>{err}</p>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function Profile() {
  const { logout, updateUser } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string[] | null>(null);
  const [editError, setEditError] = useState<string[] | null>(null);
  const [editImgError, setEditImgError] = useState<string[] | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    email_confirm: "",
    birth_year: "",
    gender: ""
  });
  const [profilePicture, setProfilePicture] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [editCommentId, setEditCommentId] = useState<string | null>(null);
  const [editCommentText, setEditCommentText] = useState({
    comment: "",
    rating: 1,
  });
  const [editCommentError, setEditCommentError] = useState<string[] | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          logout();
          return;
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/users/me`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          if (response.status === 401) {
            logout();
            return;
          }
          const errorData = await response.json();
          const errorText = parsedError(errorData);
          throw new Error(Array.isArray(errorText) ? errorText.join(', ') : errorText);
        }

        const data = await response.json();
        setUser(data);
        setFormData({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          email: data.email || "",
          email_confirm: data.email || "",
          birth_year: data.birth_year ? String(data.birth_year) : "",
          gender: data.gender || "",
        });
      } catch (err) {
        console.error('Error fetching user profile:', err);
        setError([err instanceof Error ? err.message : 'An error occurred']);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserProfile();
  }, [logout]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const validateForm = (): string[] => {
    const errors: string[] = [];
    
    if (!formData.first_name?.trim()) {
      errors.push("First name is required");
    }
    
    if (!formData.last_name?.trim()) {
      errors.push("Last name is required");
    }
    
    if (!formData.email?.trim()) {
      errors.push("Email is required");
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.push("Please enter a valid email address");
    }
    
    if (formData.email !== formData.email_confirm) {
      errors.push("Email addresses do not match");
    }

    if (formData.birth_year && (isNaN(Number(formData.birth_year)) || Number(formData.birth_year) < 1900 || Number(formData.birth_year) > new Date().getFullYear())) {
      errors.push("Please enter a valid birth year");
    }

    return errors;
  };

  const handleSave = async () => {
    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
      setEditError(validationErrors);
      return;
    }

    setIsLoading(true);
    setEditError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        logout();
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/users/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        if (response.status === 401) {
          logout();
          return;
        }
        const errorData = await response.json();
        const errorText = parsedEditError(errorData);
        throw errorText;
      }

      const data = await response.json();
      // Preserve existing comments when updating profile
      const updatedUserData = {
        ...data,
        comments: user?.comments || [] // Keep existing comments
      };
      setUser(updatedUserData);
      setIsEditing(false);
      updateUser(updatedUserData); // Update context
    } catch (err) {
      console.error('Error updating profile:', err);
      setEditError(Array.isArray(err) ? err : [typeof err === 'string' ? err : 'An error occurred']);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file size (e.g., max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setEditImgError(['File size must be less than 5MB']);
        return;
      }
      
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setEditImgError(['Please select a valid image file']);
        return;
      }
      
      setProfilePicture(file);
      setEditImgError(null);
    }
  };

  const handleUpload = async () => {
    if (!profilePicture) {
      setEditImgError(['Please select a file to upload']);
      return;
    }

    setUploading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        logout();
        return;
      }

      const uploadFormData = new FormData();
      uploadFormData.append('profile_picture', profilePicture);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/users/profile/image`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: uploadFormData,
      });

      if (!response.ok) {
        if (response.status === 401) {
          logout();
          return;
        }
        const errorData = await response.json();
        const errorText = parsedEditError(errorData);
        throw errorText;
      }

      const data = await response.json();
      setUser((prevUser) => ({ ...prevUser!, profile_picture: data.profile_picture }));
      updateUser({ profile_picture: data.profile_picture });
      setProfilePicture(null);
      setEditImgError(null);
    } catch (err) {
      console.error('Error uploading image:', err);
      setEditImgError(Array.isArray(err) ? err : [typeof err === 'string' ? err : 'An error occurred uploading image']);
    } finally {
      setUploading(false);
    }
  };
  
  const handleEditComment = (comment: any) => {
    setEditCommentId(comment.id);
    setEditCommentText({
      comment: comment.comment,
      rating: comment.rating,
    });
    setEditCommentError(null);
  };

  const handleCancelEditComment = () => {
    setEditCommentId(null);
    setEditCommentText({ comment: "", rating: 1 });
    setEditCommentError(null);
  };

  const handleSaveEditComment = async () => {
    if (!editCommentText.comment.trim()) {
      setEditCommentError(['Comment cannot be empty']);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        logout();
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/${editCommentId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(editCommentText),
      });

      if (!response.ok) {
        if (response.status === 401) {
          logout();
          return;
        }
        const errorData = await response.json();
        const errorText = parsedError(errorData);
        throw errorText;
      }

      const updatedComment = await response.json();
      setUser((prevUser) => {
        if (!prevUser) return null;
        return {
          ...prevUser,
          comments: prevUser.comments?.map((c) =>
            c.id === updatedComment.id 
              ? {
                  ...updatedComment,
                  movie_title: c.movie_title, // Preserve movie title
                  movie_id: c.movie_id // Preserve movie id
                }
              : c
          ) || [],
        };
      });
      setEditCommentError(null);
      setEditCommentId(null);
      setEditCommentText({ comment: "", rating: 1 });
    } catch (err) {
      console.error('Error updating comment:', err);
      setEditCommentError(['Failed to update comment. Please try again.']);
    }
  };

  const handleCommentInputChange = (field: string, value: any) => {
    setEditCommentText(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!window.confirm(t("profile.delete"))) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        logout();
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/${commentId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          logout();
          return;
        }
        const errorData = await response.json();
        const errorText = parsedError(errorData);
        throw errorText;
      }

      setUser((prevUser) => {
        if (!prevUser) return null;
        return {
          ...prevUser,
          comments: prevUser.comments?.filter(comment => comment.id !== commentId) || [],
        };
      });
    } catch (err) {
      console.error('Error deleting comment:', err);
      setError(['Failed to delete comment. Please try again.']);
    }
  };

  const handleCancelEdit = () => {
    if (user) {
      setFormData({
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        email: user.email || "",
        email_confirm: user.email || "",
        birth_year: user.birth_year ? String(user.birth_year) : "",
        gender: user.gender || "",
      });
    }
    setIsEditing(false);
    setEditError(null);
    setEditImgError(null);
    setProfilePicture(null);
  };

  // Helper function to safely render values
  const safeRender = (value: any, fallback: string = "N/A"): string => {
    if (value === null || value === undefined || value === "") return fallback;
    if (typeof value === 'object') return fallback;
    return String(value);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen p-6 bg-dark-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-white mb-4"></div>
          <p>{t("profile.loading")}</p>
        </div>
      </div>
    );
  }

  if (error && !user) {
    return (
      <div className="min-h-screen p-6 bg-dark-900 text-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded mb-4">
            {Array.isArray(error) ? error.map((err, index) => (
              <p key={index}>{err}</p>
            )) : <p>{error}</p>}
          </div>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen p-6 bg-dark-900 text-white flex items-center justify-center">
        <p>No user data available</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 bg-dark-900 text-white">
      <div className="max-w-4xl mx-auto">
        {!isEditing ? (
          <>
            {/* Profile Display Mode */}
            <div className="flex flex-col md:flex-row items-start md:items-center space-y-4 md:space-y-0 md:space-x-6 mb-8">
              <img
                src={user.profile_picture || '/default-avatar.png'}
                alt={user.username}
                className="w-32 h-32 rounded-full border-4 border-gray-600 object-cover"
              />
              <div className="flex-1">
                <div className="flex items-center mb-2">
                  <h1 className="text-3xl font-bold mr-4">{user.username}</h1>
                  <button
                    onClick={() => setIsEditing(true)} 
                    className="text-gray-400 hover:text-white transition-colors" 
                    title="Edit profile"
                  >
                    <Pencil className="h-5 w-5" />
                  </button>
                </div>
                <div className="space-y-1 text-gray-300">
                  <p><span className="font-medium">Name:</span> {safeRender(user.first_name)} {safeRender(user.last_name)}</p>
                  <p><span className="font-medium">Email:</span> {safeRender(user.email)}</p>
                  <p><span className="font-medium">{t("profile.year")}</span> {safeRender(user.birth_year)}</p>
                  <p><span className="font-medium">{t("profile.gender")}</span> {safeRender(user.gender)}</p>
                </div>
              </div>
            </div>

            {/* Comments Section */}
            <div className="mt-8">
              <h2 className="text-2xl font-semibold mb-6 text-center">{t("profile.comments")}</h2>
              {(!user.comments || user.comments.length === 0) ? (
                <div className='text-center py-12 text-gray-400'>
                  <MessageCircle className='w-16 h-16 mx-auto mb-4 opacity-50' />
                  <p>{t("profile.nocomments")}</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto rounded-lg p-4 custom-scrollbar">
                  {user.comments.map((comment) => (
                    <div key={comment.id} className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                            {user.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{user.username}</p>
                            <p className="text-xs text-gray-400">
                              {formatDate(comment.created_at)}
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          {editCommentId !== comment.id && (
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleEditComment(comment)}
                                className="text-gray-400 hover:text-blue-500 transition-colors p-1"
                                title="Edit comment"
                              >
                                <Pencil className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteComment(comment.id)}
                                className="text-gray-400 hover:text-red-500 transition-colors p-1"
                                title="Delete comment"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          )}
                          {editCommentId !== comment.id ? (
                            <div className="flex items-center gap-1">
                              {renderStars(comment.rating)}
                              <span className="ml-1 text-sm text-gray-400">
                                ({comment.rating}/5)
                              </span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1">
                              {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                  key={star}
                                  onClick={() => handleCommentInputChange('rating', star)}
                                  className={`transition-colors ${
                                    star <= editCommentText.rating
                                      ? 'text-yellow-400 hover:text-yellow-300'
                                      : 'text-gray-400 hover:text-gray-300'
                                  }`}
                                >
                                  <Star className="h-4 w-4 fill-current" />
                                </button>
                              ))}
                              <span className="ml-1 text-sm text-gray-400">
                                ({editCommentText.rating}/5)
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {editCommentId !== comment.id ? (
                        <p className="text-gray-200 leading-relaxed mb-3">{comment.comment}</p>
                      ) : (
                        <div className="mb-3">
                          <textarea
                            id="edit-comment"
                            name="edit-comment"
                            value={editCommentText.comment}
                            onChange={(e) => handleCommentInputChange('comment', e.target.value)}
                            className="w-full p-3 bg-gray-700 text-white rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={3}
                            placeholder="Write your comment..."
                            maxLength={1000}
                          />
                          <div className="flex justify-between items-center mt-2">
                            <div className="text-xs text-gray-400">
                              {editCommentText.comment.length}/1000 {t("movies.character")}
                            </div>
                            <div className="flex justify-end gap-2">
                              <button
                                onClick={handleSaveEditComment}
                                className="text-gray-400 hover:text-green-500 transition-colors p-1"
                                title="Save changes"
                              >
                                <Check className="h-4 w-4" />
                              </button>
                              <button
                                onClick={handleCancelEditComment}
                                className="text-gray-400 hover:text-red-500 transition-colors p-1"
                                title="Cancel edit"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                          {editCommentError && editCommentError.length > 0 && (
                            <div className="mt-2 text-red-500 text-xs">
                              {editCommentError.map((err, index) => (
                                <p key={index}>{err}</p>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                      
                      {comment.movie_title && (
                        <Link href={`/movies/${comment.movie_id}`} className="inline-block">
                          <div className="text-blue-400 hover:text-blue-300 hover:underline transition-colors">
                            {comment.movie_title}
                          </div>
                        </Link>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          /* Profile Edit Mode */
          <div className="mt-6">
            <h1 className="text-3xl font-bold mb-6 text-center">Edit Profile</h1>
            <div className="flex flex-col lg:flex-row items-start gap-8">
              <div className="flex-shrink-0">
                <AvatarUpload 
                  user={user}
                  handleImageChange={handleImageChange}
                  handleUpload={handleUpload}
                  uploading={uploading}
                  editError={editImgError}
                  profilePicture={profilePicture}
                  setProfilePicture={setProfilePicture}
                />
              </div>
              
              <div className="flex-1 w-full">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-300 mb-2">
                      {t("profile.firstName")} *
                    </label>
                    <input 
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleChange}
                      placeholder={t("profile.firstName")}
                      autoComplete="given-name"
                      className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-300 mb-2">
                      {t("profile.lastName")} *
                    </label>
                    <input 
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleChange}
                      placeholder={t("profile.lastName")}
                      autoComplete="family-name"
                      className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                      {t("profile.email")} *
                    </label>
                    <input 
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder={t("profile.email")}
                      autoComplete="email"
                      className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="email_confirm" className="block text-sm font-medium text-gray-300 mb-2">
                      {t("profile.confirmEmail")} *
                    </label>
                    <input 
                      type="email"
                      id="email_confirm"
                      name="email_confirm"
                      value={formData.email_confirm}
                      onChange={handleChange}
                      placeholder={t("profile.confirmEmail")}
                      autoComplete="email"
                      className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="birth_year" className="block text-sm font-medium text-gray-300 mb-2">
                      {t("profile.birth")}
                    </label>
                    <input 
                      type="number"
                      id="birth_year"
                      name="birth_year"
                      value={formData.birth_year}
                      onChange={handleChange}
                      placeholder={t("profile.birth")}
                      autoComplete="bday-year"
                      min={1900}
                      max={new Date().getFullYear()}
                      className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="gender" className="block text-sm font-medium text-gray-300 mb-2">
                      {t("profile.genderEdit")}
                    </label>
                    <select 
                      id="gender"
                      name="gender"
                      value={formData.gender}
                      onChange={handleChange}
                      autoComplete="sex"
                      className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">{t("profile.selectGender")}</option>
                      <option value="male">{t("profile.male")}</option>
                      <option value="female">{t("profile.female")}</option>
                      <option value="non-binary">{t("profile.noBinary")}</option>
                      <option value="prefer-not-to-say">{t("profile.notsay")}</option>  
                      <option value="other">{t("profile.other")}</option>
                    </select>
                  </div>
                </div>
                
                <div className="mt-6 flex gap-3">
                  <button 
                    onClick={handleSave}
                    disabled={isLoading}
                    className="bg-blue-500 px-6 py-3 rounded text-white hover:bg-blue-600 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
                  >
                    {isLoading ? 'Saving...' : t("profile.save")}
                  </button>
                  <button 
                    onClick={handleCancelEdit}
                    disabled={isLoading}
                    className="bg-gray-500 px-6 py-3 rounded text-white hover:bg-gray-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    {t("profile.cancel")}
                  </button>
                </div>
                
                {editError && editError.length > 0 && (
                  <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                    {editError.map((err, index) => (
                      <p key={index}>{err}</p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}