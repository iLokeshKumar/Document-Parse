'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function MFASetupPage() {
    const [secret, setSecret] = useState('');
    const [otpAuthUrl, setOtpAuthUrl] = useState('');
    const [code, setCode] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [mfaEnabled, setMfaEnabled] = useState(false);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const checkMfaStatus = async () => {
            const token = localStorage.getItem('token');
            if (!token) {
                router.push('/login');
                return;
            }

            try {
                // Try to setup - if already enabled, we'll get an error
                const res = await fetch('http://localhost:8000/auth/mfa/setup', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!res.ok) {
                    const data = await res.json();
                    if (data.detail === "MFA is already enabled") {
                        setMfaEnabled(true);
                        setLoading(false);
                        return;
                    }
                    throw new Error('Failed to check MFA status');
                }

                const data = await res.json();
                setSecret(data.secret);
                setOtpAuthUrl(data.otpauth_url);
                setMfaEnabled(false);
                setLoading(false);
            } catch (err: any) {
                setError(err.message);
                setLoading(false);
            }
        };

        checkMfaStatus();
    }, [router]);

    const handleEnable = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:8000/auth/mfa/enable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ code }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to enable MFA');
            }

            setSuccess("MFA Enabled Successfully!");
            setTimeout(() => router.push('/'), 2000);
        } catch (err: any) {
            setError(err.message);
        }
    };

    const handleDisable = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:8000/auth/mfa/disable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ code }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to disable MFA');
            }

            setSuccess("MFA Disabled Successfully!");
            setTimeout(() => router.push('/'), 2000);
        } catch (err: any) {
            setError(err.message);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-gray-600">Loading...</div>
            </div>
        );
    }

    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="p-8 bg-white rounded shadow text-center">
                    <h2 className="text-xl font-bold text-green-600">{success}</h2>
                    <button onClick={() => router.push('/')} className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
                        Go Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md">
                <h2 className="text-2xl font-bold mb-6 text-center">
                    {mfaEnabled ? 'Disable' : 'Setup'} Multi-Factor Authentication
                </h2>

                {!mfaEnabled && otpAuthUrl && (
                    <div className="mb-6 flex flex-col items-center">
                        <p className="mb-4 text-sm text-gray-600 text-center">
                            Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
                        </p>
                        <img
                            src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(otpAuthUrl)}`}
                            alt="MFA QR Code"
                            className="mb-4 border p-2"
                        />
                        <p className="text-xs text-gray-500">Secret: {secret}</p>
                    </div>
                )}

                {mfaEnabled && (
                    <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
                        <p className="text-sm text-yellow-800">
                            ⚠️ MFA is currently enabled. Enter your current MFA code to disable it.
                        </p>
                    </div>
                )}

                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Enter the 6-digit code from your app
                    </label>
                    <input
                        type="text"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        className="w-full p-2 border rounded text-gray-900 focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="123456"
                    />
                </div>

                {error && <div className="text-red-500 text-sm mb-4 text-center">{error}</div>}

                <button
                    onClick={mfaEnabled ? handleDisable : handleEnable}
                    className={`w-full py-2 rounded text-white ${mfaEnabled
                            ? 'bg-red-600 hover:bg-red-700'
                            : 'bg-indigo-600 hover:bg-indigo-700'
                        }`}
                >
                    {mfaEnabled ? 'Disable MFA' : 'Enable MFA'}
                </button>

                <button
                    onClick={() => router.push('/')}
                    className="w-full mt-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                >
                    Cancel
                </button>
            </div>
        </div>
    );
}
