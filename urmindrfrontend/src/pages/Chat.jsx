import React from 'react'
import { useState, useEffect } from "react";



function Chat() {

    const [started, setStarted] = useState(false);
    const [result, setResult] = useState(false);

    const recognition = new webkitSpeechRecognition();

    recognition.onstart = function() {
        console.log('Speech recognition service has started');
    };

    recognition.onend = async function() {
        console.log('Speech recognition service disconnected');
    };

    recognition.onresult = async function(event) {
        const transcript = event.results[0][0].transcript;
        console.log('Result received: ' + transcript);
        let ptag = document.getElementsByClassName('here');
        ptag.innerHtml=transcript;
        console.log(transcript)
        const url = "http://127.0.0.1:5000/api/generate"

        try {
            const response = await fetch(url,{
                method:"POST",
                headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: transcript })
                
            })
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const result = await response.json();
        console.log(result);
        setResult(result.response)

    } catch (error) {
        console.error(error.message);
    }
    };

    function toggleStart () {
        console.log("running")
        if(!started){
            recognition.start();
            setStarted(true); 
        }
        else{
            recognition.stop();
            setStarted(false);
        }

    }

    // Check browser support
    if (!('webkitSpeechRecognition' in window)) {
        alert('Sorry, your browser doesn\'t support speech recognition. Try Chrome on desktop/Android.');
    }

  return (
    <div>
        <button onClick={toggleStart}>Click for speech recognition</button>
        <p>{result}</p>
    </div>
  )
}

export default Chat