"use client";
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useAuth, User } from '../../context/authcontext';
import { MessageCircle, Calendar, UserIcon } from 'lucide-react';
import { parsedError } from '../../ui/error/parsedError';
import { formatDate, renderStars } from '../../ui/comments';
import { useTranslation } from 'react-i18next';

export default function UserPublicProfile() {
  const { logout } = useAuth();
  const { username } = useParams();
  const [userProfile, setUserProfile] = useState<User | null>(null);
  const [error, setError] = useState<string[] | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { t } = useTranslation();

  useEffect(() => {
      const token = localStorage.getItem('token');
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
        <div className="p-6 bg-dark-900 text-white ">
          <div className="text-center mt-4 py-2">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
            <p className="mt-2">{t("profile.userloading")}</p>
          </div>
        </div>
      );
    }

  if (!userProfile) {
      return (
        <div className="p-6 bg-dark-900 text-white ">
          <div className="text-center mt-4 py-2">
            <p className="text-lg">{t("profile.notfound")}</p>
          </div>
        </div>
      );
    }
  
  return (
      <div className="p-6 bg-dark-900 text-white ">
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
                  <span>{t("profile.born")} {userProfile.birth_year}</span>
                  </div>
              )}
              {userProfile.gender && (
                  <div className="flex items-center mt-1 text-gray-400">
                  <UserIcon className="h-4 w-4 mr-2" />
                  <span className="capitalize">{t(`profile.allGenders.${userProfile.gender}`)}</span>
                  </div>
              )}
            </div>
          </div>
          <div>
            <h2 className="text-2xl font-semibold mb-4 text-center">{t("profile.comments")}</h2>
            {userProfile.comments.length == 0 ? (
              <div className='text-center py-8 text-gray-400'>
                <MessageCircle className='iw-12 h-12 mx-auto mb-2 opacity-50' />
                <p>{t("profile.nocomments")}</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto rounded-lg p-4">
              {userProfile.comments.map((comment) => (
                <div key={comment.id} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                        {userProfile.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium">{userProfile.username}</p>
                        <p className="text-xs text-gray-400">
                          {formatDate(comment.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {renderStars(comment.rating)}
                      <span className="ml-1 text-sm text-gray-400">
                        ({comment.rating}/5)
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-200 leading-relaxed mb-2">{comment.comment}</p>
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
      </div>
    </div>
  );
}


