"use client";

import React, { useEffect, useState } from "react";
import { useAuth, User } from "../context/authcontext";
import { Pencil, Camera, Upload, X, MessageCircle, Trash2, Check, Star } from "lucide-react";
import { parsedError, parsedEditError } from "../ui/error/parsedError";
import Link from "next/link";
import { formatDate, renderStars } from "../ui/comments";

function AvatarUpload({
    user,
    handleImageChange,
    handleUpload,
    uploading,
    editError,
    profilePicture,
    setProfilePicture
}: {
    user: User;
    handleImageChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
    handleUpload: () => void;
    uploading: boolean;
    editError: string[] | null;
    profilePicture: File | null;
    setProfilePicture: (file: File | null) => void;
}) {
  const [hover, setHover] = useState(false);
  const [previewURL, setPreviewURL] = useState<string | null>(null);

  useEffect(() => {
    if(profilePicture) {
      const url = URL.createObjectURL(profilePicture);
      setPreviewURL(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewURL(null);
    }
  },[profilePicture]);

  const handleCancel = () => {
    setProfilePicture(null);
    setPreviewURL(null);

    const input = document.getElementById('avatar-upload') as HTMLInputElement;
    if (input) {
      input.value = '';
    }
  }

  return (
    <div className="flex flex-col items-center">
      <div 
        className="relative group"
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        <img
          src={previewURL || user?.profile_picture || '/default-avatar.png'}
          alt={user.username}
          className="w-32 h-32 rounded-full border-4 border-gray-600"
        />
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          className="hidden"
          id="avatar-upload"
        />
        <label
          htmlFor="avatar-upload"
          className={`absolute inset-0 bg-black bg-opacity-50 rounded-full flex items-center justify-center cursor-pointer 
            ${hover ? 'opacity-75' : 'opacity-0'} 
            transition-opacity duration-300 ease-in-out`}
          title="Change profile picture"
        >
          <Camera className="h-8 w-8 text-white" />
        </label>
      </div>

      {uploading ? (
        <div className="mt-4 flex items-center">
          <div className="animate-spin mr-2">
            <Upload className="text-blue-500" />
          </div>
          <span className="text-sm text-gray-400">Uploading...</span>
      </div>
      ) : (
        <>
          {profilePicture && (
            <div className="mt-4 flex  flex-col space-x-2">
              <button
                onClick={handleUpload}
                className="w-full mt-4 bg-blue-500 text-white px-4 py-2 rounded-md flex items-center hover:bg-blue-600 transition"
              >
                <Upload className="mr-2 w-5 h-5" />
                Upload
              </button>
              <button
                onClick={handleCancel}
                className="w-full mt-4 bg-gray-500 text-white px-4 py-2 rounded-md flex items-center hover:bg-gray-600 transition"
              >
                <X className="mr-2 w-5 h-5" />
                Cancel
              </button>
            </div>
          )}
          {editError && (
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
  const [error, setError] = useState <string[] | null>(null);
  const [editError, setEditError] = useState <string[] | null>(null);
  const [editImgError, setEditImgError] = useState <string[] | null>(null);
  const [isEditing, setEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [profilePicture, setProfilePicture] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [editCommentId, setEditCommentId] = useState<string | null>(null);
  const [editCommentText, setEditCommentText] = useState({
    comment: "",
    rating: 1,
  });
  const [editCommentError, setEditCommentError] = useState<string[] | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/users/me`, {
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
      const token = localStorage.getItem('token');
      fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/users/profile`, {
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
  
  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setProfilePicture(file);
      setEditImgError(null);
    }
  }

  const handleUpload = () => {
    if (!profilePicture) {
      setEditImgError(['Please select a file to upload']);
      return 
    }
    setUploading(true);
    const formData = new FormData();
    const token = localStorage.getItem('token');
    formData.append('profile_picture', profilePicture);
    fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/users/profile/image`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    })
    .then(async (response) => {
      if (!response.ok) {
        if (response.status === 401) logout();
        const text = parsedEditError(await response.json());
        return Promise.reject(text);
      }
      return response.json();
    })
    .then((data) => {
      setUser((prevUser) => ({ ...prevUser!, profile_picture: data.profile_picture }));
      updateUser({ profile_picture: data.profile_picture });
      setProfilePicture(null);
    })
    .catch((err) => {
      setEditImgError(err);
    })
    .finally(() => {
      setUploading(false);
    });
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
      const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/${editCommentId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(editCommentText),
      });

      if (!response.ok) {
        if (response.status === 401) logout();
        const data = parsedError(await response.json());
        return Promise.reject(data);
      }

      const updatedComment = await response.json();
      setUser((prevUser) => {
        if (!prevUser) return null;
        return {
          ...prevUser,
          comments: prevUser.comments.map((c) =>
            c.id === updatedComment.id ? updatedComment : c
          ),
        };
      });
      setEditCommentError(null);
      setEditCommentId(null);
      setEditCommentText({ comment: "", rating: 1 });
    } catch (err) {
      setEditCommentError(err as string[]);
    }
  };

  const handleCommentInputChange = (field: string, value: any) => {
    setEditCommentText(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDeleteComment = async (commentId: string) => {
    if (window.confirm("Are you sure you want to delete this comment?")) {
      const token = localStorage.getItem('token');
      fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/${commentId}`, {
        method: 'DELETE',
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
        setUser((prevUser) => {
          if (!prevUser) return null;
          return {
            ...prevUser,
            comments: prevUser.comments.filter(comments => comments.id !== commentId),
          };
        });
      }).catch((err) => {
        setError(err);
      });
    }
  };
  return (
    < div className=" p-6 bg-dark-900 text-white" >
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
            <>
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
              <div className="mt-6">
                <h2 className="text-2xl font-semibold mb-4 text-center">Recent comments</h2>
                {user.comments.length == 0 ? (
                  <div className='text-center py-8 text-gray-400'>
                    <MessageCircle className='iw-12 h-12 mx-auto mb-2 opacity-50' />
                    <p>No recent comments found.</p>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-96 overflow-y-auto rounded-lg p-4">
                  {user.comments.map((comment) => (
                    <div key={comment.id} className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
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
                                className="text-gray-400 hover:text-blue-500 transition-colors"
                                title="Edit comment"
                              >
                                <Pencil className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteComment(comment.id)}
                                className="text-gray-400 hover:text-red-500 transition-colors"
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
                        <p className="text-gray-200 leading-relaxed mb-2">{comment.comment}</p>
                      ) : (
                        <div className="mb-2">
                          <textarea
                            id="edit-comment"
                            name="edit-comment"
                            value={editCommentText.comment}
                            onChange={(e) => handleCommentInputChange('comment', e.target.value)}
                            className="w-full p-2 bg-gray-700 text-white rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={3}
                            placeholder="Write your comment..."
                            maxLength={1000}
                          />
                          <div className="flex justify-between items-center mt-2">
                            <div className="text-xs text-gray-400">
                              {editCommentText.comment.length}/1000 characters
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
                          {editCommentError&& (
                            <div className="mt-1 text-red-500 text-xs">
                              {editCommentError.map((err, index) => (
                                <p key={index}>{err}</p>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                      {comment.movie_title && (
                        <Link href={`/movies/${comment.movie_id}`} >
                          <div className="text-blue-500 hover:underline">
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
          ):(
            <div className="mt-6">
                <div className="flex flex-col md:flex-row items-start gap-6">
                  <AvatarUpload 
                    user={user}
                    handleImageChange={handleImageChange}
                    handleUpload={handleUpload}
                    uploading={uploading}
                    editError={editImgError}
                    profilePicture={profilePicture}
                    setProfilePicture={setProfilePicture}
                  />
                  <div className="flex-1">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="first_name" className="block text-sm font-medium text-gray-300 mb-1">
                          First Name
                        </label>
                        <input 
                          type="text"
                          id="first_name"
                          name="first_name"
                          value={formData.first_name}
                          onChange={handleChange}
                          placeholder="First Name"
                          autoComplete="given-name"
                          className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.first_name ? 'border border-red-500' : ''}`}
                          />
                      </div>
                      <div>
                        <label htmlFor="last_name" className="block text-sm font-medium text-gray-300 mb-1">
                          Last Name
                        </label>
                        <input 
                          type="text"
                          id="last_name"
                          name="last_name"
                          value={formData.last_name}
                          onChange={handleChange}
                          placeholder="Last Name"
                          autoComplete="family-name"
                          className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.last_name ? 'border border-red-500' : ''}`}
                          />
                      </div>
                      <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">
                          Email
                        </label>
                        <input 
                          type="email"
                          id="email"
                          name="email"
                          value={formData.email}
                          onChange={handleChange}
                          placeholder="Email"
                          autoComplete="email"
                          className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.email ? 'border border-red-500' : ''}`}
                          />
                      </div>
                      <div>
                        <label htmlFor="birth_year" className="block text-sm font-medium text-gray-300 mb-1">
                          Year of Birth
                        </label>
                        <input 
                          type="number"
                          id="birth_year"
                          name="birth_year"
                          value={formData.birth_year}
                          onChange={handleChange}
                          placeholder="Year of Birth"
                          autoComplete="bday-year"
                          min={1900}
                          max={new Date().getFullYear()}
                          className={`w-full p-2 bg-gray-700 text-white rounded ${editError?.birth_year ? 'border border-red-500' : ''}`}
                          />
                      </div>
                      <div>
                        <label htmlFor="gender" className="block text-sm font-medium text-gray-300 mb-1">
                          Gender
                        </label>
                        <select 
                          id="gender"
                          name="gender"
                          value={formData.gender}
                          onChange={handleChange}
                          autoComplete="sex"
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
                        onClick={() => {setEditing(false), setEditError(null), setEditImgError(null)}}
                        className="ml-2 bg-gray-500 px-4 py-2 rounded text-white hover:bg-gray-600">
                          Cancel
                        </button>
                    {editError && (
                      <div className="mt-2 text-red-500 text-sm">
                        {Object.entries(editError).map(([field, message]) => (
                          <p key={field}>
                            <strong>{field}:</strong> {message}
                          </p>
                        ))}
                      </div>
                    )}
                    </div>
                  </div>
                </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}