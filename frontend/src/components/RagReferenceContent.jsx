import _styles from "./RagReferenceContent.module.css";
import _styles2 from "./Username.module.css";
import FullScreenModal from "./FullScreenModal";
import { renderNewLines } from "../utils/jsxUtils";
import ShowItemInFolderButton from "./ShowItemInFolderButton";
import { DocumentIcon } from "./Icons/ComponentIcons";
const styles = { ..._styles, ..._styles2 };

export default function RagReferenceContent({ msg, setReference }) {
  const ragReference = JSON.parse(msg?.rag_sources ?? "[]") ?? [];

  const hasReference = ragReference.length > 0;

  return (
    <>
      <div>
        {hasReference ? (
          <div
            className={`${styles["list-content"]} ${styles["content-style"]}`}
          >
            {ragReference
              .toSorted((a, b) => a.similarity_score - b.similarity_score)
              .map((ref, i) => (
                <>
                  {" "}
                  <div className={styles["reference-content"]}>
                    <div className={styles["reference-left"]}>
                      <span>
                        <DocumentIcon
                          className={`${styles["icon"]} ${styles["document-icon"]} `}
                        />
                      </span>

                      <a
                        className={styles["reference-link"]}
                        title="More"
                        key={i}
                        href="#"
                        onClick={(e) => {
                          e.preventDefault();
                          setReference(ref);
                        }}
                      >
                        <b>{ref.metadata.filename}&nbsp;</b>
                        <br />
                        <b>
                          Page {ref.metadata.page_number}/
                          {ref.metadata.page_count}
                        </b>{" "}
                        - "{ref.content}";
                      </a>
                    </div>
                    <div>
                      <ShowItemInFolderButton
                        filePath={ref.metadata.document_path}
                      />
                    </div>
                  </div>
                </>
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
  metadata.chunk = `${chunk_number}/${chunk_count}`;
  metadata.document = `${document_number}/${document_count}`;

  const metadataEntries = Object.entries(metadata).toSorted((a, b) =>
    a[0].localeCompare(b[0]),
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
            <h2>Source</h2>
            <div className={styles["ref-doc-group"]}>
              <div className={styles["ref-doc-wrapper"]}>
                <span>
                  <DocumentIcon
                    className={`${styles["icon-xl"]} ${styles["document-icon"]}`}
                  />
                </span>
                <h3 className={styles["reference-link"]}>
                  <b>{metadata.filename}</b>
                </h3>
              </div>
              <div>
                <ShowItemInFolderButton filePath={metadata.document_path} />
              </div>
            </div>
            <h3>Page {(metadata.page = `${page_number}/${page_count}`)}</h3>

            <span className={styles["horizontal-line"]} />

            <div className={styles["reference-section"]}>
              <h3>Retrieved Content</h3>

              <div className={styles["retrieved-content"]}>
                <p>{renderNewLines(reference.content)}</p>
              </div>
            </div>

            <span className={styles["horizontal-line"]} />

            <h3>Source Information</h3>

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
