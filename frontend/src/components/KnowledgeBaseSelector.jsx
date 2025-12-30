import { useEffect, useState } from "react";
import styles from "./Selector.module.css";

export default function KnowledgeBaseSelector({
  kb,
  setKb,
  className,
  maxWidth = 100,
}) {
  const [kbs, setKbs] = useState([]);

  useEffect(() => {
    async function fetchKBs() {
      const req = await fetch("/api/kb/");
      const json = [{ name: "None" }, ...(await req.json())];
      setKbs(json ?? []);
    }
    fetchKBs();
  }, []);

  function shortenName(name) {
    if (name.length <= maxWidth) {
      return name;
    }
    return name.substring(0, maxWidth) + "...";
  }

  return (
    <div className={`${styles["select-ctn"]} ${className}`} title={kb}>
      <label for="kb">Knowledge base:</label>
      <select
        name="kb_name"
        value={kb}
        onChange={(e) => setKb(e.target.value)}
        title={kb.name}
      >
        {kbs.map((kb) => (
          <option value={kb.name} key={kb.name}>
            {shortenName(kb.name)}
          </option>
        ))}
      </select>
    </div>
  );
}
