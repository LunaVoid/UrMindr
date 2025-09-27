import React from "react";
import { useState, useEffect } from "react";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import microphoneIcon from "../assets/microphone icon.png";

function Chat() {
  const [started, setStarted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [user, setUser] = useState(null);
  const [currentChatId, setCurrentChatId] = useState(null);
  const googleAccessToken = sessionStorage.getItem("accessToken");
  if(!googleAccessToken){
    console.error("No access token redirect to signup?")
  }


  useEffect(() => {
    const auth = getAuth();
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe();
  }, []);

  const sendMessageToApi = async (message, chatId = null) => {
    if (!user) {
      console.error("No user logged in.");
      setMessages((prevMessages) => [
        ...prevMessages,
        { text: "You must be logged in to use the chat.", sender: "bot" },
      ]);
      return;
    }

    const idToken = await user.getIdToken();
    const url = "http://127.0.0.1:5000/api/toolcall";

    const requestBody = { prompt: message };
    if (chatId) {
      requestBody.chat_id = chatId;
    }

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({...requestBody,
          accessToken: googleAccessToken
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        const errorMessage =
          result.error || `Error: ${response.status} ${response.statusText}`;
        setMessages((prevMessages) => [
          ...prevMessages,
          { text: `Error: ${errorMessage}`, sender: "bot" },
        ]);
        return;
      }

      if (result.chat_id && result.chat_id !== currentChatId) {
        setCurrentChatId(result.chat_id);
      }

      if (result.authorization_url) {
        const authLink = (
          <a
            href={result.authorization_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 underline"
          >
            Click here to authorize Google Calendar
          </a>
        );
        setMessages((prevMessages) => [
          ...prevMessages,
          { text: result.response, sender: "bot" },
          { text: authLink, sender: "bot" },
        ]);
      } else {
        setMessages((prevMessages) => [
          ...prevMessages,
          { text: result.response, sender: "bot" },
        ]);
      }
    } catch (error) {
      console.error(error.message);
      setMessages((prevMessages) => [
        ...prevMessages,
        { text: `Network Error: ${error.message}`, sender: "bot" },
      ]);
    }
  };

  const handleSendMessage = () => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: "user" }]);
      sendMessageToApi(input, currentChatId);
      setInput("");
    }
  };

  const recognition = new webkitSpeechRecognition();

  recognition.onstart = function () {
    console.log("Speech recognition service has started");
  };

  recognition.onend = async function () {
    console.log("Speech recognition service disconnected");
  };

  recognition.onresult = async function (event) {
    const transcript = event.results[0][0].transcript;
    console.log("Result received: " + transcript);
    setMessages((prevMessages) => [
      ...prevMessages,
      { text: transcript, sender: "user" },
    ]);
    sendMessageToApi(transcript, currentChatId);
  };

  function toggleStart() {
    console.log("running");
    if (!started) {
      recognition.start();
      setStarted(true);
    } else {
      recognition.stop();
      setStarted(false);
    }
  }

  const handleNewChat = () => {
    setCurrentChatId(null);
    setMessages([]);
  };

  // Check browser support
  if (!("webkitSpeechRecognition" in window)) {
    alert(
      "Sorry, your browser doesn't support speech recognition. Try Chrome on desktop/Android."
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat UI - this will be the main content area */}
      <div className="flex flex-col h-full border rounded-lg p-4">
        {" "}
        {/* Main chat container */}
        <div className="flex-grow overflow-y-auto">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`mb-2 flex ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {" "}
              <span
                className={`block p-2 rounded-lg w-fit max-w-[50%] ${
                  msg.sender === "user" ? "bg-blue-200" : "bg-gray-200"
                }`}
              >
                {" "}
                {msg.text}
              </span>
            </div>
          ))}
        </div>
        <div className="flex flex-col sm:flex-row mt-4">
          <input
            type="text"
            className="flex-grow border rounded-lg p-2 focus:outline-none mb-2 sm:mb-0"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                handleSendMessage();
              }
            }}
          />
          <div className="flex flex-row sm:ml-2 mb-2 sm:mb-0">
            <button
              className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-3 rounded-lg flex-1"
              onClick={handleSendMessage}
            >
              Send
            </button>
            <button
              onClick={toggleStart}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-3 rounded-lg ml-2 flex-1"
              aria-label="Toggle Speech Recognition"
            >
              <img
                src={microphoneIcon}
                alt="Microphone Icon"
                className="w-5 h-5 inline-block"
              />
            </button>
          </div>
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-3 rounded-lg sm:ml-2 w-full sm:w-auto mt-2 sm:mt-0"
            onClick={handleNewChat}
          >
            New Chat
          </button>
        </div>
      </div>
    </div>
  );
}

export default Chat;
