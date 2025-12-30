import "./Index.css";
import _styles from "./AboutAusma.module.css";
import _styles2 from "./Chat.module.css";
import { MarkdownHooks } from "react-markdown";
import rehypeStarryNight from "rehype-starry-night";
import "@wooorm/starry-night/style/both";
import onigurumaURL from "vscode-oniguruma/release/onig.wasm?url";
import ReadMe from "../../../README.md?raw";
import HowToCustomModels from "../../../docs/HOWTO_custom_models_hf_to_ollama.md?raw";
import HowToWorkWithKB from "../../../docs/HOWTO_knowledge_base.md?raw";
import { useState } from "react";

const styles = { ..._styles, ..._styles2 };

export default function About() {
  const [selectedOption, setSelectedOption] = useState("option1");

  const options = [
    { id: "option1", label: "About ausma.ai" },
    { id: "option2", label: "Custom Models" },
    { id: "option3", label: "About Knowledge Base" },
  ];

  const handleClick = (e, id) => {
    e.preventDefault();
    setSelectedOption(id);
  };

  return (
    <>
      <div className={styles["main"]}>
        <nav>
          {options.map((opt) => (
            <a
              className={`${styles.nav_opt} ${
                selectedOption === opt.id ? styles.active : ""
              }`}
              href={`#${opt.id}`}
              key={opt.id}
              c
              onClick={(e) => handleClick(e, opt.id)}
            >
              {opt.label}
            </a>
          ))}
        </nav>

        <div className={`${styles["main-content"]} ${styles["message"]}`}>
          {selectedOption === "option1" && (
            <MarkdownHooks
              rehypePlugins={[
                [
                  rehypeStarryNight,
                  { getOnigurumaUrlFetch: () => onigurumaURL },
                ],
              ]}
            >
              {ReadMe}
            </MarkdownHooks>
          )}
          {selectedOption === "option2" && (
            <MarkdownHooks
              rehypePlugins={[
                [
                  rehypeStarryNight,
                  { getOnigurumaUrlFetch: () => onigurumaURL },
                ],
              ]}
            >
              {HowToCustomModels}
            </MarkdownHooks>
          )}

          {selectedOption === "option3" && (
            <MarkdownHooks
              rehypePlugins={[
                [
                  rehypeStarryNight,
                  { getOnigurumaUrlFetch: () => onigurumaURL },
                ],
              ]}
            >
              {HowToWorkWithKB}
            </MarkdownHooks>
          )}
        </div>
      </div>
    </>
  );
}
