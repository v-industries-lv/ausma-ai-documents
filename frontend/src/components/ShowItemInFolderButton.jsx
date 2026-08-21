import styles from "./ChatToolbar.module.css";
import { ShowInExplorer } from "./Icons/ComponentIcons";

function ShowItemInFolderButton({ filePath }) {
  if (!window.electron?.showItemInFolder) {
    return null;
  }

  const handleClick = async () => {
    await window.electron.showItemInFolder(filePath);
  };

  return (
    <div className={styles["toolbar-btns"]}>
      <a className={styles["tool"]}>
        <ShowInExplorer onClick={handleClick} />
      </a>
    </div>
  );
}

export default ShowItemInFolderButton;
