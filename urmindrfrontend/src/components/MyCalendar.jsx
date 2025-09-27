import React, { useState, useEffect } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";

function MyCalendar({ token }) {
  const [events, setEvents] = useState([]);

  // Fetch events from Google Calendar when token changes
  useEffect(() => {
    if (!token) return;

    const fetchEvents = async () => {
      try {
        const timeMin = new Date().toISOString(); // only future events
        const res = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events?singleEvents=true&orderBy=startTime&timeMin=${timeMin}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        const data = await res.json();

        if (data.error) {
          console.error("Google Calendar API error:", data.error);
          return;
        }

        const calendarEvents = (data.items || []).map((event) => ({
          id: event.id,
          title: event.summary || "(No Title)",
          start: event.start.dateTime || event.start.date,
          end: event.end?.dateTime || event.end?.date,
        }));
        setEvents(calendarEvents);
      } catch (err) {
        console.error("Failed to fetch events:", err);
      }
    };

    fetchEvents();
  }, [token]);

  return (
    <div>
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        events={events}
        editable={true}
        selectable={true}
      />
    </div>
  );
}

export default MyCalendar;
