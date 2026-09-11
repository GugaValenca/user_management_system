import React from "react";

interface LogoProps {
  size?: number;
  className?: string;
}

/**
 * Custom shield monogram - the app's actual brand mark, used in the navbar,
 * the auth screens, and (rendered to PNG/ICO separately) the favicon.
 */
const Logo: React.FC<LogoProps> = ({ size = 40, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 100 100"
    className={className}
    role="img"
    aria-label="User Management System logo"
  >
    <defs>
      <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#a78bfa" />
        <stop offset="100%" stopColor="#f472b6" />
      </linearGradient>
    </defs>
    <path
      d="M50 4 L88 18 V46 C88 72 71 90 50 97 C29 90 12 72 12 46 V18 Z"
      fill="url(#logo-gradient)"
    />
    <path
      d="M50 8 L84 21 V46 C84 70 68 87 50 93 C32 87 16 70 16 46 V21 Z"
      fill="none"
      stroke="rgba(255,255,255,0.35)"
      strokeWidth="1.5"
    />
    <text
      x="50"
      y="63"
      textAnchor="middle"
      fontFamily="'Segoe UI', system-ui, sans-serif"
      fontWeight="700"
      fontSize="36"
      letterSpacing="-1"
      fill="#ffffff"
    >
      UM
    </text>
  </svg>
);

export default Logo;
