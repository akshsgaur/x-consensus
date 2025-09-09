import React from "react"

export default function Header() {
  return (
    <div className="flex items-center justify-between p-6">
      <div className="flex items-center gap-3">
        <div
          className="px-4 py-2 flex items-center gap-2"
          style={{
            backgroundColor: "#ffffff",
            color: "#000000",
            border: "2px solid #000000",
            boxShadow: "4px 4px 0px #666666",
            borderRadius: "8px",
          }}
        >
          <span className="text-xl">🤝</span>
          <span className="font-bold text-lg">X-Consensus Builder</span>
        </div>
      </div>
      <div
        className="px-3 py-1 text-sm font-medium"
        style={{
          backgroundColor: "#ffffff",
          color: "#000000",
          border: "2px solid #000000",
          boxShadow: "3px 3px 0px #666666",
          borderRadius: "16px",
        }}
      >
        hackathon
      </div>
    </div>
  )
}