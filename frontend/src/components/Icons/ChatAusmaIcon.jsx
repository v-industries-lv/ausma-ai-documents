import * as React from "react";
const ChatAusmaIcon = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    xmlnsXlink="http://www.w3.org/1999/xlink"
    width="93mm"
    height="93mm"
    viewBox="0 0 93 93"
    {...props}
  >
    <defs>
      <linearGradient id="b">
        <stop
          offset={0.126}
          style={{
            stopColor: "var(--color-ausma-light-dark-blue)",
            stopOpacity: 1,
          }}
        />
        <stop
          offset={0.492}
          style={{
            stopColor: "var(--color-ausma-light-blue)",
            stopOpacity: 1,
          }}
        />
        <stop
          offset={0.644}
          style={{
            stopColor: "var(--color-ausma-light-yellow)",
            stopOpacity: 1,
          }}
        />
        <stop
          offset={0.733}
          style={{
            stopColor: "var(--color-ausma-light-orange)",
            stopOpacity: 1,
          }}
        />
        <stop
          offset={0.85}
          style={{
            stopColor: "#f03630",
            stopOpacity: 1,
          }}
        />
      </linearGradient>
      <linearGradient id="a">
        <stop
          offset={0.145}
          style={{
            stopColor: "var(--color-ausma-light-dark-blue)",
            stopOpacity: 1,
          }}
        />
        <stop
          offset={0.448}
          style={{
            stopColor: "var(--color-ausma-light-blue)",
            stopOpacity: 1,
          }}
        />
        <stop
          offset={0.567}
          style={{
            stopColor: "var(--color-ausma-light-yellow)",
            stopOpacity: 1,
          }}
        />
        <stop
          offset={0.632}
          style={{
            stopColor: "var(--color-ausma-light-orange)",
            stopOpacity: 1,
          }}
        />
        <stop
          offset={0.791}
          style={{
            stopColor: "var(--color-ausma-light-red)",
            stopOpacity: 1,
          }}
        />
      </linearGradient>
      <linearGradient
        xlinkHref="#a"
        id="c"
        x1={35}
        x2={35}
        y1={63.038}
        y2={-5.038}
        gradientTransform="translate(11.5 11.003)"
        gradientUnits="userSpaceOnUse"
      />
      <linearGradient
        xlinkHref="#b"
        id="d"
        x1={46.5}
        x2={46.5}
        y1={91.707}
        y2={1.293}
        gradientUnits="userSpaceOnUse"
      />
    </defs>
    <g
      style={{
        display: "inline",
      }}
    >
      <path
        d="M79.913 52.88c1.125-5.02 2.056-19.133-9.7-30.586-5.981-5.825-14.516-9.648-24.528-9.577-10.605.076-21.7 6.238-27.326 14.967-13.851 21.493 1.04 39.567 1.04 39.567s8.991-9.03 27.303-9.463c15.47-.366 26.321 9.503 26.321 9.503l-1.483-5.946 5.825-.633s-8.842-11.16-30.108-11.217c-17.46-.046-26.895 6.897-26.895 6.897s-5.203-11.6 2.356-24.234c4.523-7.56 13.8-13.088 22.83-13.317 7.61-.193 15.328 2.924 20.61 8.078 9.74 9.504 8.172 21.917 8.172 21.917z"
        style={{
          display: "inline",
          fill: "url(#c)",
          fillOpacity: 1,
          fillRule: "evenodd",
          stroke: "none",
          strokeWidth: 1.7,
          strokeOpacity: 1,
        }}
      />
      <circle
        cx={46.5}
        cy={46.5}
        r={42.207}
        style={{
          fill: "none",
          fillRule: "evenodd",
          stroke: "url(#d)",
          strokeWidth: 6,
          strokeDasharray: "none",
          strokeOpacity: 1,
        }}
      />
    </g>
  </svg>
);
export default ChatAusmaIcon;
