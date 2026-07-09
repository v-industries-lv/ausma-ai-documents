import * as React from "react";
const UploadImageIcon = ({ title = "Upload Images", ...props }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={800}
    height={800}
    fill="none"
    viewBox="0 0 24 24"
    {...props}
  >
    <title>{title}</title>
    <path
      stroke="#1C274C"
      strokeLinecap="round"
      strokeWidth={1.5}
      d="M22 12c0 4.714 0 7.071-1.465 8.535C19.072 22 16.714 22 12 22s-7.071 0-8.536-1.465C2 19.072 2 16.714 2 12s0-7.071 1.464-8.536C4.93 2 7.286 2 12 2"
      style={{
        stroke: "var(--color-svg-fill-primary)",
        strokeOpacity: 1,
      }}
    />
    <path
      stroke="#1C274C"
      strokeLinecap="round"
      strokeWidth={1.5}
      d="m2 12.5 1.752-1.533a2.3 2.3 0 0 1 3.14.105l4.29 4.29a2 2 0 0 0 2.564.222l.299-.21a3 3 0 0 1 3.731.225L21 18.5M15 5.5h3.5m0 0H22m-3.5 0V9m0-3.5V2"
      style={{
        stroke: "var(--color-svg-fill-primary)",
        strokeOpacity: 1,
      }}
    />
  </svg>
);
export default UploadImageIcon;
