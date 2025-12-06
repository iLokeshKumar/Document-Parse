'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';

export default function VerifyEmailPage() {
    const searchParams = useSearchParams();
    const token = searchParams.get('token');
    const [status, setStatus] = useState('Verifying...');
    const [error, setError] = useState('');
    const router = useRouter();

    useEffect(() => {
        if (!token) {
            setStatus('');
            setError('No verification token found.');
            return;
        }

        const verify = async () => {
            try {
                const res = await fetch('http://localhost:8000/auth/verify-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token }),
                });

                if (!res.ok) {
                    const data = await res.json();
                    throw new Error(data.detail || 'Verification failed');
                }

                setStatus('Email verified successfully!');
            } catch (err: any) {
                setStatus('');
                setError(err.message);
            }
        };

        verify();
    }, [token]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md text-center">
                <h2 className="text-2xl font-bold mb-4">Email Verification</h2>

                {error ? (
                    <div className="text-red-600 mb-4">{error}</div>
                ) : (
                    <div className="text-green-600 mb-4">{status}</div>
                )}

                <Link href="/login" className="inline-block bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">
                    Go to Login
                </Link>
            </div>
        </div>
    );
}
