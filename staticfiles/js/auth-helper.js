/**
 * Firebase Authentication Helper
 * This file adds the Firebase authentication token to all AJAX requests.
 */

(function() {
    // Function to set a cookie
    function setCookie(name, value, days) {
        let expires = '';
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = '; expires=' + date.toUTCString();
        }
        document.cookie = name + '=' + (value || '') + expires + '; path=/; SameSite=Lax';
    }
    
    // Function to get a cookie
    function getCookie(name) {
        const nameEQ = name + '=';
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    // Function to update Firebase token in both localStorage and cookies
    function syncFirebaseToken() {
        const token = localStorage.getItem('firebaseToken');
        const cookieToken = getCookie('firebaseToken');
        
        if (token && token !== cookieToken) {
            setCookie('firebaseToken', token, 7); // Store for 7 days
            console.log('Firebase token synced to cookies');
        }
    }
    
    // Sync token on load
    syncFirebaseToken();
    
    // Check periodically for token changes
    setInterval(syncFirebaseToken, 5000);
    
    // Original XHR open method
    const originalXhrOpen = XMLHttpRequest.prototype.open;
    
    // Override XHR open to add auth token before sending request
    XMLHttpRequest.prototype.open = function() {
        // Call the original open method
        originalXhrOpen.apply(this, arguments);
        
        // Add event listener to add auth token before the request is sent
        this.addEventListener('loadstart', function() {
            const token = localStorage.getItem('firebaseToken');
            if (token) {
                this.setRequestHeader('Authorization', `Bearer ${token}`);
            }
        });
    };
    
    // Add token to fetch requests too
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        const token = localStorage.getItem('firebaseToken');
        
        if (token) {
            options.headers = options.headers || {};
            
            // Handle both Headers object and plain object
            if (options.headers instanceof Headers) {
                if (!options.headers.has('Authorization')) {
                    options.headers.append('Authorization', `Bearer ${token}`);
                }
            } else {
                if (!options.headers['Authorization']) {
                    options.headers['Authorization'] = `Bearer ${token}`;
                }
            }
        }
        
        return originalFetch(url, options);
    };
    
    // Watch for auth changes from Firebase directly
    if (typeof firebase !== 'undefined' && firebase.auth) {
        console.log("Auth helper: setting up token synchronization");
        // We'll only handle token storage, not signout
        firebase.auth().onAuthStateChanged(function(user) {
            if (user) {
                console.log("Auth helper: User authenticated, syncing token");
                user.getIdToken().then(token => {
                    localStorage.setItem('firebaseToken', token);
                    setCookie('firebaseToken', token, 7);
                    console.log('Auth helper: Firebase token synced');
                });
            } else {
                console.log("Auth helper: User signed out noted (not taking action)");
                // We don't remove tokens here, let the main handler do that
            }
        });
    }
    
    console.log('Auth helper initialized - all AJAX requests will include Firebase token');
})(); 