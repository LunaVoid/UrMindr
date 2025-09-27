import { Link, useNavigate } from "react-router-dom";
import {
  getAuth,
  signOut,
  GoogleAuthProvider,
  signInWithPopup,
} from "firebase/auth";

function Navbar({ setAccessToken, user }) {
  const auth = getAuth();
  const provider = new GoogleAuthProvider();
  provider.addScope("https://www.googleapis.com/auth/calendar");

  const navigate = useNavigate();

  const handleSignIn = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      const credential = GoogleAuthProvider.credentialFromResult(result);
      const token = credential.accessToken;
      setAccessToken(token);
      sessionStorage.setItem("accessToken", token);
    } catch (error) {
      console.error("Error signing in:", error);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut(auth);
      // Clear the access token from session storage on sign out
      sessionStorage.removeItem("accessToken");
      setAccessToken(null);
      const navigate = useNavigate();

      navigate('/');
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  const handleCalendarClick = () => {
    navigate("/calendar");
  };

  return (
    <nav className="bg-gray-800 p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-white text-lg font-bold">
          Urmindr
        </Link>
        <div>
          {user ? (
            <div className="flex items-center">
              <span className="text-white mr-4">{user.displayName}</span>
              <button
                onClick={handleSignOut}
                className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              onClick={handleSignIn}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
              Sign In
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;