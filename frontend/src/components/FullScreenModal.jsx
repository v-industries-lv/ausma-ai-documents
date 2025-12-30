import { useRef } from "react";
import styles from "./FullScreenModal.module.css";

export default function FullScreenModal({
  isClosed,
  onClickOff,
  children,
  className,
}) {
  const backgroundComponent = useRef(null);
  function onClick(e) {
    if (e.target === backgroundComponent.current) {
      onClickOff?.(e);
    }
  }
  return (
    isClosed || (
      <>
        <div
          className={styles.modal}
          onClick={onClick}
          ref={backgroundComponent}
        >
          <div className={className}>{children}</div>
        </div>
      </>
    )
  );
}
