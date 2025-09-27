import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

function Landing() {
  const auth = getAuth();
  const provider = new GoogleAuthProvider();

  const handleSignIn = async () => {
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error("Error signing in:", error);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Urmindr</h1>
        <p className="text-lg mb-8">
          Your personal AI assistant for managing your tasks.
        </p>
        <button
          onClick={handleSignIn}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Get Started Now!
        </button>
        <div className="flex flex-col md:flex-row items-center mt-10 mx-5 gap-5">
          <p className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg">
            Uses natural dialogue or text to take in a list of tasks and
            deadlines you need to get done
          </p>
          <p className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg">
            Divides your workload over any amount of time, saving you time to
            focus on what you need to get done
          </p>
          <p className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg">
            Seamlessly integrates with your Google calendar so you can keep
            track of your deadlines
          </p>
        </div>
      </div>
    </div>
  );
}

export default Landing;