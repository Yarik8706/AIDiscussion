/**
 * Firebase initialization
 * This script is loaded first to ensure Firebase is properly initialized
 */

// Ensure console.log is available
if (!window.console) window.console = { log: function() {} };

// Log Firebase initialization
console.log('Initializing Firebase...');

// Globals for tracking Firebase state
window.firebaseInitialized = false;
window.firebaseUser = null;

/**
 * Initialize Firebase with the given config
 * 
 * @param {Object} config The Firebase configuration object
 */
function initializeFirebase(config) {
    if (window.firebaseInitialized) {
        console.log('Firebase already initialized, skipping');
        return;
    }

    console.log('Firebase config:', config);

    try {
        // Check if required Firebase SDK is loaded
        if (typeof firebase === 'undefined') {
            console.error('Firebase SDK not loaded!');
            return;
        }

        // Initialize Firebase
        firebase.initializeApp(config);
        window.firebaseInitialized = true;
        console.log('Firebase initialized successfully');

        // Set up auth state listener
        firebase.auth().onAuthStateChanged(function(user) {
            window.firebaseUser = user;
            if (user) {
                console.log('Firebase user signed in:', user.email);
                
                // Get token
                user.getIdToken().then(function(token) {
                    console.log('Firebase token obtained');
                    // Store token in localStorage and cookie
                    localStorage.setItem('firebaseToken', token);
                    
                    // Set cookie
                    const date = new Date();
                    date.setTime(date.getTime() + (7 * 24 * 60 * 60 * 1000));
                    const expires = '; expires=' + date.toUTCString();
                    document.cookie = 'firebaseToken=' + token + expires + '; path=/; SameSite=Lax';
                    
                    // Dispatch custom event
                    const event = new CustomEvent('firebaseUserSignedIn', { detail: { user, token } });
                    document.dispatchEvent(event);
                });
            } else {
                console.log('No Firebase user signed in');
                // Remove token
                localStorage.removeItem('firebaseToken');
                document.cookie = 'firebaseToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
                
                // Dispatch custom event
                const event = new CustomEvent('firebaseUserSignedOut');
                document.dispatchEvent(event);
            }
        });
    } catch (error) {
        console.error('Firebase initialization error:', error);
    }
} 