import * as React from "react";
const CreateRoomIcon = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={30}
    height={30}
    fill="none"
    viewBox="0 0 24 24"
    {...props}
  >
    <path
      fill="#1C274C"
      d="M12.75 9a.75.75 0 0 0-1.5 0v2.25H9a.75.75 0 0 0 0 1.5h2.25V15a.75.75 0 0 0 1.5 0v-2.25H15a.75.75 0 0 0 0-1.5h-2.25V9Z"
      style={{
        fill: "var(--color-svg-fill-primary)",
        fillOpacity: 1,
      }}
    />
    <path
      fill="#1C274C"
      fillRule="evenodd"
      d="M12 1.25C6.063 1.25 1.25 6.063 1.25 12S6.063 22.75 12 22.75 22.75 17.937 22.75 12 17.937 1.25 12 1.25ZM2.75 12a9.25 9.25 0 1 1 18.5 0 9.25 9.25 0 0 1-18.5 0Z"
      clipRule="evenodd"
      style={{
        fill: "var(--color-svg-fill-primary)",
        fillOpacity: 1,
      }}
    />
  </svg>
);
export default CreateRoomIcon;
