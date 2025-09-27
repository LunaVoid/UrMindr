import { useEffect, useState } from "react";

function Home({ user, accessToken }) {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");

  useEffect(() => {
    const fetchEvents = async () => {
      if (!accessToken) {
        return; // Do not fetch if accessToken is not available
      }

      try {
        const timeMin = new Date().toISOString();
        const response = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=15&orderBy=startTime&singleEvents=true&timeMin=${timeMin}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          console.error("Error fetching events:", errorData);
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setEvents(data.items);
      } catch (error) {
        setError("Failed to fetch calendar events.");
      }
    };

    fetchEvents();
  }, [accessToken]);

  const handleAddEvent = async (e) => {
    e.preventDefault();
    if (!accessToken) {
      setError("Not authenticated to add event.");
      return;
    }

    const event = {
      summary: summary,
      start: {
        dateTime: new Date(startTime).toISOString(),
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
      end: {
        dateTime: new Date(endTime).toISOString(),
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
    };

    try {
      const response = await fetch(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(event),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error creating event:", errorData);
        throw new Error("Failed to create event");
      }

      // Refresh events list after adding a new one
      // A simple way is to re-fetch, but for better UX you might just add the new event to the state
      alert("Event created successfully!");
      setSummary("");
      setStartTime("");
      setEndTime("");
      // Re-fetch events to show the new one
      // Note: This is a simple approach. For a more optimized UX, you could add the new event directly to the events state.
      const timeMin = new Date().toISOString();
      const eventsResponse = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=15&orderBy=startTime&singleEvents=true&timeMin=${timeMin}`,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
      print (accessToken)
      const data = await eventsResponse.json();
      setEvents(data.items);

    } catch (error) {
      setError(error.message);
    }
  };

  const displayEvents = (events) => {
    if (error) {
      return <p className="text-red-500">{error}</p>;
    }
    if (!events || events.length === 0) {
      return <p>No upcoming events found.</p>;
    } else {
      return (
        <ul className="text-left">
          {events.map((event, index) => {
            const start = event.start.dateTime || event.start.date;
            return (
              <li key={index}>
                {new Date(start).toLocaleString()} - {event.summary}
              </li>
            );
          })}
        </ul>
      );
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="text-center w-full max-w-2xl">
        <h1 className="text-4xl font-bold mb-4">Account Information</h1>
        <p className="text-lg">Welcome, {user.displayName}!</p>
        <p className="text-lg mb-8">Email: {user.email}</p>

        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-2xl font-bold mb-4">Create New Event</h2>
          <form onSubmit={handleAddEvent} className="flex flex-col gap-4">
            <input
              type="text"
              placeholder="Event Title"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="p-2 border rounded"
              required
            />
            <div className="flex gap-4">
              <input
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="p-2 border rounded w-full"
                required
              />
              <input
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="p-2 border rounded w-full"
                required
              />
            </div>
            <button type="submit" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Add Event
            </button>
          </form>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4">Upcoming Events</h2>
          {displayEvents(events)}
        </div>
      </div>
    </div>
  );
}

export default Home;
