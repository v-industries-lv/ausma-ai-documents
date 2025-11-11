async function loadHTML() {
  const response = await fetch("/static/side_bar.html");
  const html = await response.text();
  const bodyTag = document.querySelector("body");
  //we will convert hmtl to dom nodes
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = html.trim();
  const oldFirst = bodyTag.firstChild;
  //add all the nodes one by one
  tempDiv.childNodes.forEach(function (child) {
    bodyTag.insertBefore(child, oldFirst);
  });
  afterLoading();
}

loadHTML();

function afterLoading() {
  const navBarToggleBTN = document.querySelector(".toggle_button");
  const sideBar = document.querySelector(".side_bar");

  const isClosed = sideBar.classList.contains("close");
  navBarToggleBTN.title = isClosed ? "Open sidebar" : "Close sidebar";
  navBarToggleBTN.setAttribute("aria-label", navBarToggleBTN.title);

  navBarToggleBTN.addEventListener("click", function () {
    sideBar.classList.toggle("close");
    navBarToggleBTN.classList.toggle("button_rotation");
    navBarToggleBTN.classList.toggle("at-start");

    const isClosedNow = sideBar.classList.contains("close");
    navBarToggleBTN.title = isClosedNow ? "Open sidebar" : "Close sidebar";
    navBarToggleBTN.setAttribute("aria-label", navBarToggleBTN.title);
  });

  const socket = io();

  document.getElementById("new-room-form").onsubmit = function (e) {
    e.preventDefault();
    const name = document.getElementById("room-name").value.trim();
    if (name) {
      fetch("/create_room", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name }),
      })
        .then((res) => res.json())
        .then((room) => {
          document.getElementById("room-name").value = "";
        });
    }
  };

  // Listen for live updates
  socket.on("rooms_list", function (rooms) {
    renderRooms(rooms);
  });

  function removeRoom(event) {
    var room = event.target.getAttribute("data-value");
    socket.emit("remove_room", { room_id: room });
  }

  function renderRooms(rooms) {
    let ul = document.getElementById("rooms-list");
    ul.innerHTML = "";
    // calculating the number of times each name is repeated
    let nameFreq = {};
    for (let room of rooms) {
      let name = room.name;
      let old = nameFreq[name];
      nameFreq[name] = old ? old + 1 : 1;
    }

    rooms.forEach((room) => {
      let li = document.createElement("li");
      li.style.cursor = "pointer";
      // only show the id prefix if the name is not unique
      let suffix =
        nameFreq[room.name] > 1 ? " @" + room.id.substring(0, 5) : "";
      let fullName = room.name + suffix;
      li.innerHTML = `<div class="room-item" title="room: ${fullName}">${fullName}</div>
                <img src='/static/svg-icons/trash-bin-trash-svgrepo-com.svg' class="remove_room_image" data-value="${room.id}" data-name="${fullName}" 
                style='height:30px;cursor:pointer;width:30px;vertical-align:middle;' title='Remove room'>`;
      const roomItem = li.querySelector(".room-item");
      roomItem.addEventListener("click", function () {
        window.location.href = `/chat/${room.id}`;
      });
      ul.appendChild(li);
    });

    document
      .querySelectorAll(".remove_room_image")
      .forEach(function (click_image) {
        click_image.addEventListener("click", function (evnt) {
          evnt.stopPropagation();
          evnt.preventDefault();
          let fullName = click_image.dataset.name;
          let message = `Are you sure you want to delete - ${fullName}?`;
          if (confirm(message)) {
            removeRoom(evnt);
          }
        });
      });
  }

  // Call this just after DOM loads (before any socket logic)
  function fetchRooms() {
    fetch("/rooms")
      .then((r) => r.json())
      .then(renderRooms);
  }

  // Socket.IO: will overwrite live as rooms_list arrives
  socket.on("rooms_list", renderRooms);
  fetchRooms();
}
