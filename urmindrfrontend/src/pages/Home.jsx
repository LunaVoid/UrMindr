function Home({ user }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Account Information</h1>
        <p className="text-lg">Welcome, {user.displayName}!</p>
        <p className="text-lg">Email: {user.email}</p>
      </div>
    </div>
  );
}

export default Home;
