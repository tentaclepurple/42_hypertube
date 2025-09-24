// frontend/app/src/api/page.tsx

'use client';

import { useState } from 'react';
import { useAuth } from '../context/authcontext';
import { useTranslation } from 'react-i18next';
import { parsedError} from '../ui/error/parsedError';
import { Key, Copy, AlertTriangle, Dice1 } from 'lucide-react';

interface ApiKeyProps {
  apiKey: string;
  apiSecret: string;
}

export default function Apipage(){
    const { user, logout } = useAuth();
    const { t } = useTranslation();
    const [loading, setLoading] = useState<boolean>(false);
    const [apiKey, setApiKey] = useState<ApiKeyProps | null>(null);
    const [error, setError] = useState<string[] | null>(null);
    const [copyField, setCopyField] = useState<string>('');

    const generateApiKey = async () => {
        setLoading(true);
        setError(null);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/auth/api-keys/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ 
                    name: `${user?.username}`,
                    expires_in_days: 30,

                }),
            });

            if (!response.ok) {
                if (response.status === 401) logout();
                const errorText = parsedError(await response.json());
                return Promise.reject(errorText);
            }
            const data = await response.json();
            setApiKey({
                apiKey: data.api_key,
                apiSecret: data.api_secret,
            });
        } catch (err) {
            setError(Array.isArray(err) ? err : [String(err)]);
        } finally {
            setLoading(false);
        }
    };

    // const copyToClipboard = async (text: string, field: string) => {
    //     try {
    //         await navigator.clipboard.writeText(text);
    //         setCopyField(field);
    //         setTimeout(() => setCopyField(''), 2000);
    //     } catch (err) {
    //         console.error('Failed to copy text: ', err);
    //     }
    // };

    return (
        <div className='text-white max-w-4xl mx-auto p-6'>
            <div className='mb-8'>
                <h1 className='text-3xl font-bold mb-4 text-center'>
                    API Keys
                </h1>
                <p className='text-gray-400 text-center'>
                    {t('api.description')}
                </p>
            </div>
            <div className='bg-gray-800 p-6 rounded-lg'>
                {!apiKey ? (
                    <>
                        <div className='text-center mb-6'>
                            <Key className='mx-auto text-gray-400 mb-4' size={48} />
                            <h2 className='text-xl font-semibold mb-2'>{t('api.key_generated')}</h2>
                            <p className='text-gray-300 mb-4'>{t('api.key_info')}</p>
                        </div>
                        
                        {error && (
                            <div className='text-red-500 text-center'>
                                {error.map((err, index) => (
                                    <p key={index}>{err}</p>
                                ))}
                            </div>
                        )}
                        <button
                            onClick={generateApiKey}
                            className=' hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 mx-auto'
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                                        {t('api.generating')}
                                </>
                            ) : (
                                <>
                                    <Key size={20}/>
                                    {t('api.button')}
                                </>
                            )}
                        </button>
                    </>
                ) : (
                    <div className='space-y-6'>
                        <div className='bg-yellow-900/20 border border-yellow-500 p-4 rounded-lg'>
                            <div className='flex items-center gap-2 mb-2'>
                                <AlertTriangle className='text-yellow-500' size={20} />
                                <h3 className='text-yellow-300 font-semibold'>{t('api.important')}</h3>
                            </div>
                            <p className='text-gray-300'>{t('api.warning_info')}</p>
                        </div>

                        <div className='space-y-4'>
                            <div>
                                <label className='block text-sm font-medium text-gray-300 mb-2'>
                                    API KEY
                                </label>
                                <div className='flex items-center gap-2'>
                                    <div className='flex-1 text-gray-200 break-allflex-1 px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white font-mono text-sm break-all'>
                                        {apiKey.apiKey}
                                    </div>
                                    {/* <button
                                        onClick={() => copyToClipboard(apiKey.apiKey, 'apiKey')}
                                        className='px-4 py-3 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 whitespace-nowrap'
                                    >
                                        <Copy size={16} />
                                        {copyField === 'apiKey' ? t('api.copied') : t('api.copy')}
                                    </button> */}
                                </div>
                            </div>
                            <div>
                                <label className='block text-sm font-medium text-gray-300 mb-2'>
                                    API SECRET
                                </label>
                                <div className='flex items-center gap-2'>
                                    <div className='flex-1 text-gray-200 break-all px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white font-mono text-sm break-all'>
                                        {apiKey.apiSecret}
                                    </div>
                                    {/* <button
                                        onClick={() => copyToClipboard(apiKey.apiSecret, 'apiSecret')}
                                        className='px-4 py-3 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 whitespace-nowrap'
                                    >
                                        <Copy size={16} />
                                        {copyField === 'apiSecret' ? t('api.copied') : t('api.copy')}
                                    </button> */}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}


