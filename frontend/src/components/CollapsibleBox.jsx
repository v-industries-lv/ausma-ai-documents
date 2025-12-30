import { useState } from "react";
import styles from "./CollapsibleBox.module.css";

export default function CollapsibleBox({
  title,
  children,
  className,
  initiallyClosed = true,
}) {
  const [isClosed, setIsClosed] = useState(initiallyClosed);
  function onToggle() {
    setIsClosed((isClosed) => !isClosed);
  }
  return (
    <section className={styles["settings-list-section"]}>
      <div className={styles["settings-cnt"]} onClick={onToggle}>
        <h1 className={styles["settings-option"]}>{title}</h1>
        <div className={styles.arrow}>
          <svg
            className={isClosed ? "" : styles.rotated}
            style={{ cursor: "pointer" }}
            xmlns="http://www.w3.org/2000/svg"
            x="0px"
            y="0px"
            width="20"
            height="20"
            viewBox="0 0 30 30"
          >
            <path d="M 24.990234 8.9863281 A 1.0001 1.0001 0 0 0 24.292969 9.2929688 L 15 18.585938 L 5.7070312 9.2929688 A 1.0001 1.0001 0 0 0 4.9902344 8.9902344 A 1.0001 1.0001 0 0 0 4.2929688 10.707031 L 14.292969 20.707031 A 1.0001 1.0001 0 0 0 15.707031 20.707031 L 25.707031 10.707031 A 1.0001 1.0001 0 0 0 24.990234 8.9863281 z"></path>
          </svg>
        </div>
      </div>
      <div
        className={`${styles["setting-list"]} ${className ?? ""} ${
          isClosed ? "" : styles.open
        }`}
      >
        {children}
      </div>
    </section>
  );
}
