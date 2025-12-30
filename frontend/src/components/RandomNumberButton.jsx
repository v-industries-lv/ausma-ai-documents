import _styles from "./SmallButtons.module.css";
import _styles2 from "../pages/SettingsCommon.module.css";

const styles = { ..._styles, ..._styles2 };

export default function RandomNumberButton({ setNumber }) {
  const generateRandomNumber = () => {
    if (!setNumber) return;
    const random = Math.floor(Math.random() * 32768);
    setNumber(random);
  };
  return (
    <>
      <div className={styles["button-container"]}>
        <button
          onClick={generateRandomNumber}
          className={`${styles["button-style"]} ${styles["small-btn"]} ${styles["random-number-button"]}`}
          title="Generate Random Seed Number"
        >
          &#x1F5D8;
        </button>
      </div>
    </>
  );
}
