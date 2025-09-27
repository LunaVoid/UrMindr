import { Link, useNavigate} from 'react-router-dom';
import { getAuth, signOut, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';

function Navbar({ setAccessToken, user }) {
  const auth = getAuth();
  const provider = new GoogleAuthProvider();
  provider.addScope("https://www.googleapis.com/auth/calendar.readonly");

  const navigate = useNavigate();

  const handleSignIn = async () => {
    try {
      await signInWithPopup(auth, provider);

    } catch (error) {
      console.error('Error signing in:', error);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut(auth);
      setAccessToken(null);
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const handleCalendarClick = () => {
    navigate('/calendar'); 
  };

  const handleConnectCalendar = () => {
  /* global google */
  if (window.google) {
    const client = google.accounts.oauth2.initCodeClient({
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,  // from Google Cloud Console
      scope: "https://www.googleapis.com/auth/calendar.readonly",
      access_type: "offline",
      ux_mode: "popup",
      callback: async (response) => {
        if (response.code) {
          // Send the code to your Flask backend
          await fetch("http://localhost:5000/exchange_code", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              code: response.code,
              uid: user.uid, // link tokens to Firebase user
            }),
          });
          alert("Calendar connected!");
        }
      },
    });
    client.requestCode();
  }
};


  return (
    <nav className="bg-gray-800 p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-white text-lg font-bold">Urmindr</Link>
        <div>
          {user ? (
            <div className="flex items-center">
              <span className="text-white mr-4">Welcome, {user.displayName}</span>
              <button onClick={handleSignOut} className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded">
                Sign Out
              </button>
            </div>
          ) : (
            <button onClick={handleSignIn} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Sign In
            </button>
          )}
        </div>
        <button onClick = {handleCalendarClick} className = "button"> Calendar</button>
      </div>
    </nav>
  );
}

export default Navbar;