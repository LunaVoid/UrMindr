import React, { useState, useEffect } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";

function MyCalendar({ token }) {
  const [events, setEvents] = useState([
    { title: "Initial Event", start: "2025-09-27" },
  ]);

  // Fetch events from Google Calendar when token changes
  useEffect(() => {
    if (!token) return;

    fetch(
      "https://www.googleapis.com/calendar/v3/calendars/primary/events?singleEvents=true",
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    )
      .then((res) => res.json())
      .then((data) => {
        // Map Google events to FullCalendar format
        const formattedEvents = data.items
          .filter((event) => event.summary && event.start && event.end)
          .map((event) => ({
            title: event.summary,
            start: event.start.dateTime || event.start.date,
            end: event.end.dateTime || event.end.date,
          }));
        setEvents(formattedEvents);
      })
      .catch((err) => console.error("Error fetching events:", err));
  }, [token]);

  const handleDateClick = (arg) => {
    const title = prompt("Enter event title:");
    if (title) {
      setEvents([...events, { title, start: arg.dateStr }]);
    }
  };

  return (
    <div>
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        events={events}
        dateClick={handleDateClick}
        editable={true}
        selectable={true}
      />
      <button
        onClick={() => console.log("Connect Calendar clicked")}
        className="bg-green-500 text-white px-4 py-2 rounded mt-4"
      >
        Connect Google Calendar
      </button>
    </div>
  );
}

export default MyCalendar;
