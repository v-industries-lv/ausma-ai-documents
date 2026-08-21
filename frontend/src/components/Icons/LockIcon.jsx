import * as React from "react";
const LockIcon = ({ title = "Locked", ...props }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={800}
    height={800}
    fill="none"
    viewBox="0 0 24 24"
    {...props}
  >
    <path
      stroke="#1C274C"
      strokeWidth={1.5}
      d="M2 16c0-2.828 0-4.243.879-5.121C3.757 10 5.172 10 8 10h8c2.828 0 4.243 0 5.121.879C22 11.757 22 13.172 22 16c0 2.828 0 4.243-.879 5.121C20.243 22 18.828 22 16 22H8c-2.828 0-4.243 0-5.121-.879C2 20.243 2 18.828 2 16Z"
      style={{
        stroke: "var(--color-svg-fill-primary)",
        strokeOpacity: 1,
      }}
    />
    <circle
      cx={12}
      cy={16}
      r={2}
      stroke="#1C274C"
      strokeWidth={1.5}
      style={{
        stroke: "var(--color-svg-fill-primary)",
        strokeOpacity: 1,
      }}
    />
    <path
      stroke="#1C274C"
      strokeLinecap="round"
      strokeWidth={1.5}
      d="M6 10V8a6 6 0 1 1 12 0v2"
      style={{
        stroke: "var(--color-svg-fill-primary)",
        strokeOpacity: 1,
      }}
    />
  </svg>
);
export default LockIcon;
