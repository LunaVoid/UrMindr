import { useState, useEffect } from 'react';
import app from './firebase';
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from 'firebase/auth';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);

  const auth = getAuth(app);
  const provider = new GoogleAuthProvider();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setUser(user);
      } else {
        setUser(null);
      }
    });

    return () => unsubscribe();
  }, [auth]);

  const handleSignIn = async () => {
    setError(null);
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      setError(error.message);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <div className="App">
      {user ? (
        <div>
          <h2>Welcome, {user.displayName}</h2>
          <button onClick={handleSignOut}>Sign Out</button>
        </div>
      ) : (
        <div>
          <h2>Urmindr</h2>
          <p>Your personal AI assistant for managing your tasks.</p>
          <button onClick={handleSignIn}>Sign In with Google</button>
          {error && <p>{error}</p>}
        </div>
      )}
    </div>
  );
}

export default App;
