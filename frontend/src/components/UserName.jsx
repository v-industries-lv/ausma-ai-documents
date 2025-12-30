import { createContext, useContext, useState } from "react";
import styles from "./Username.module.css";
import FullScreenModal from "./FullScreenModal";

export const UsernameContext = createContext({});

export default function Username() {
  const { username, setUsername } = useContext(UsernameContext);
  const [panelClosed, setPanelClosed] = useState(true);
  const [value, setValue] = useState(username);

  function cancel() {
    setValue(username);
    close();
  }
  function close() {
    setPanelClosed(true);
  }
  function save() {
    setUsername(value);
    close();
  }

  function edit(e) {
    setValue(e.target.value);
  }

  return (
    <>
      <div
        title={`Username: ${username}`}
        onClick={() => setPanelClosed(false)}
        className={styles.username_ctn}
      >
        <img src="/static/svg-icons/user-circle-svgrepo-com.svg"></img>
        <h1>{username}</h1>
      </div>
      <FullScreenModal
        className={styles.username_popup}
        isClosed={panelClosed}
        onClickOff={cancel}
      >
        <label htmlFor="username">Username:</label>
        <input id="username" value={value} onChange={edit} />

        <div className={styles.button_group}>
          <button onClick={save}>Save</button>
          <button onClick={cancel}>Cancel</button>
        </div>
      </FullScreenModal>
    </>
  );
}
