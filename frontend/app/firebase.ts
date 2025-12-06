// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics, isSupported } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBrtu1yYhsZxSmYsV3gMz_RBD9wDx3KC7k",
    authDomain: "legal-ai-aut.firebaseapp.com",
    projectId: "legal-ai-aut",
    storageBucket: "legal-ai-aut.firebasestorage.app",
    messagingSenderId: "1007040981424",
    appId: "1:1007040981424:web:864af15e599baccdf8ce75",
    measurementId: "G-7Y5TCVG1K4"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

// Initialize Analytics only if supported (client-side)
let analytics;
if (typeof window !== 'undefined') {
    isSupported().then((supported) => {
        if (supported) {
            analytics = getAnalytics(app);
        }
    });
}

export { app, analytics };
