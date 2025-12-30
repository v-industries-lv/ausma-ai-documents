import { useEffect } from "react";
import _styles from "./Layout.module.css";
import _styles2 from "./Username.module.css";
import "./SideBarAnimation.css";
import { useState } from "react";
import { socket } from "../socket";
import { NavLink, useNavigate } from "react-router-dom";
import Username from "./UserName";
import FullScreenModal from "./FullScreenModal";

const styles = { ..._styles, ..._styles2 };

export default function Layout({ username, children }) {
  const [isClosed, setClosed] = useState(false);
  const navigate = useNavigate();
  const [currentRenameRoom, setCurrentRenameRoom] = useState(null);

  const inner =
    typeof children === "function" ? children({ setClosed }) : children;

  const [rooms, setRooms] = useState([]);
  function calculateNameFreq() {
    let nameFreq = {};
    for (let room of rooms) {
      let name = room.name;
      let old = nameFreq[name];
      nameFreq[name] = old ? old + 1 : 1;
    }
    return nameFreq;
  }
  const nameFreq = calculateNameFreq();

  function confirm(message) {
    return window.confirm(message);
  }

  async function createRoom() {
    // TODO move room name to state
    const name = document.getElementById("room-name").value.trim();
    if (name) {
      const res = await fetch("/api/create_room", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name }),
      });
      const room = await res.json();
      document.getElementById("room-name").value = "";
    }
  }

  function removeRoom(id, name) {
    const message = `Are you sure you want to delete - ${name}?`;
    if (confirm(message)) {
      socket.emit("remove_room", { room_id: id });
    }
  }

  useEffect(() => {
    async function fetchRooms() {
      const res = await fetch("/api/rooms");
      setRooms(await res.json());
    }
    fetchRooms();
  }, []);

  useEffect(() => {
    socket.on("rooms_list", setRooms);
  }, []);

  return (
    <>
      <aside
        className={`${styles.side_bar} side_bar ${
          isClosed ? `${styles.close} close` : ""
        }`}
      >
        <aside className={styles["content"]}>
          <div className={styles["navigation"]}>
            <NavLink to="/">
              <img
                src="/static/svg-icons/ausma3-gray.svg"
                className={`${styles["ausma_ai_logo"]} ${styles["hover_btn"]}`}
              />
            </NavLink>
            <div className={styles["option_buttons"]}>
              <NavLink to="/knowledge-base">
                <img
                  src="/static/svg-icons/notebook-minimalistic-svgrepo-com.svg"
                  alt="knowledge-base-button"
                  className={`${styles["home_icon"]} ${styles["hover_btn"]}`}
                  title="Knowledge Base Settings"
                />
              </NavLink>
              <NavLink to="/settings">
                <img
                  src="/static/svg-icons/settings-svgrepo-com.svg"
                  alt="settings-icon"
                  className={`${styles["home_icon"]} ${styles["gear"]} ${styles["hover_btn"]}`}
                  title="Settings"
                />
              </NavLink>
              <NavLink to="/about">
                <img
                  src="/static/svg-icons/question-square-svgrepo-com.svg"
                  alt="faq-button"
                  className={`${styles["home_icon"]} ${styles["gear"]} ${styles["hover_btn"]}`}
                  title="About ausma.ai"
                />
              </NavLink>
            </div>
          </div>
        </aside>

        <div className={styles["room_create"]}>
          <form
            className={styles["new-room-form"]}
            onSubmit={(e) => {
              e.preventDefault();
              createRoom();
            }}
          >
            <input
              className={styles["input-style"]}
              id="room-name"
              placeholder="Create your room name"
              required
            />
            <button
              className={`${styles["create-button"]} ${styles["hover_btn"]}`}
              type="submit"
              title="Create Room"
            >
              <img src="/static/svg-icons/createRoom.svg" />
            </button>
          </form>
        </div>
        <ul className={styles["rooms-list"]}>
          {rooms.toReversed().map((room) => {
            // only show the id prefix if the name is not unique
            const suffix =
              nameFreq[room.name] > 1 ? " @" + room.id.substring(0, 5) : "";
            const fullName = room.name + suffix;
            return (
              <li style={{ cursor: "pointer" }} key={room.id}>
                <div
                  className={styles["room-item"]}
                  title={`Room: ${fullName} [ ${room.created} ]`}
                  onClick={() => {
                    navigate(`/chat/${room.id}`);
                  }}
                >
                  {fullName}
                </div>
                <img
                  src="/static/svg-icons/pen-svgrepo-com.svg"
                  className={`${styles["rename_room_image"]} ${styles["hover_btn"]}`}
                  data-value="${room.id}"
                  data-name="${fullName}"
                  style={{
                    height: "30px",
                    cursor: "pointer",
                    width: "30px",
                    verticalAlign: "middle",
                  }}
                  title="Rename Room"
                  onClick={() => setCurrentRenameRoom(room)}
                />
                <img
                  src="/static/svg-icons/trash-bin-trash-svgrepo-com.svg"
                  className={`${styles["remove_room_image"]} ${styles["hover_btn"]}`}
                  data-value="${room.id}"
                  data-name="${fullName}"
                  style={{
                    height: "30px",
                    cursor: "pointer",
                    width: "30px",
                    verticalAlign: "middle",
                  }}
                  title="Remove Room"
                  onClick={() => removeRoom(room.id, fullName)}
                />
              </li>
            );
          })}
        </ul>
      </aside>
      <div
        className={`${styles.toggle_button} ${styles.home_icon} ${
          styles.hover_btn
        } ${styles.position_left} ${
          isClosed ? `${styles.button_rotation} ${styles["at-start"]}` : ""
        }`}
        onClick={() => setClosed((closed) => !closed)}
        title={isClosed ? "Open Sidebar" : "Close Sidebar"}
      >
        <img src="/static/svg-icons/send-square-svgrepo-com.svg" />
      </div>
      <Username />
      {inner}
      <RoomRenamer room={currentRenameRoom} setRoom={setCurrentRenameRoom} />
    </>
  );
}

function RoomRenamer({ room, setRoom }) {
  const [value, setValue] = useState(room?.name);
  useEffect(() => setValue(room?.name), [room]);
  function cancel() {
    setValue(room?.name);
    close();
  }
  function close() {
    setRoom(null);
  }
  function save() {
    renameRoom(room.id, value);
    close();
  }

  function edit(e) {
    setValue(e.target.value);
  }

  async function renameRoom(id, name) {
    if (name) {
      await fetch(`/api/room/${id}/rename/${encodeURIComponent(name)}`);
    }
  }

  return (
    <FullScreenModal isClosed={!room} onClickOff={() => setRoom(null)}>
      <div className={styles["username_popup"]}>
        <label htmlFor="currentRoom">New room name:</label>
        <input id="currentRoom" value={value} onChange={edit} />

        <div className={styles["button_group"]}>
          <button onClick={save}>Save</button>
          <button onClick={cancel}>Cancel</button>
        </div>
      </div>
    </FullScreenModal>
  );
}
