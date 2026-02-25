/* -------- Websockets -------- */

let socket = null


function connectToServer() {
    // Use wss: protocol if site using https:, otherwise use ws: protocol
    let wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"

    // Create a new WebSocket.
    let url = `${wsProtocol}//${window.location.host}/dashboard/data`
    // websocket handshake process done here
    socket = new WebSocket(url)

    // Handle any errors that occur.
    socket.onerror = function(error) {
        displayMessage("WebSocket Error: " + error)
    }

    // Show a connected message when the WebSocket is opened.
    socket.onopen = function(event) {
        displayMessage("WebSocket Connected")
    }

    // Show a disconnected message when the WebSocket is closed.
    socket.onclose = function(event) {
        displayMessage("WebSocket Disconnected")
    }

    // Handle messages received from the server.
    socket.onmessage = function(event) {
        let response = JSON.parse(event.data)
        if (("commentor" in response[0]) && Array.isArray(response)) {
            updateComments(response)
        } else if (("replier" in response[0]) && Array.isArray(response)){
            updateReplies(response)
        }
        else {
            displayResponse(response)
        }
    }

}

function displayError(message) {
    let errorElement = document.getElementById("error")
    errorElement.innerHTML = message
}

function displayMessage(message) {
    let errorElement = document.getElementById("message")
    errorElement.innerHTML = message
}

function displayResponse(response) {
    if ("error" in response) {
        displayError(response.error)
    } else if ("message" in response) {
        displayMessage(response.message)
    } else {
        displayMessage("Unknown response")
    }
}

function addComment() {
    const stationSection = document.getElementById("stationDetailRoot");
    const stationIdStr = stationSection.dataset.stationId;
    const stationId = parseInt(stationIdStr);

    let textInputEl = document.getElementById("commentInput")
    let commentText = textInputEl.value
    if (commentText === "") return

    // Clear previous error message, if any
    displayError("")
    
    let data = {action: "add_comment", text: commentText, id: stationId}
    socket.send(JSON.stringify(data))

    textInputEl.value = ""
}

function addReply(buttonId) {
    let commentId = buttonId.split('_').pop()
    let replyInputId = `id_reply_input_text_${commentId}`
    let replyTextElement = document.getElementById(replyInputId)
    let replyText  = replyTextElement.value

    if (replyText === "") return

    // Clear previous error message, if any
    displayError("")
    
    let data = {action: "add_reply", text: replyText, id: commentId}
    socket.send(JSON.stringify(data))

    replyTextElement.value = ""
}

function deleteItem(id) {
    let data = {action: "delete", id: id}
    socket.send(JSON.stringify(data))
}

function makeListItemElement(comment) {
    let deleteButton

    // const stationSection = document.getElementById("stationDetailRoot");
    // const stationIdStr = stationSection.dataset.stationId;
    // const stationId = parseInt(stationIdStr); 

    // if (comment.commented_to_id === stationId) {
    //     deleteButton = `<button onclick='deleteItem(${comment.id})'>X</button>`
    // } else {
    //     deleteButton = "<button style='visibility: hidden'>X</button> "
    // }

    let details = `<span class="details">(id=${comment.id}, user=${comment.commentor})</span>`

    let element = document.createElement("li")
    element.id = `id_comment_${comment.id}`
    element.innerHTML = ` ${sanitize(comment.content)} ${details}
    <br>
    <div class="reply-container">
        <ul id="replies_${comment.id}" class="replies"></ul>

        <div>
            <label for="id_reply_input_text_${comment.id}">Reply:</label>
            <input id="id_reply_input_text_${comment.id}" type="text" name="target"></input>
            <button id="id_reply_button_${comment.id}" onclick="addReply(this.id)">Submit</button>
        </div>
    </div>
    `


    return element
}

function makeListReplyElement(reply) {
    let deleteButton
    if (reply.user === myUserName) {
        deleteButton = `<button onclick='deleteItem(${reply.id})'>X</button>`
    } else {
        deleteButton = "<button style='visibility: hidden'>X</button> "
    }

    let details = `<span class="details">(id=${reply.id}, user=${reply.replier})</span>`

    let element = document.createElement("li")
    element.id = `id_reply_${reply.id}`
    element.innerHTML = `${deleteButton} ${sanitize(reply.content)} ${details}`


    return element
}

function sanitize(s) {
    // Be sure to replace ampersand first
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
}

function updateComments(comments) {
    // Removes items from todolist if they not in items
    // let liElements = document.getElementsByTagName("li")
    // for (let i = 0; i < liElements.length; i++) {
    //     let element = liElements[i]
    //     let deleteIt = true
    //     comments.forEach(comment => {
    //         if (element.id === `id_item_${comment.id}`) deleteIt = false
    //     })
    //     if (deleteIt) element.remove()
    // }

    const stationSection = document.getElementById("stationDetailRoot");
    const stationIdStr = stationSection.dataset.stationId;
    const stationId = parseInt(stationIdStr); 

    let list = document.getElementById(`commentList${stationId}`)
    // Adds each to do list item received from the server to the displayed list
    comments.forEach(comment => {
        if (comment.commented_to_id === stationId){
            if (document.getElementById(`id_comment_${comment.id}`) == null) {
            list.append(makeListItemElement(comment))
        }
        }
    })
}

function updateReplies(replies) {

    // Adds each to do list item received from the server to the displayed list
    replies.forEach(reply => {
        if (document.getElementById(`replies_${reply.replied_to_id}`) != null){
            let list = document.getElementById(`replies_${reply.replied_to_id}`)
            if (document.getElementById(`id_reply_${reply.id}`) == null) {
                list.append(makeListReplyElement(reply))
            }
        }
    })
}

/* -------- Station detail page: chart only -------- */
document.addEventListener("DOMContentLoaded", () => {
    const root       = document.getElementById("stationDetailRoot");
    const stationId  = root.dataset.stationId;
    const messageEl  = document.getElementById("message");
    const errorEl    = document.getElementById("error");

    fetch(`/api/stations/${stationId}/trend/`)
        .then(r => {
            if (!r.ok) throw new Error(r.statusText);
            return r.json();
        })
        .then(data => {
            // Accept {granularity, series} OR plain [ {...} ]
            const granularity = data.granularity || "day";
            const series      = Array.isArray(data) ? data : data.series;

            if (!series || series.length === 0) {
            messageEl.textContent = "No trend data available.";
            return;
            }
            drawTrend(granularity, series);
        })
        .catch(() => { errorEl.textContent = "Could not load trend data."; 
    });
});

function drawTrend(granularity, series) {
  const ctx    = document.getElementById("trendChart").getContext("2d");
  const labels = series.map(d => {
    const dt = new Date(d.ts);
    return granularity === "hour"
      ? dt.toLocaleTimeString([], { hour: "2-digit" })
      : dt.toLocaleDateString();
  });
  const values = series.map(d => d.free);

  new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: values,
        borderWidth: 2,
        tension: 0.25,
        fill: false
      }]
    },
    options: {
      scales: {
        x: { title: { display: true, text: granularity === "hour" ? "Hour" : "Date" } },
        y: { beginAtZero: true, title: { display: true, text: "Bikes available" } }
      },
      plugins: { legend: { display: false } }
    }
  });
}
