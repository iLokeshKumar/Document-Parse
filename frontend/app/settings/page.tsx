'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { auth } from '../firebase';
import { RecaptchaVerifier, signInWithPhoneNumber, PhoneAuthProvider, signInWithCredential } from 'firebase/auth';

export default function SettingsPage() {
    const [password, setPassword] = useState('');
    const [confirmDelete, setConfirmDelete] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    // User info
    const [userEmail, setUserEmail] = useState('');
    const [userRole, setUserRole] = useState('');

    // MFA
    const [mfaEnabled, setMfaEnabled] = useState(false);
    const [mfaCode, setMfaCode] = useState('');
    const [secret, setSecret] = useState('');
    const [otpAuthUrl, setOtpAuthUrl] = useState('');
    const [showMfaSetup, setShowMfaSetup] = useState(false);
    const [emailOtp, setEmailOtp] = useState('');
    const [showEmailOtp, setShowEmailOtp] = useState(false);

    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/login');
            return;
        }

        // Decode JWT to get user info
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            setUserEmail(payload.sub || 'Unknown');
            setUserRole(payload.role || 'user');
        } catch (error) {
            console.error('Failed to decode token:', error);
        }

        // Check MFA status
        checkMfaStatus();
    }, [router]);

    const checkMfaStatus = async () => {
        const token = localStorage.getItem('token');
        try {
            const res = await fetch('http://localhost:8000/auth/mfa/setup', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) {
                const data = await res.json();
                if (data.detail === "MFA is already enabled") {
                    setMfaEnabled(true);
                }
            } else {
                const data = await res.json();
                setSecret(data.secret);
                setOtpAuthUrl(data.otpauth_url);
                setMfaEnabled(false);
            }
        } catch (err) {
            console.error('Failed to check MFA status:', err);
        }
    };

    const handleEnableMfa = async () => {
        setError('');
        setSuccess('');
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:8000/auth/mfa/enable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ code: mfaCode }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to enable MFA');
            }

            setSuccess("MFA Enabled Successfully!");
            setMfaEnabled(true);
            setShowMfaSetup(false);
            setMfaCode('');
        } catch (err: any) {
            setError(err.message);
        }
    };

    const handleDisableMfa = async () => {
        setError('');
        setSuccess('');
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:8000/auth/mfa/disable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ code: mfaCode }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to disable MFA');
            }

            const data = await res.json();
            if (data.status === 'otp_sent') {
                setSuccess("OTP sent to your email. Please check your inbox.");
                setShowEmailOtp(true);
                setMfaCode('');
            }
        } catch (err: any) {
            setError(err.message);
        }
    };

    const handleVerifyEmailOtp = async () => {
        setError('');
        setSuccess('');
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:8000/auth/mfa/disable/verify-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ otp: emailOtp }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to verify OTP');
            }

            setSuccess("MFA Disabled Successfully!");
            setMfaEnabled(false);
            setEmailOtp('');
            setShowEmailOtp(false);
        } catch (err: any) {
            setError(err.message);
        }
    };

    const handleDeleteAccount = async () => {
        if (!password) {
            setError('Please enter your password');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:8000/auth/account', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ password }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to delete account');
            }

            localStorage.removeItem('token');
            alert('Account deleted successfully');
            router.push('/login');
        } catch (err: any) {
            setError(err.message);
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            <div className="max-w-2xl w-full p-8 bg-white rounded-lg shadow-md">
                <h2 className="text-2xl font-bold mb-6 text-center">Account Settings</h2>

                {/* User Information */}
                <div className="mb-8 p-4 bg-gray-50 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">Account Information</h3>
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <span className="text-gray-600">Email:</span>
                            <span className="font-medium text-gray-900">{userEmail}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Role:</span>
                            <span className="font-medium text-gray-900 capitalize">{userRole}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">MFA Status:</span>
                            <span className={`font-medium ${mfaEnabled ? 'text-green-600' : 'text-gray-500'}`}>
                                {mfaEnabled ? '✓ Enabled' : '✗ Disabled'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* MFA Management */}
                <div className="mb-8 p-4 border border-gray-200 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">Multi-Factor Authentication</h3>

                    {!mfaEnabled && !showMfaSetup && (
                        <div>
                            <p className="text-sm text-gray-600 mb-4">
                                Add an extra layer of security to your account with MFA.
                            </p>
                            <button
                                onClick={() => setShowMfaSetup(true)}
                                className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700"
                            >
                                Enable MFA
                            </button>
                        </div>
                    )}

                    {!mfaEnabled && showMfaSetup && otpAuthUrl && (
                        <div>
                            <div className="mb-4 flex flex-col items-center">
                                <p className="mb-3 text-sm text-gray-600 text-center">
                                    Scan this QR code with your authenticator app
                                </p>
                                <img
                                    src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(otpAuthUrl)}`}
                                    alt="MFA QR Code"
                                    className="mb-3 border p-2"
                                />
                                <p className="text-xs text-gray-500">Secret: {secret}</p>
                            </div>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Enter 6-digit code
                                </label>
                                <input
                                    type="text"
                                    value={mfaCode}
                                    onChange={(e) => setMfaCode(e.target.value)}
                                    className="w-full p-2 border rounded text-gray-900"
                                    placeholder="123456"
                                />
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleEnableMfa}
                                    className="flex-1 bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700"
                                >
                                    Confirm
                                </button>
                                <button
                                    onClick={() => setShowMfaSetup(false)}
                                    className="flex-1 border border-gray-300 py-2 rounded hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}

                    {mfaEnabled && (
                        <div>
                            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded">
                                <p className="text-sm text-green-800">
                                    ✓ MFA is currently enabled on your account
                                </p>
                            </div>

                            {!showEmailOtp ? (
                                <>
                                    <div className="mb-4">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Step 1: Enter current MFA code
                                        </label>
                                        <input
                                            type="text"
                                            value={mfaCode}
                                            onChange={(e) => setMfaCode(e.target.value)}
                                            className="w-full p-2 border rounded text-gray-900"
                                            placeholder="123456"
                                        />
                                    </div>
                                    <button
                                        onClick={handleDisableMfa}
                                        className="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700"
                                    >
                                        Request Email OTP
                                    </button>
                                </>
                            ) : (
                                <>
                                    <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
                                        <p className="text-sm text-blue-800">
                                            📧 OTP sent to your email. Check your inbox.
                                        </p>
                                    </div>
                                    <div className="mb-4">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Step 2: Enter email OTP
                                        </label>
                                        <input
                                            type="text"
                                            value={emailOtp}
                                            onChange={(e) => setEmailOtp(e.target.value)}
                                            className="w-full p-2 border rounded text-gray-900"
                                            placeholder="123456"
                                        />
                                    </div>
                                    <button
                                        onClick={handleVerifyEmailOtp}
                                        className="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700"
                                    >
                                        Verify OTP & Disable MFA
                                    </button>
                                </>
                            )}
                        </div>
                    )}
                </div>

                {/* Messages */}
                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
                        {error}
                    </div>
                )}
                {success && (
                    <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-green-800 text-sm">
                        {success}
                    </div>
                )}

                {/* Delete Account */}
                <div className="mb-8 p-4 border border-red-200 rounded-lg bg-red-50">
                    <h3 className="text-lg font-semibold text-red-800 mb-3">Danger Zone</h3>

                    <div className="p-3 bg-white border border-red-200 rounded mb-4">
                        <p className="text-sm text-red-800">
                            ⚠️ <strong>Warning:</strong> This action is permanent and cannot be undone.
                        </p>
                    </div>

                    <div className="mb-4">
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                checked={confirmDelete}
                                onChange={(e) => setConfirmDelete(e.target.checked)}
                                className="mr-2"
                            />
                            <span className="text-sm text-gray-700">
                                I understand this action is permanent
                            </span>
                        </label>
                    </div>

                    {confirmDelete && (
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Enter your password to confirm
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full p-2 border rounded text-gray-900"
                                placeholder="Your password"
                            />
                        </div>
                    )}

                    <button
                        onClick={handleDeleteAccount}
                        disabled={!confirmDelete || loading}
                        className="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Deleting...' : 'Delete My Account'}
                    </button>
                </div>

                <button
                    onClick={() => router.push('/')}
                    className="w-full py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                >
                    Back to Home
                </button>
            </div>
        </div>
    );
}
