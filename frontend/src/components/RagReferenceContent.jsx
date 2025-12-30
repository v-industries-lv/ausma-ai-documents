import _styles from "./RagReferenceContent.module.css";
import _styles2 from "./Username.module.css";
import FullScreenModal from "./FullScreenModal";
import { renderNewLines } from "../utils/jsxUtils";

const styles = { ..._styles, ..._styles2 };

export default function RagReferenceContent({ msg, setReference }) {
  const ragReference = JSON.parse(msg?.rag_sources ?? "[]") ?? [];
  console.log(ragReference);

  const hasReference = ragReference.length > 0;

  return (
    <>
      <div className={`${styles["list-content"]} ${styles["content-style"]}`}>
        {hasReference ? (
          <div>
            {ragReference
              .toSorted((a, b) => a.similarity_score - b.similarity_score)
              .map((ref, i) => (
                <a
                  title="More"
                  key={i}
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setReference(ref);
                  }}
                >
                  {ref.metadata.document_path},&nbsp;{ref.metadata.page_number}/
                  {ref.metadata.page_count}, &nbsp;{ref.metadata.chunk_number}/
                  {ref.metadata.chunk_count}, &nbsp;{ref.content};<br />
                </a>
              ))}
          </div>
        ) : (
          <p className={styles["no-ref-msg"]}>No Reference available!</p>
        )}
      </div>
    </>
  );
}

export function RagReferenceModal({ reference, close }) {
  if (!reference) return null;

  const {
    document_number,
    document_count,
    chunk_number,
    chunk_count,
    page_number,
    page_count,
    ...metadata
  } = reference.metadata;
  metadata.page = `${page_number}/${page_count}`;
  metadata.chunk = `${chunk_number}/${chunk_count}`;
  metadata.document = `${document_number}/${document_count}`;

  const metadataEntries = Object.entries(metadata).toSorted((a, b) =>
    a[0].localeCompare(b[0])
  );
  const entries = [
    ["id", reference.id],
    ...metadataEntries,
    ["similarity_score", reference.similarity_score],
  ];

  return (
    <>
      <FullScreenModal isClosed={!reference} onClickOff={close}>
        <div className={styles["content-style"]}>
          <div className={styles["reference-wrapper"]} title="Full Reference">
            <p>{renderNewLines(reference.content)}</p>
            {entries.map((pair) => (
              <p>
                {pair[0]} : {pair[1]}
              </p>
            ))}
          </div>
        </div>
        <div
          className={`${styles["username_popup"]} ${styles["position-center"]}`}
        >
          <button
            title="Return to Chat"
            onClick={close}
            className={styles["buttons_group"]}
          >
            Close
          </button>
        </div>
      </FullScreenModal>
    </>
  );
}
