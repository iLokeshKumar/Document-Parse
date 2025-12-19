'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DocumentsArchivePage() {
    const router = useRouter();
    const [userRole, setUserRole] = useState<string | null>(null);
    const [documents, setDocuments] = useState<any[]>([]);
    const [skip, setSkip] = useState(0);
    const [limit] = useState(10);
    const [totalCount, setTotalCount] = useState(0);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/login');
            return;
        }

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const role = payload.role || 'paralegal';
            setUserRole(role);

            if (role !== 'admin' && role !== 'lawyer') {
                alert("Access Denied: You do not have permission to view this page.");
                router.push('/');
            }
        } catch (error) {
            console.error('Failed to decode token:', error);
            router.push('/login');
        }
    }, [router]);

    const fetchDocuments = async () => {
        try {
            const token = localStorage.getItem('token');
            // Fetch Docs
            const res = await fetch(`http://localhost:8000/documents?skip=${skip}&limit=${limit}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setDocuments(data);
            }

            // Fetch Count
            const countRes = await fetch('http://localhost:8000/documents/count', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (countRes.ok) {
                const data = await countRes.json();
                setTotalCount(data.count);
            }

        } catch (e) {
            console.error("Failed to fetch documents", e);
        }
    };

    useEffect(() => {
        if (userRole === 'admin' || userRole === 'lawyer') {
            fetchDocuments();
        }
    }, [userRole, skip]);

    const handleDeleteDocument = async (id: number) => {
        if (!confirm("Are you sure you want to delete this document? This cannot be undone.")) return;

        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`http://localhost:8000/documents/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                alert("Document deleted successfully");
                fetchDocuments(); // Refresh list
            } else {
                alert("Failed to delete document");
            }
        } catch (e) {
            console.error("Delete failed", e);
        }
    };

    const handleNext = () => {
        if (skip + limit < totalCount) {
            setSkip(skip + limit);
        }
    };

    const handlePrev = () => {
        if (skip - limit >= 0) {
            setSkip(skip - limit);
        }
    };

    return (
        <main className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-800">Uploaded Documents Archive</h1>
                    <a href="/" className="text-indigo-600 hover:text-indigo-800 font-medium">
                        &larr; Back to Chat
                    </a>
                </div>

                <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-semibold text-gray-700">All Files ({totalCount})</h2>
                        <span className="text-sm text-gray-500">Page {Math.floor(skip / limit) + 1} of {Math.ceil(totalCount / limit) || 1}</span>
                    </div>

                    {documents.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">No documents found.</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Filename</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date Uploaded</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {documents.map((doc) => (
                                        <tr key={doc.id}>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{doc.filename}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(doc.upload_date).toLocaleString()}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <button
                                                    onClick={() => handleDeleteDocument(doc.id)}
                                                    className="text-red-600 hover:text-red-900 bg-red-50 px-3 py-1 rounded hover:bg-red-100 transition-colors"
                                                >
                                                    Delete
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Pagination Controls */}
                    <div className="mt-6 flex justify-between items-center pt-4 border-t border-gray-200">
                        <button
                            onClick={handlePrev}
                            disabled={skip === 0}
                            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <div className="text-sm text-gray-600">
                            Showing {skip + 1} to {Math.min(skip + limit, totalCount)} of {totalCount} results
                        </div>
                        <button
                            onClick={handleNext}
                            disabled={skip + limit >= totalCount}
                            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>
        </main>
    );
}
